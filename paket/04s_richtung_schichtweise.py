"""Richtungssuche wie 04_richtung.py, aber SCHICHTWEISE: es liegt immer nur eine Decoder-Schicht im RAM.

Für Modelle, die nicht in den Arbeitsspeicher passen (Qwen3.6-35B-A3B bf16 = 72 GB, MiniPC 64 GB).
  python 04s_richtung_schichtweise.py --modell MODELLE/Qwen3.6-35B-A3B --ergebnisse diagnose/ergebnisse.jsonl \
      --edit-schichten 15,19 --aus ergebnisse/richtung_moe.npz

Ablauf: Modell-Gerüst ohne Gewichte (meta) -> Embeddings aller Transkripte -> für jede Schicht L:
Gewichte von L aus den safetensors laden, ALLE Transkripte durch L schicken, Statistik sammeln,
Gewichte von L wieder freigeben. Speicher ~ 1 Schicht (35B-MoE: ~1,7 GB) + Zustände aller Transkripte
(Tokens x d_model x 2 Byte, z. B. 48 x 8,4k x 2048 x 2 = 1,7 GB). Jede Schicht wird nur EINMAL gelesen.

Rechnung identisch zu 04_richtung.py (gleiche Labels, gleiche Zufallsauswahl, gleiche Formeln); bei
dichten Modellen sollten u, d' und Spalten mit dem Original übereinstimmen (test_04s_gegen_original.py).

MoE-Schichten (mlp.experts + mlp.shared_expert, Qwen3.5/3.6-MoE):
  Experten-Neuron (e, j) schreibt g_e(t) * a_ej(t) * W_e[:, j] in den Residual Stream (g_e = Router-Gewicht,
  0 wenn e nicht gewählt). Score = (E_rep[g*a] - E_prod[g*a]) * (u . W_e[:, j]); Top-k über alle E x d_ff.
  Shared Expert: wie dicht, aber mit dem Sigmoid-Gate s(t) gewichtet.
  -> exp_spalten_L [k, 2] (Experte, Neuron), shared_spalten_L [k]; Patch mit 05m_patch_moe.py.
  --pruefe-moe rechnet den MoE-Ausgang aus den eigenen Aktivierungen nach (Selbstkontrolle gegen HF).

--modus voll lädt das ganze Modell auf einmal (nur für Tests: gleiche Rechnung, anderer Speicherweg).
"""
import argparse
import json
import os
import sys
import time

import numpy as np

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
import wsp_lib as W  # noqa: E402


# ------------------------------------------------------------------ Labels (identisch zu 04_richtung.py)

def labels(gen, min_lauf):
    n = len(gen)
    rep = np.zeros(n, dtype=bool)
    gesehen = set()
    for t in range(7, n):
        g = tuple(gen[t - 7:t + 1])
        rep[t] = g in gesehen
        gesehen.add(g)
    lauf = np.zeros(n, dtype=bool)
    t = 0
    onset = n
    while t < n:
        if rep[t]:
            s = t
            while t < n and rep[t]:
                t += 1
            if t - s >= min_lauf:
                lauf[s:t] = True
                onset = min(onset, s)
        else:
            t += 1
    return rep, lauf, onset


def positionen(texte, a, rng):
    """Gleiche Auswahl (und gleiche Reihenfolge der Zufallszüge) wie 04_richtung.py.

    --kontrast: statt Schleifen-Erkennung stehen die Klassen im Datensatz:
      klasse_a  Token-Indizes in gen_ids mit dem unerwünschten Merkmal (z. B. Rechtschreibfehler) -> wie "rep"
      klasse_b  Token-Indizes ohne Merkmal (fehlt: alle übrigen Antwort-Tokens ab Index 1)        -> wie "prod"
    Position t (Eingabe-Token t) sagt Token t+1 voraus -> Token-Index g wird an Position g-1 gemessen.
    """
    jobs = []
    hz, nz = getattr(a, "halte_zurueck", 0), getattr(a, "nur_zurueckgehalten", 0)
    for i_text, r in enumerate(texte[:a.max_texte]):
        if hz and i_text % hz == 0:      # zurückgehalten für den Prüfstand
            continue
        if nz and i_text % nz != 0:      # Prüfstand: nur die zurückgehaltenen
            continue
        gen = r["gen_ids"][:a.max_len]
        P = len(r["prompt_ids"])
        onset = len(gen)
        if a.kontrast:
            ka = sorted({g for g in r.get("klasse_a", []) if 1 <= g < len(gen)})
            if "klasse_b" in r:
                kb = sorted({g for g in r["klasse_b"] if 1 <= g < len(gen)} - set(ka))
            else:
                kb = sorted(set(range(1, len(gen))) - set(ka))
            rep_pos, prod_pos = [g - 1 for g in ka], [g - 1 for g in kb]
            ein_pos = sorted({g - 1 for g in r.get("klasse_e", []) if 1 <= g < len(gen)})
        else:
            ein_pos = []
            rep, lauf, onset = labels(gen, a.min_lauf)
            rep_pos = [t for t in range(len(gen) - 1) if lauf[t + 1]]
            prod_pos = [t for t in range(7, min(onset, len(gen)) - 1) if not rep[t + 1]]
        if not rep_pos and not prod_pos:
            continue
        if len(rep_pos) > a.pos_je_text:
            rep_pos = sorted(rng.choice(rep_pos, a.pos_je_text, replace=False).tolist())
        if len(prod_pos) > a.pos_je_text:
            prod_pos = sorted(rng.choice(prod_pos, a.pos_je_text, replace=False).tolist())
        jobs.append({"id": r["id"], "ids": r["prompt_ids"] + gen, "n_gen": len(gen), "onset": onset, "P": P,
                     "ke": [P + t for t in ein_pos],
                     "ir": [P + t for t in rep_pos], "ip": [P + t for t in prod_pos]})
    return jobs


# ------------------------------------------------------------------ Modell-Gerüst und schichtweises Laden

def geruest(pfad, dtype, voll):
    import torch
    import transformers as tf
    dt = {"bf16": torch.bfloat16, "f32": torch.float32}[dtype]
    cfg = tf.AutoConfig.from_pretrained(pfad)
    m = None
    for cls in ("AutoModelForImageTextToText", "AutoModelForCausalLM"):
        try:
            if voll:
                m = getattr(tf, cls).from_pretrained(pfad, dtype=dt)
            else:
                with torch.device("meta"):
                    m = getattr(tf, cls).from_config(cfg, dtype=dt)
            break
        except Exception as e:  # noqa: BLE001
            print(f"{cls}: {e}")
    if m is None:
        raise SystemExit("Modell-Gerüst ließ sich nicht bauen")
    m.eval()
    kand = [(n, mod) for n, mod in m.named_modules()
            if isinstance(getattr(mod, "layers", None), torch.nn.ModuleList) and hasattr(mod, "embed_tokens")]
    kand.sort(key=lambda x: ("language_model" not in x[0], -len(x[1].layers)))
    name, tm = kand[0]
    if not voll:  # Rotary-Puffer auf CPU neu berechnen (auf meta gibt es keine Werte)
        tm.rotary_emb = type(tm.rotary_emb)(config=tm.config)
    return m, name, tm, dt


class Lader:
    """Lädt Parameter eines Teilmoduls aus den safetensors (Namen = Modulpfad, wie im Checkpoint)."""

    def __init__(self, pfad):
        self.pfad = pfad
        self.index = W.tensor_index(pfad)
        self.offen = {}

    def tensor(self, key):
        from safetensors import safe_open
        shard = self.index[key]
        if shard not in self.offen:
            self.offen[shard] = safe_open(os.path.join(self.pfad, shard), framework="pt")
        return self.offen[shard].get_tensor(key)

    def tensor_mmap(self, key):
        """Tensor als Sicht auf die gemappte Datei (keine Kopie im RAM, belastet den Zusagespeicher nicht).
        Nur lesen bzw. direkt auf ein anderes Gerät kopieren (.to("cuda"))."""
        import warnings

        import torch
        dt, arr = W.tensor_lesen(self.pfad, key, self.index)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")  # nicht beschreibbares Array -> Warnung von torch.from_numpy
            t = torch.from_numpy(arr)
        return t.view(torch.bfloat16) if dt == "BF16" else t

    def zeilen(self, key, ids):
        """Nur die benötigten Zeilen einer großen Tabelle (z. B. Einbettung 248k x 2048) lesen."""
        import torch
        dt, arr = W.tensor_lesen(self.pfad, key, self.index)
        t = torch.from_numpy(np.ascontiguousarray(arr[np.asarray(ids)]))
        return t.view(torch.bfloat16) if dt == "BF16" else t

    def experten_gestapelt(self, praefix, name):
        """Fallback für Checkpoints mit Einzel-Experten (experts.{e}.gate_proj/up_proj/down_proj)."""
        import torch
        basis = praefix + name.rsplit(".", 1)[0]  # ...mlp.experts
        n = 0
        while f"{basis}.{n}.down_proj.weight" in self.index:
            n += 1
        if name.endswith("gate_up_proj"):
            return torch.stack([torch.cat([self.tensor(f"{basis}.{e}.gate_proj.weight"),
                                           self.tensor(f"{basis}.{e}.up_proj.weight")], 0) for e in range(n)])
        return torch.stack([self.tensor(f"{basis}.{e}.down_proj.weight") for e in range(n)])

    def lade(self, modul, praefix, dt, dev=None):
        """Lädt die Parameter von `modul`. Mit dev=cuda direkt aus der gemappten Datei auf die GPU (keine
        RAM-Kopie); sonst als RAM-Kopie (CPU-Rechnung braucht beschreibbare Tensoren)."""
        import torch
        gpu = dev is not None and torch.device(dev).type == "cuda"
        sd = {}
        for name, p in modul.named_parameters():
            key = praefix + name
            if key in self.index:
                t = self.tensor_mmap(key).to(dev) if gpu else self.tensor(key)
            elif name.endswith(("experts.gate_up_proj", "experts.down_proj")):
                t = self.experten_gestapelt(praefix, name)
                t = t.to(dev) if gpu else t
            else:
                raise KeyError(f"nicht im Checkpoint: {key}")
            assert tuple(t.shape) == tuple(p.shape), (key, tuple(t.shape), tuple(p.shape))
            sd[name] = t.to(p.dtype if p.dtype.is_floating_point else t.dtype)
        modul.load_state_dict(sd, strict=True, assign=True)

    def schliessen(self):
        self.offen.clear()


def schicht_vorwaerts(layer, h, tm, L):
    """Eine Decoder-Schicht auf h [1, T, d] anwenden – exakt wie Qwen3_5TextModel.forward (nur Text, ohne Cache)."""
    import torch
    from transformers import masking_utils as MU
    cfg = tm.config
    T = h.shape[1]
    pos_ids = torch.arange(T, device=h.device).view(1, 1, -1).expand(4, 1, -1)
    text_pos, rope_pos = pos_ids[0], pos_ids[1:]
    mk = {"config": cfg, "inputs_embeds": h, "attention_mask": None, "past_key_values": None,
          "position_ids": text_pos}
    if hasattr(cfg, "layer_types"):
        maske = (MU.create_causal_mask(**mk) if cfg.layer_types[L] == "full_attention"
                 else MU.create_recurrent_attention_mask(**mk))
    else:
        maske = MU.create_causal_mask(**mk)
    pe = tm.rotary_emb(h, rope_pos)
    h_neu = layer(h, position_embeddings=pe, attention_mask=maske, position_ids=text_pos,
                  past_key_values=None, use_cache=False)
    return h_neu[0] if isinstance(h_neu, tuple) else h_neu


# ------------------------------------------------------------------ MoE-Aktivierungen an ausgewählten Positionen

def moe_aktivierungen(mlp, x, pos, router_f32=False):
    """x [T, H] (Eingang des MoE-Blocks), pos: Positionen -> (G [n, E, I] float32 = g * a, s [n] Shared-Gate).

    Router exakt wie Qwen3_5MoeTopKRouter (Logits im Modell-dtype, Softmax in float32 -> gleiche Expertenwahl),
    Experten-Aktivierungen dann in float32 und nur für `pos`.
    """
    import torch
    import torch.nn.functional as F
    xs = x[pos].float()
    logits = F.linear(xs, mlp.gate.weight.float()) if router_f32 else F.linear(x[pos], mlp.gate.weight)
    probs = torch.softmax(logits, dtype=torch.float, dim=-1)
    top_w, top_i = torch.topk(probs, mlp.gate.top_k, dim=-1)
    top_w = top_w / top_w.sum(-1, keepdim=True)
    ex = mlp.experts
    E, I = ex.down_proj.shape[0], ex.down_proj.shape[2]
    G = torch.zeros(len(pos), E, I, device=x.device)
    for e in torch.unique(top_i).tolist():
        zeilen, k = torch.where(top_i == e)
        gu = F.linear(xs[zeilen], ex.gate_up_proj[e].float())
        g, u = gu.chunk(2, dim=-1)
        G[zeilen, e] = ex.act_fn(g) * u * top_w[zeilen, k, None]
    s = torch.sigmoid(F.linear(xs, mlp.shared_expert_gate.weight.float()))[:, 0]
    return G, s, top_i


def pruefe_moe(mlp, x, pos, G, s, a_shared, y_hf):
    """Nachrechnen: sum_e W_e (g*a) + s * W_sh a_sh  ==  HF-Ausgang des MoE-Blocks (rel. Fehler)."""
    import torch
    down = mlp.experts.down_proj.float()                         # [E, H, I]
    y = torch.einsum("ehi,nei->nh", down, G)
    y = y + s[:, None] * (a_shared[pos].float() @ mlp.shared_expert.down_proj.weight.float().T)
    ref = y_hf[pos].float()
    return float(torch.linalg.norm(y - ref) / torch.linalg.norm(ref)), y


def pruefe_moe_f32(mlp, cfg, x, pos, y_mein, y_hf):
    """Gegenprobe in float32: derselbe HF-Block (gleiche Klasse, gleiche Gewichte) auf der CPU in float32.
    Trennt Rundung (HF rechnet in bf16) von echten Fehlern der Nachrechnung.
    -> (mein vs HF-f32, HF-bf16 vs HF-f32)"""
    import torch
    sd = {k: v.detach().to("cpu", torch.float32) for k, v in mlp.state_dict().items()}
    with torch.device("meta"):
        m32 = type(mlp)(cfg)
    m32.load_state_dict(sd, strict=True, assign=True)
    m32.eval()
    with torch.no_grad():
        y32 = m32(x[pos].detach().to("cpu", torch.float32)[None])
        y32 = (y32[0] if isinstance(y32, tuple) else y32)[0]
    n = torch.linalg.norm(y32)
    a = float(torch.linalg.norm(y_mein.cpu() - y32) / n)
    b = float(torch.linalg.norm(y_hf[pos].float().cpu() - y32) / n)
    # c: meine Nachrechnung KOMPLETT in float32 (Router + Shared Expert) -> muss mit HF-f32 übereinstimmen
    import torch.nn.functional as F
    G, s, _ = moe_aktivierungen(mlp, x, pos, router_f32=True)
    xs, sh = x[pos].float(), mlp.shared_expert
    a_sh = sh.act_fn(F.linear(xs, sh.gate_proj.weight.float())) * F.linear(xs, sh.up_proj.weight.float())
    y_m = torch.einsum("ehi,nei->nh", mlp.experts.down_proj.float(), G) + s[:, None] * (a_sh @ sh.down_proj.weight.float().T)
    c = float(torch.linalg.norm(y_m.cpu() - y32) / n)
    del m32, sd
    return a, b, c


# ------------------------------------------------------------------ Hauptprogramm

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--modell", required=True)
    ap.add_argument("--ergebnisse", required=True, help="ergebnisse.jsonl (03_eval.py) mit prompt_ids/gen_ids")
    ap.add_argument("--edit-schichten", default="15,19")
    ap.add_argument("--schichten", default="alle", help="Schichten für die Richtungs-Analyse")
    ap.add_argument("--max-len", type=int, default=8192)
    ap.add_argument("--pos-je-text", type=int, default=400)
    ap.add_argument("--min-lauf", type=int, default=32)
    ap.add_argument("--max-texte", type=int, default=64)
    ap.add_argument("--top-k", type=int, default=64, help="dicht: Spalten; MoE: Experten-Neuronen")
    ap.add_argument("--top-k-shared", type=int, default=64, help="MoE: Neuronen des Shared Expert")
    ap.add_argument("--dtype", default="bf16", choices=["bf16", "f32"])
    ap.add_argument("--threads", type=int, default=0)
    ap.add_argument("--mit", help="mit_richtung.npz (Abgleich)")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--modus", default="schicht", choices=["schicht", "voll"])
    ap.add_argument("--pruefe-moe", action="store_true")
    ap.add_argument("--kontrast", action="store_true",
                    help="Klassen aus dem Datensatz (klasse_a / klasse_b) statt Schleifen-Erkennung")
    ap.add_argument("--geraet", default="cpu", help="cpu oder cuda (Schicht + ein Transkript auf der GPU)")
    ap.add_argument("--halte-zurueck", type=int, default=0,
                    help="N: jedes N-te Transkript (Index %% N == 0) auslassen -> für 09_pruefstand.py --nur-zurueckgehalten N")
    ap.add_argument("--nicht-kuerzen", action="store_true",
                    help="Transkripte nicht nach der letzten benötigten Position abschneiden")
    ap.add_argument("--aus", required=True)
    a = ap.parse_args()

    import torch
    if a.threads:
        torch.set_num_threads(a.threads)
    dev = torch.device(a.geraet)
    t0 = time.time()
    rng = np.random.default_rng(a.seed)
    model, tpfad, tm, dt = geruest(a.modell, a.dtype, a.modus == "voll")
    layers, cfg = tm.layers, tm.config
    nL = len(layers)
    schichten = list(range(nL)) if a.schichten == "alle" else [int(x) for x in a.schichten.split(",")]
    edit = [int(x) for x in a.edit_schichten.split(",")] if a.edit_schichten else []
    bis = max(schichten + edit)
    praefix = tpfad + "."
    print(f"Decoder-Schichten: {tpfad} ({nL}); Analyse {schichten}; Edit {edit}; Modus {a.modus}; bis Schicht {bis}")

    texte = [json.loads(z) for z in open(a.ergebnisse, encoding="utf-8")]
    jobs = positionen(texte, a, rng)
    if not jobs:
        raise SystemExit("keine verwertbaren Transkripte")
    tok_voll = sum(len(j["ids"]) for j in jobs)
    if not a.nicht_kuerzen:  # kausales Modell: Tokens nach der letzten Messposition ändern nichts
        for j in jobs:
            j["ids"] = j["ids"][:max(j["ir"] + j["ip"]) + 1]
    tok = sum(len(j["ids"]) for j in jobs)
    print(f"{len(jobs)} Transkripte, {tok} Tokens (ungekürzt {tok_voll}); Gerät {dev}", flush=True)
    lader = Lader(a.modell)

    # Embeddings (auf CPU; Zustände aller Transkripte bleiben im RAM, je Schicht wandert eins auf das Gerät)
    H = []
    with torch.no_grad():
        if a.modus == "schicht" and type(tm.embed_tokens) is torch.nn.Embedding:
            # nur die benötigten Zeilen aus der gemappten Datei (spart ~1 GB RAM beim 35B)
            for j in jobs:
                H.append(lader.zeilen(praefix + "embed_tokens.weight", j["ids"]).to(dt)[None])
        else:
            if a.modus == "schicht":
                lader.lade(tm.embed_tokens, praefix + "embed_tokens.", dt)
            for j in jobs:
                H.append(tm.embed_tokens(torch.tensor([j["ids"]])))
            if a.modus == "schicht":
                tm.embed_tokens.to("meta")
    tm.rotary_emb.to(dev)

    acc, nacc, eacc, sacc, halb = {}, {}, {}, {}, {}
    out, bericht = {}, {"statistik": {"texte": len(jobs), "pos_rep": sum(len(j["ir"]) for j in jobs),
                                      "pos_prod": sum(len(j["ip"]) for j in jobs)}, "schichten": {}}
    mit = dict(np.load(a.mit)) if a.mit else {}

    f32_gemacht = []
    for L in range(bis + 1):
        tL = time.time()
        layer = layers[L]
        if a.modus == "schicht":
            lader.lade(layer, f"{praefix}layers.{L}.", dt, dev)
        layer.to(dev)
        ist_moe = hasattr(layer.mlp, "experts")
        fang = {}
        hooks = []
        if L in edit:
            if ist_moe:
                hooks.append(layer.mlp.register_forward_pre_hook(lambda m, i: fang.__setitem__("x", i[0])))
                hooks.append(layer.mlp.register_forward_hook(lambda m, i, o: fang.__setitem__("y", o)))
                hooks.append(layer.mlp.shared_expert.down_proj.register_forward_pre_hook(
                    lambda m, i: fang.__setitem__("ash", i[0])))
            else:
                hooks.append(layer.mlp.down_proj.register_forward_pre_hook(
                    lambda m, i: fang.__setitem__("a", i[0][0].float())))
        pruef, pruef_f32 = [], []
        for k, j in enumerate(jobs):
            h = H[k].to(dev)
            T = h.shape[1]
            with torch.no_grad():
                h_neu = schicht_vorwaerts(layer, h, tm, L)
            H[k] = h_neu.to("cpu")
            ir = torch.tensor(j["ir"], dtype=torch.long, device=dev)
            ip = torch.tensor(j["ip"], dtype=torch.long, device=dev)
            if L in schichten:
                x = h_neu[0].float()
                d = x.shape[1]
                s = acc.setdefault(L, {"sr": np.zeros(d), "sp": np.zeros(d), "qr": np.zeros((d, d)),
                                       "qp": np.zeros((d, d)), "nr": 0, "np": 0})
                hb = halb.setdefault(L, [{"sr": np.zeros(d), "sp": np.zeros(d), "nr": 0, "np": 0} for _ in range(2)])[k % 2]
                if len(ir):
                    xr = x[ir].double().cpu().numpy()
                    s["sr"] += xr.sum(0); s["qr"] += xr.T @ xr; s["nr"] += len(ir)
                    hb["sr"] += xr.sum(0); hb["nr"] += len(ir)
                if len(ip):
                    xp = x[ip].double().cpu().numpy()
                    s["sp"] += xp.sum(0); s["qp"] += xp.T @ xp; s["np"] += len(ip)
                    hb["sp"] += xp.sum(0); hb["np"] += len(ip)
            if L in edit and not ist_moe:
                av = fang.pop("a")
                s = nacc.setdefault(L, {"ar": np.zeros(av.shape[1]), "ap": np.zeros(av.shape[1]), "nr": 0, "np": 0})
                if len(ir):
                    s["ar"] += av[ir].double().cpu().numpy().sum(0); s["nr"] += len(ir)
                if len(ip):
                    s["ap"] += av[ip].double().cpu().numpy().sum(0); s["np"] += len(ip)
            if L in edit and ist_moe:
                dim = h.shape[-1]
                xm = fang.pop("x").reshape(-1, dim)
                ash = fang.pop("ash")
                y = fang.pop("y").reshape(-1, dim)
                for cls, idx in (("r", ir), ("p", ip)):
                    if not len(idx):
                        continue
                    with torch.no_grad():
                        G, sg, _ = moe_aktivierungen(layer.mlp, xm, idx)
                        if a.pruefe_moe and len(pruef) < 4:
                            rel, y_mein = pruefe_moe(layer.mlp, xm, idx, G, sg, ash, y)
                            pruef.append(rel)
                            if not pruef_f32 and not f32_gemacht:  # float32-Gegenprobe einmal (CPU, ~3 GB RAM)
                                pruef_f32.append(pruefe_moe_f32(layer.mlp, tm.config, xm, idx, y_mein, y))
                                f32_gemacht.append(L)
                    E_, I_ = G.shape[1], G.shape[2]
                    se = eacc.setdefault(L, {"ar": np.zeros((E_, I_)), "ap": np.zeros((E_, I_)), "nr": 0, "np": 0})
                    se["a" + cls] += G.double().sum(0).cpu().numpy(); se["n" + cls] += len(idx)
                    sh = (ash[idx].float() * sg[:, None]).double().cpu().numpy()
                    ss = sacc.setdefault(L, {"ar": np.zeros(sh.shape[1]), "ap": np.zeros(sh.shape[1]), "nr": 0, "np": 0})
                    ss["a" + cls] += sh.sum(0); ss["n" + cls] += len(idx)
            fang.clear()
            if L == 0:
                print(f"{j['id']}: {j['n_gen']} Tok, Schleife ab {j['onset'] if j['onset'] < j['n_gen'] else '-'}, "
                      f"rep {len(ir)} / prod {len(ip)}, gerechnet {T} Tok", flush=True)
        for hk in hooks:
            hk.remove()

        # Richtung dieser Schicht ist jetzt vollständig -> sofort auswerten (Gewichte sind noch geladen)
        if L in schichten:
            s = acc[L]
            if s["nr"] == 0 or s["np"] == 0:
                raise SystemExit("Zu wenig Positionen in einer der Klassen (Schleife/Fehler UND produktiv/korrekt nötig)")
            mr, mp = s["sr"] / s["nr"], s["sp"] / s["np"]
            Cr = s["qr"] / s["nr"] - np.outer(mr, mr)
            Cp = s["qp"] / s["np"] - np.outer(mp, mp)
            diff = mr - mp
            u = diff / np.linalg.norm(diff)
            dprime = float((diff @ u) / np.sqrt(0.5 * (u @ Cr @ u + u @ Cp @ u)))
            out[f"u_{L}"] = u.astype(np.float32)
            b = {"d_prime": round(dprime, 3), "abstand": round(float(np.linalg.norm(diff)), 3)}
            for k_ in [k_ for k_ in mit if k_.startswith("u_")]:
                b[f"cos_mit_{k_[2:]}"] = round(float(abs(u @ mit[k_])), 3)
            hs = halb.pop(L)
            if all(h_["nr"] and h_["np"] for h_ in hs):  # Stabilität: Richtung aus Hälfte A vs. Hälfte B
                uh = [(h_["sr"] / h_["nr"] - h_["sp"] / h_["np"]) for h_ in hs]
                b["stabilitaet_cos_halbe"] = round(float(uh[0] @ uh[1] / (np.linalg.norm(uh[0]) * np.linalg.norm(uh[1]))), 4)
            bericht["schichten"][L] = b
            del acc[L]
        if L in edit:
            u = out[f"u_{L}"].astype(np.float64) if f"u_{L}" in out else None
            if u is None:
                raise SystemExit(f"Edit-Schicht {L} muss auch in --schichten liegen")
            b = bericht["schichten"][L]
            if not ist_moe:
                Wd = layer.mlp.down_proj.weight.detach().float().cpu().double().numpy()
                s = nacc[L]
                da = s["ar"] / s["nr"] - s["ap"] / s["np"]
                score = da * (u @ Wd)
                top = np.argsort(-score)[:a.top_k]
                out[f"spalten_{L}"] = np.sort(top)
                out[f"score_{L}"] = score.astype(np.float32)
                b["tensor"] = f"{praefix}layers.{L}.mlp.down_proj.weight"
                b["top_k"] = a.top_k
                if f"spalten_{L}" in mit:
                    ref = set(mit[f"spalten_{L}"].tolist())
                    b["ueberschneidung_mit_spalten"] = len(ref & set(top.tolist()))
                    if f"u_{L}" in mit:
                        sm = da * (mit[f"u_{L}"].astype(np.float64) @ Wd)
                        b["ueberschneidung_bei_mit_u"] = len(ref & set(np.argsort(-sm)[:a.top_k].tolist()))
            else:
                down = layer.mlp.experts.down_proj.detach().float()            # [E, H, I]
                schreib = torch.einsum("h,ehi->ei", torch.from_numpy(u).float().to(down.device), down).double().cpu().numpy()
                se = eacc[L]
                da = se["ar"] / se["nr"] - se["ap"] / se["np"]
                score = da * schreib
                flach = np.argsort(-score.ravel())[:a.top_k]
                paare = np.stack(np.unravel_index(flach, score.shape), 1)
                out[f"exp_spalten_{L}"] = paare[np.lexsort((paare[:, 1], paare[:, 0]))].astype(np.int64)
                out[f"exp_score_{L}"] = score.astype(np.float32)
                ss = sacc[L]
                Wsh = layer.mlp.shared_expert.down_proj.weight.detach().float().cpu().double().numpy()
                dsh = ss["ar"] / ss["nr"] - ss["ap"] / ss["np"]
                ssc = dsh * (u @ Wsh)
                out[f"shared_spalten_{L}"] = np.sort(np.argsort(-ssc)[:a.top_k_shared])
                out[f"shared_score_{L}"] = ssc.astype(np.float32)
                b["moe"] = {"top_k_experten": a.top_k, "experten_betroffen": int(len(set(paare[:, 0].tolist()))),
                            "top_k_shared": a.top_k_shared,
                            "anteil_score_experten": round(float(np.sort(score.ravel())[-a.top_k:].sum() /
                                                                 (np.sort(score.ravel())[-a.top_k:].sum() +
                                                                  np.sort(ssc)[-a.top_k_shared:].sum())), 3)}
                if pruef:
                    b["moe"]["pruefung_rel_fehler_max"] = round(max(pruef), 5)
                    print(f"  MoE-Nachrechnung Schicht {L}: rel. Fehler gegen HF-bf16 max {max(pruef):.2e}", flush=True)
                if pruef_f32:
                    mf, hf, m32 = pruef_f32[0]
                    b["moe"]["pruefung_f32"] = {"mein_vs_hf_f32": round(mf, 6), "hf_bf16_vs_hf_f32": round(hf, 6),
                                                "mein_ganz_f32_vs_hf_f32": round(m32, 8)}
                    print(f"  float32-Gegenprobe Schicht {L}: meine Nachrechnung vs HF-f32 {mf:.2e}, "
                          f"HF-bf16 vs HF-f32 {hf:.2e}, meine Rechnung ganz in f32 vs HF-f32 {m32:.2e}", flush=True)
        if a.modus == "schicht":
            layer.to("meta")
        else:
            layer.to("cpu")
        if dev.type == "cuda":
            torch.cuda.empty_cache()
        print(f"Schicht {L}/{bis} fertig ({time.time() - tL:.1f} s, gesamt {time.time() - t0:.0f} s)", flush=True)
    lader.schliessen()

    os.makedirs(os.path.dirname(os.path.abspath(a.aus)), exist_ok=True)
    np.savez(a.aus, **out)
    rang = sorted(bericht["schichten"].items(), key=lambda kv: -kv[1]["d_prime"])
    bericht["staerkste_schichten"] = [L for L, _ in rang[:6]]
    bericht["laufzeit_s"] = round(time.time() - t0, 1)
    bericht["modus"] = a.modus
    bericht["geraet"] = str(dev)
    bericht["kontrast"] = bool(a.kontrast)
    bericht["tokens_gerechnet"], bericht["tokens_ungekuerzt"] = tok, tok_voll
    json.dump(bericht, open(os.path.splitext(a.aus)[0] + ".json", "w"), indent=1)
    print(json.dumps(bericht, indent=1))


if __name__ == "__main__":
    main()
