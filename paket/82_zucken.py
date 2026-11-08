"""Zuck-Messung (08.11. nachts; NACHTRÄGLICH, beschreibend). Teacher-Forcing auf VORHANDENEN Läufen; keine Generierung, keine
neuen Aufgaben.
Fragen des Nutzers (~00:50–01:05):
  „Gab es ein Zucken? Wenn ja, weil die Lösung wahr ist oder nicht? Wie stark?“
  „Wenn kein Zucken: eher entmutigt oder unterbrochen? Fehlt der Horizont? Gleiche Präzision mit dem längeren Atem?“
Zwei Einsätze:
  A) --quelle WT-A --modell Qwen3.5-0.8B-ergo-zigA:
     Wie zuckt WT-A in seinen eigenen Läufen (161–300)? Mit --ablation werden dieselben Stellen zusätzlich ohne die 16 WT-Neuronen
     gemessen (≈ eigen). Das zeigt die Wirkung des Reflexes, auch einen Gegenschub („entmutigt?“).
  B) --quelle MIT --modell Qwen3.5-0.8B-mit-wt:
     Wo hätte der Reflex in MITs Läufen gezuckt? Die L15-Eingänge sind für denselben Text bei Basis, eigen, MIT, WT-A und MIT+WT
     gleich, weil alle Eingriffe in down_proj von L15/L19 bzw. in den 16 Neuronen sitzen.
     Mit MIT+WT (84) und --ablation ergibt sich die Zusatz-Abschlusswahrscheinlichkeit durch den Reflex an jeder Stelle. Daraus folgt
     eine SCHÄTZUNG, was MIT+WT auf denselben Aufgaben erreicht hätte. Das ist keine Messung.
Je Stelle des Denkens (bis zum ersten </think>, höchstens --max-tokens) wird gemessen:
  zT = κ_g·(s_T − τ_T). Größer 0 heißt Wahrheits-Tor offen; der Auslegungspunkt liegt bei 3.
  up = κ_u·(s_C − τ_C). Kontext „Kandidaten-Ende“; 1 ist typisch.
  S  = SiLU(zT)·up / SiLU(3). 1 ist der volle Reflex; negativ heißt Schub weg vom Abschluss.
An ausgewählten Stellen wird p(</think>) bestimmt, jeweils mit und (bei --ablation) ohne Reflex:
  - roh (Softmax);
  - „gezogen“ nach dem Lauf-Protokoll: Strafe auf schon vorgekommene Tokens, Temperatur, top-k, top-p.
Ausgewählt werden:
  - Wert-Aussagen (wie 76): das Wert-Ende und die Stelle mit dem größten S im Fenster [+0, +12];
  - alle Stellen mit |S| ≥ 0,02 (höchstens 1500, die größten);
  - die Abschluss-Stelle;
  - ein Raster alle 256 Tokens.
Wahrheit der Wert-Aussagen kommt aus dem Zwischenspeicher (80); fehlt ein Paar, gilt es als „unbekannt“.
Die Läufe kamen aus llama.cpp (q8_0); gemessen wird in transformers (float32). Kleine Zahlenabweichungen sind möglich.
  python 82_zucken.py --quelle WT-A --modell Qwen3.5-0.8B-ergo-zigA --ablation --geraet cuda
  python 82_zucken.py --quelle MIT  --modell Qwen3.5-0.8B-mit-wt   --ablation --geraet cuda
  python 82_zucken.py --auswerten --quelle WT-A|MIT --modell …
"""
import argparse
import collections
import importlib.util
import json
import os
import re
import time

import numpy as np

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(HIER)
ERG = os.path.join(WURZEL, "ergebnisse")
QUELLEN = {"WT-A": ["s3-wta-161-210", "s3-wta-211-260", "s3-wta-261-300"], "MIT": ["s3-mit-161-260", "s3-mit-261-300"]}
FENSTER = 12


def lade_mod(name, pfad):
    s = importlib.util.spec_from_file_location(name, pfad)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


def laufe(dirs):
    R = {}
    for d in dirs:
        for z in open(os.path.join(ERG, d, "ergebnisse.jsonl"), encoding="utf-8"):
            r = json.loads(z)
            R[r["id"]] = r
    return R


def sig(z):
    return 1.0 / (1.0 + np.exp(-np.clip(z, -60, 60)))


def ausgabe(quelle, modell):
    tag = modell.replace("Qwen3.5-0.8B-", "")
    return os.path.join(ERG, f"zucken_{quelle}_{tag}.jsonl")


def messen(a):
    import torch
    import transformers as tf
    torch.set_num_threads(int(os.environ.get("WSP_THREADS", 6)))
    dev = torch.device(a.geraet)
    dt = {"f32": torch.float32, "bf16": torch.bfloat16}[a.dtype]
    wm = lade_mod("wm", os.path.join(HIER, "42_wahrheitsmelder.py"))
    k2 = lade_mod("k2", os.path.join(HIER, "76_kandidaten_v2.py"))
    tok = tf.AutoTokenizer.from_pretrained(os.path.join(WURZEL, "modelle", "Qwen3.5-0.8B"))
    ZU = tok.convert_tokens_to_ids("</think>")
    memo = {}
    cp = os.path.join(ERG, "wertcache.json")
    if os.path.exists(cp):
        memo = {(c, g): bool(v) for c, g, v in json.load(open(cp, encoding="utf-8"))}
    Q = laufe(QUELLEN[a.quelle])
    W_, M_ = laufe(QUELLEN["WT-A"]), laufe(QUELLEN["MIT"])
    ids = sorted(set(W_) & set(M_))
    nur_mit = [i for i in ids if M_[i]["korrekt"] and not W_[i]["korrekt"]]
    nur_wta = [i for i in ids if W_[i]["korrekt"] and not M_[i]["korrekt"]]
    rest = [i for i in ids if i not in set(nur_mit) | set(nur_wta)]
    reihe = [(i, "nur MIT richtig") for i in nur_mit] + [(i, "nur WT-A richtig") for i in nur_wta] + [(i, "gleich") for i in rest]
    if a.ids:
        reihe = [(i, g) for i, g in reihe if i in set(a.ids.split(","))]
    prot = json.load(open(os.path.join(ERG, QUELLEN[a.quelle][0], "zusammenfassung.json"), encoding="utf-8"))["protokoll"]
    assert prot["samplers"] == ["penalties", "temperature", "top_k", "top_p", "min_p"] and prot["min_p"] == 0.0, prot
    aus = a.aus or ausgabe(a.quelle, a.modell)
    fertig = {json.loads(z)["id"] for z in open(aus, encoding="utf-8")} if os.path.exists(aus) else set()
    print(f"Quelle {a.quelle}, Modell {a.modell}, Gerät {a.geraet}/{a.dtype}, Ablation {a.ablation} | Aufgaben {len(reihe)}, "
          f"schon fertig {len(fertig)} | Protokoll T {prot['temperature']} top-k {prot['top_k']} top-p {prot['top_p']} "
          f"Strafe {prot['presence_penalty']}", flush=True)
    mdir = os.path.join(WURZEL, "modelle", a.modell)
    meta = json.load(open(os.path.join(mdir, "wsp_patch.json"), encoding="utf-8"))
    G, z_ziel = meta["neuronen"], float(meta["z_ziel"])
    silu_ziel = z_ziel * float(sig(z_ziel))
    cls = getattr(tf, "AutoModelForImageTextToText", None) or tf.AutoModelForCausalLM
    model = cls.from_pretrained(mdir, dtype=dt).to(dev).eval()
    head = model.get_output_embeddings()
    mlp = norm = None
    for n_, m_ in model.named_modules():
        if re.search(r"language_model\.layers\.15\.mlp$", n_):
            mlp = m_
        if re.search(r"(language_model|model)\.norm$", n_) and "visual" not in n_:
            norm = m_
    assert mlp is not None and norm is not None, "Module nicht gefunden"
    Wg, Wu = mlp.gate_proj.weight[G].detach(), mlp.up_proj.weight[G].detach()
    assert torch.allclose(Wg, Wg[:1].expand_as(Wg)) and torch.allclose(Wu, Wu[:1].expand_as(Wu)), "WT-Zeilen nicht gleich"
    wg, wu = Wg[0].clone().float(), Wu[0].clone().float()
    Gt = torch.tensor(G, device=dev)
    cap = {"ablation": False}

    def h_mlp(mod, args):
        x = args[0][0].float()
        cap["zT"] = (x @ wg).cpu().numpy().astype(np.float64)
        cap["up"] = (x @ wu).cpu().numpy().astype(np.float64)

    def h_down(mod, args):  # Ablation: die 16 WT-Neuronen stumm (≈ Modell ohne Reflex)
        if cap["ablation"]:
            args[0][..., Gt] = 0

    def h_norm(mod, args, out):
        o = out[0] if isinstance(out, tuple) else out
        cap["hn"] = o[0].detach()

    mlp.register_forward_pre_hook(h_mlp)
    mlp.down_proj.register_forward_pre_hook(h_down)
    norm.register_forward_hook(h_norm)
    V = head.weight.shape[0]

    def p_stellen(hn, abs_pos, first_occ):
        """p(</think>) roh und gezogen (Strafe → Temperatur → top-k → top-p) an absoluten Positionen."""
        roh, gez = [], []
        for k0 in range(0, len(abs_pos), 256):
            ap_ = torch.tensor(abs_pos[k0:k0 + 256], device=dev)
            with torch.no_grad():
                lg = head(hn[ap_]).float()
                roh += torch.softmax(lg, -1)[:, ZU].tolist()
                gesehen = first_occ[None, :] <= ap_[:, None]
                l2 = (lg - prot["presence_penalty"] * gesehen.float()) / prot["temperature"]
                tv, ti = l2.topk(int(prot["top_k"]), dim=-1)
                pr = torch.softmax(tv, -1)
                behalten = (pr.cumsum(-1) - pr) < prot["top_p"]
                pr = pr * behalten
                pr = pr / pr.sum(-1, keepdim=True)
                gez += (pr * (ti == ZU)).sum(-1).tolist()
        return roh, gez

    zustand = {"geprueft": False}

    def eins(i, gruppe, max_tok):
        t_start = time.time()
        r = Q[i]
        g = r["gen_ids"]
        st = [tok.decode([t]) for t in g]
        gr = np.cumsum([len(s) for s in st]) if st else np.array([0])
        text = "".join(st)
        zc = text.find("</think>")
        zu_tok = g.index(ZU) if ZU in g else None
        denk = text if zc < 0 else text[:zc]
        antw = "" if zc < 0 else text[zc + len("</think>"):]
        if zc < 0:
            art = "nie geschlossen (" + r["ende"] + ")"
        elif "\\boxed" not in antw:
            art = "geschlossen, keine Antwort (" + r["ende"] + ")"
        elif not r["korrekt"]:
            art = "geschlossen, falsche Antwort"
        else:
            art = "richtig"
        ende = zu_tok if zu_tok is not None else len(g)
        n_mess = max(1, min(ende, max_tok))
        aussagen = {}
        for (_, e, c) in list(wm.kandidaten_mit_ende(denk)) + list(k2.wert_aussagen(denk)):
            t = min(int(np.searchsorted(gr, e - 1, side="right")), len(st) - 1)
            aussagen[(t, c)] = memo.get((c, r["gold"]))
        p0 = len(r["prompt_ids"])
        seq = r["prompt_ids"] + g[:n_mess]
        inp = torch.tensor([seq], device=dev)
        first_occ = torch.full((V,), 10 ** 9, dtype=torch.long, device=dev)
        first_occ.scatter_reduce_(0, inp[0], torch.arange(len(seq), device=dev), reduce="amin")
        with torch.no_grad():
            out = model(input_ids=inp, logits_to_keep=1)
        hn, zT, up = cap.pop("hn"), cap.pop("zT")[p0:], cap.pop("up")[p0:]
        if not zustand["geprueft"]:  # Endnorm-Haken liefert die echten Logits?
            assert torch.allclose(head(hn[-1:]).float(), out.logits[0, -1:].float(), atol=1e-2, rtol=1e-3), "Logit-Abgleich gescheitert"
            zustand["geprueft"] = True
            print("  (Logit-Abgleich über den Endnorm-Haken ok)", flush=True)
        del out
        S = zT * sig(zT) * up / silu_ziel
        A = []
        for (t, c), ok in sorted(aussagen.items()):
            if t >= n_mess:
                continue
            w1 = min(t + FENSTER, n_mess - 1)
            seg = S[t:w1 + 1]
            pa = t + int(np.argmax(seg))
            A.append({"t": t, "wert": c[:40], "ok": ok, "S_max": float(seg.max()), "S_min": float(seg.min()), "pa": pa,
                      "zT_max": float(zT[t:w1 + 1].max()), "up_max": float(up[t:w1 + 1].max()), "zT_arg": float(zT[pa]),
                      "up_arg": float(up[pa]), "zu_nach": (zu_tok - t) if zu_tok is not None else None})
        stark = np.where(np.abs(S[:n_mess]) >= 0.02)[0]
        if len(stark) > 1500:
            stark = stark[np.argsort(-np.abs(S[stark]))[:1500]]
        pos = set(int(q) for q in stark) | {s["pa"] for s in A} | {s["t"] for s in A} | set(range(0, n_mess, 256))
        if zu_tok is not None and 0 < zu_tok <= n_mess:
            pos.add(zu_tok - 1)
        pos = sorted(q for q in pos if q < n_mess)
        roh, gez = p_stellen(hn, [p0 + q for q in pos], first_occ)
        del hn
        roh_a = gez_a = None
        if a.ablation:
            cap["ablation"] = True
            with torch.no_grad():
                model(input_ids=inp, logits_to_keep=1)
            cap["ablation"] = False
            hn_a = cap.pop("hn")
            cap.pop("zT", None)
            cap.pop("up", None)
            roh_a, gez_a = p_stellen(hn_a, [p0 + q for q in pos], first_occ)
            del hn_a
        P = {q: (roh[k], gez[k], roh_a[k] if roh_a else None, gez_a[k] if gez_a else None) for k, q in enumerate(pos)}
        for s in A:
            s["p_arg"], s["ps_arg"], s["p_arg_abl"], s["ps_arg_abl"] = P[s["pa"]]
            s["p_t"], s["ps_t"], s["p_t_abl"], s["ps_t_abl"] = P[s["t"]]
        stellen = [[q, round(float(S[q]), 4), round(float(zT[q]), 3), round(float(up[q]), 3)] + [None if v is None else float(f"{v:.4g}") for v in P[q]]
                   for q in pos]
        top, belegt = [], []
        for q in np.argsort(-S[:n_mess])[:400]:
            q = int(q)
            if S[q] < 0.1 or len(top) >= 5:
                break
            if any(abs(q - b) < 20 for b in belegt):
                continue
            belegt.append(q)
            c0 = int(gr[q - 1]) if q > 0 else 0
            top.append({"t": q, "S": float(S[q]), "zT": float(zT[q]), "up": float(up[q]), "p": P.get(q),
                        "vor": text[max(0, c0 - 70):int(gr[q])][-90:], "nach": text[int(gr[q]):int(gr[q]) + 25]})
        Sm = S[:n_mess]
        rec = {"id": i, "gold": r["gold"], "gruppe": gruppe, "quelle": a.quelle, "modell": a.modell, "korrekt": bool(r["korrekt"]),
               "art": art, "ende": r["ende"], "zu_tok": zu_tok, "n_gen": len(g), "n_mess": int(n_mess), "abgeschnitten": bool(n_mess < ende),
               "wta_korrekt": bool(W_[i]["korrekt"]), "mit_korrekt": bool(M_[i]["korrekt"]), "aussagen": A, "stellen": stellen, "top": top,
               "jenseits": [[t, ok] for (t, c), ok in sorted(aussagen.items()) if t >= n_mess],
               "neg": {"anteil_unter_-0.05": float((Sm < -0.05).mean()), "min": float(Sm.min()), "summe_neg": float(Sm[Sm < 0].sum()),
                       "summe_pos": float(Sm[Sm > 0].sum()), "zT_offen_anteil": float((zT[:n_mess] > 0).mean())},
               "sekunden": round(time.time() - t_start, 1)}
        del inp, first_occ
        return rec, len(pos)

    n_neu = 0
    for i, gruppe in reihe:
        if i in fertig:
            continue
        if a.nur and n_neu >= a.nur:
            break
        rec = None
        for mt in sorted({a.max_tokens, min(a.max_tokens, 16384), min(a.max_tokens, 8192)}, reverse=True):
            try:
                rec, n_pos = eins(i, gruppe, mt)
                break
            except torch.cuda.OutOfMemoryError:
                cap.clear()
                cap["ablation"] = False
                torch.cuda.empty_cache()
                print(f"  {i}: Grafikspeicher voll bei höchstens {mt} Tokens – kürzer", flush=True)
        if rec is None:
            print(f"  {i}: übersprungen (Speicher)", flush=True)
            continue
        A = rec["aussagen"]
        with open(aus, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        n_neu += 1
        smax_ok = max([s["S_max"] for s in A if s["ok"]], default=None)
        smax_f = max([s["S_max"] for s in A if s["ok"] is False], default=None)
        print(f"  {i} [{gruppe}] {rec['art']} | Tokens {rec['n_mess']}{' (gekappt)' if rec['abgeschnitten'] else ''} | Aussagen {len(A)} "
              f"(richtig {sum(1 for s in A if s['ok'])}) | S max richtig {smax_ok if smax_ok is None else round(smax_ok, 2)}, falsch "
              f"{smax_f if smax_f is None else round(smax_f, 2)} | Stellen {n_pos} | {rec['sekunden']} s", flush=True)
        if dev.type == "cuda":
            torch.cuda.empty_cache()


def anteil(x):
    return f"{100 * float(np.mean(x)):.0f} %" if len(x) else "–"


def auswerten(a):
    aus = a.aus or ausgabe(a.quelle, a.modell)
    R = [json.loads(z) for z in open(aus, encoding="utf-8")]
    B = {"datei": os.path.basename(aus), "laeufe": len(R), "gekappt": sum(r["abgeschnitten"] for r in R)}
    print(f"{aus}: {len(R)} Läufe (gekappt {B['gekappt']})")
    # 1) Aussagen-Ebene: W (Tor offen), Kontext, Zucken (S), Wirkung (p mit/ohne Reflex)
    for name, sel in (("richtig", True), ("falsch", False)):
        X = [s for r in R for s in r["aussagen"] if s["ok"] is sel]
        if not X:
            continue
        S_ = np.array([s["S_max"] for s in X])
        e = {"n": len(X), "tor_offen": float(np.mean([s["zT_max"] > 0 for s in X])),
             "kontext(up>0.5)": float(np.mean([s["up_max"] > 0.5 for s in X])), "S>=0.1": float((S_ >= 0.1).mean()),
             "S>=0.5": float((S_ >= 0.5).mean()), "S>=1": float((S_ >= 1).mean()), "S_median": float(np.median(S_)),
             "ps>0.1": float(np.mean([s["ps_arg"] > 0.1 for s in X])), "ps>0.5": float(np.mean([s["ps_arg"] > 0.5 for s in X])),
             "gegenschub(S_min<-0.05)": float(np.mean([s["S_min"] < -0.05 for s in X]))}
        if X[0].get("ps_arg_abl") is not None:
            e["ps_abl>0.1"] = float(np.mean([s["ps_arg_abl"] > 0.1 for s in X]))
        B[f"aussagen_{name}"] = e
        print(f"Aussagen {name:7s} n {e['n']:5d} | Tor offen {100 * e['tor_offen']:.0f} % | Kandidaten-Ende {100 * e['kontext(up>0.5)']:.0f} % | "
              f"S≥0,1 {100 * e['S>=0.1']:.0f} %, S≥0,5 {100 * e['S>=0.5']:.0f} %, S≥1 {100 * e['S>=1']:.0f} % | p gezogen >0,1 "
              f"{100 * e['ps>0.1']:.0f} % (ohne Reflex {100 * e.get('ps_abl>0.1', float('nan')):.0f} %) | Gegenschub {100 * e['gegenschub(S_min<-0.05)']:.0f} %")
    Xr = [s["S_max"] for r in R for s in r["aussagen"] if s["ok"] is True]
    Xf = [s["S_max"] for r in R for s in r["aussagen"] if s["ok"] is False]
    if Xr and Xf:
        alle = np.concatenate([Xr, Xf])
        rang = alle.argsort().argsort() + 1.0
        B["auc_S"] = float((rang[:len(Xr)].sum() - len(Xr) * (len(Xr) + 1) / 2) / (len(Xr) * len(Xf)))
        zr = [s["zT_max"] for r in R for s in r["aussagen"] if s["ok"] is True]
        zf = [s["zT_max"] for r in R for s in r["aussagen"] if s["ok"] is False]
        alle = np.concatenate([zr, zf])
        rang = alle.argsort().argsort() + 1.0
        B["auc_zT"] = float((rang[:len(zr)].sum() - len(zr) * (len(zr) + 1) / 2) / (len(zr) * len(zf)))
        print(f"Trennschärfe richtig gegen falsch: AUC(S) {B['auc_S']:.3f}, AUC(Wahrheits-Tor zT) {B['auc_zT']:.3f}")
    # 2) Lauf-Ebene: Trichter
    def trichter(RR, schw=0.5):
        mit_wert = [r for r in RR if any(s["ok"] for s in r["aussagen"])]
        offen = [r for r in mit_wert if any(s["ok"] and s["zT_max"] > 0 for s in r["aussagen"])]
        zuck = [r for r in mit_wert if any(s["ok"] and s["S_max"] >= schw for s in r["aussagen"])]
        zu = [r for r in zuck if any(s["ok"] and s["S_max"] >= schw and s["zu_nach"] is not None and 0 < s["zu_nach"] <= 64 for s in r["aussagen"])]
        t = collections.OrderedDict([("richtiger Wert im Denken", len(mit_wert)), ("Tor offen an einem richtigen Wert (W)", len(offen)),
                                     (f"Zucken S≥{schw} an einem richtigen Wert", len(zuck)), ("danach ≤ 64 Tokens geschlossen (T)", len(zu)),
                                     ("richtig abgegeben", sum(r["korrekt"] for r in zu))])
        return t, mit_wert, offen, zuck, zu
    for name, RR in (("alle", R), ("nur MIT richtig", [r for r in R if r["gruppe"] == "nur MIT richtig"]),
                     ("nur WT-A richtig", [r for r in R if r["gruppe"] == "nur WT-A richtig"])):
        if not RR:
            continue
        t, mit_wert, offen, zuck, zu = trichter(RR)
        B[f"trichter_{name}"] = dict(t)
        print(f"\n== Trichter ({name}, {len(RR)} Läufe): " + " → ".join(f"{k} {v}" for k, v in t.items()))
        ohne_tor = [r for r in mit_wert if r not in offen]
        print(f"   Wert da, Tor nie offen ({len(ohne_tor)}): " + "; ".join(f"{x} {n}" for x, n in collections.Counter(r["art"] for r in ohne_tor).most_common()))
        tor_kein_zuck = [r for r in offen if r not in zuck]
        print(f"   Tor offen, aber kein Zucken ≥0,5 ({len(tor_kein_zuck)}): Kandidaten-Ende dort (up_max) Median "
              f"{np.median([max(s['up_max'] for s in r['aussagen'] if s['ok'] and s['zT_max'] > 0) for r in tor_kein_zuck]) if tor_kein_zuck else float('nan'):.2f}")
        kein = [r for r in RR if not any(s["ok"] for s in r["aussagen"])]
        fa = [r for r in kein if any(s["ok"] is False and s["S_max"] >= 0.5 for s in r["aussagen"])]
        print(f"   ohne richtigen Wert ({len(kein)}): Zucken ≥0,5 an falschem Wert in {len(fa)}")
    # 2b) Abschlüsse (08.11. ~07:35, nur Auswertung): war der tatsächliche Abschluss vom Reflex getragen oder natürlich?
    #     An der Stelle vor dem ersten </think>: p gezogen mit Reflex (x[5]) gegen ohne (x[7]).
    #     Reflex: ohne < 0,02 und mit ≥ 0,2 | natürlich: ohne ≥ 0,05 | sonst: unklar (Zufallsabschluss bei kleinem p)
    zus = []
    for r in R:
        if r["zu_tok"] is None:
            continue
        xc = [x for x in r["stellen"] if x[0] == r["zu_tok"] - 1 and x[7] is not None]
        if not xc:
            continue
        x = xc[0]
        art_zu = "Reflex" if (x[7] < 0.02 and x[5] >= 0.2) else "natürlich" if x[7] >= 0.05 else "unklar"
        A = [s for s in r["aussagen"] if s["t"] < r["zu_tok"]]
        letzte = max(A, key=lambda s: s["t"]) if A else None
        ort = ("am richtigen Wert" if letzte and letzte["ok"] and r["zu_tok"] - letzte["t"] <= 64 else
               "am falschen Wert" if letzte and letzte["ok"] is False and r["zu_tok"] - letzte["t"] <= 64 else "woanders")
        zus.append((art_zu, ort, r["korrekt"], x))
    if zus:
        print("\n== Tatsächliche Abschlüsse (erstes </think>): vom Reflex getragen oder natürlich?")
        B["abschluesse"] = {}
        for art_zu in ("Reflex", "natürlich", "unklar"):
            Z = [z for z in zus if z[0] == art_zu]
            orte = collections.Counter(z[1] for z in Z)
            B["abschluesse"][art_zu] = {"n": len(Z), **{k: v for k, v in orte.items()}, "richtig": sum(z[2] for z in Z)}
            print(f"   {art_zu:9s}: {len(Z):3d} | " + ", ".join(f"{k} {v}" for k, v in orte.most_common()) +
                  f" | richtig abgegeben {sum(z[2] for z in Z)}")
    # 3) Horizont: Wahrheits-Tor nach Position (richtige gegen falsche Aussagen)
    print("\n== Horizont – Wahrheits-Tor zT_max nach Position (Median; Anteil Tor offen):")
    B["horizont"] = {}
    for lo, hi in ((0, 1000), (1000, 2000), (2000, 4000), (4000, 8000), (8000, 16000), (16000, 40000)):
        Xr = [s for r in R for s in r["aussagen"] if s["ok"] and lo <= s["t"] < hi]
        Xf = [s for r in R for s in r["aussagen"] if s["ok"] is False and lo <= s["t"] < hi]
        if Xr or Xf:
            B["horizont"][f"{lo}-{hi}"] = {"richtig_n": len(Xr), "richtig_zT_median": float(np.median([s["zT_max"] for s in Xr])) if Xr else None,
                                         "richtig_offen": float(np.mean([s["zT_max"] > 0 for s in Xr])) if Xr else None,
                                         "falsch_n": len(Xf), "falsch_zT_median": float(np.median([s["zT_max"] for s in Xf])) if Xf else None,
                                         "falsch_offen": float(np.mean([s["zT_max"] > 0 for s in Xf])) if Xf else None}
            h = B["horizont"][f"{lo}-{hi}"]
            print(f"   {lo:5d}–{hi:5d}: richtig n {len(Xr):4d} zT {h['richtig_zT_median'] if h['richtig_zT_median'] is None else round(h['richtig_zT_median'], 2)} "
                  f"offen {anteil([s['zT_max'] > 0 for s in Xr])} | falsch n {len(Xf):5d} zT "
                  f"{h['falsch_zT_median'] if h['falsch_zT_median'] is None else round(h['falsch_zT_median'], 2)} offen {anteil([s['zT_max'] > 0 for s in Xf])}")
    # 4) Wirkung und Gegenschub (nur mit Ablation)
    st = [(r, x) for r in R for x in r["stellen"] if x[6] is not None]
    if st:
        neg = [x for _, x in st if x[1] <= -0.02]
        nat = [x for x in neg if x[7] >= 0.05]  # dort hätte das Modell ohne Reflex mit ≥ 5 % geschlossen
        B["gegenschub"] = {"stellen_S<=-0.02": len(neg), "davon_natuerliche_Abschlussstelle(ps_abl>=0.05)": len(nat),
                           "ps_mit_median_dort": float(np.median([x[5] for x in nat])) if nat else None,
                           "ps_ohne_median_dort": float(np.median([x[7] for x in nat])) if nat else None,
                           "verlust_summe(ohne-mit)": float(sum(max(0.0, x[7] - x[5]) for x in nat))}
        print(f"\n== Gegenschub („entmutigt?“): Stellen mit S ≤ −0,02: {len(neg)}; davon natürliche Abschluss-Stellen (ohne Reflex ≥ 5 %): "
              f"{len(nat)} | dort p gezogen mit Reflex Median {B['gegenschub']['ps_mit_median_dort']}, ohne {B['gegenschub']['ps_ohne_median_dort']} | "
              f"Summe verlorener Abschluss-Wahrscheinlichkeit {B['gegenschub']['verlust_summe(ohne-mit)']:.2f}")
        pos_ = [x for _, x in st if x[1] >= 0.5]
        print(f"   Zucken S ≥ 0,5: {len(pos_)} Stellen | p gezogen mit Reflex Median {np.median([x[5] for x in pos_]) if pos_ else float('nan'):.3f}, "
              f"ohne {np.median([x[7] for x in pos_]) if pos_ else float('nan'):.2e}")
    # 5) Schätzung MIT+WT (nur Quelle MIT mit Ablation): Zusatz-Abschluss durch den Reflex entlang MITs Läufen
    if a.quelle == "MIT" and st:
        L = json.load(open(os.path.join(ERG, "ausschluss_wta_s3_laeufe.json"), encoding="utf-8"))
        Mx = L["MIT"]
        g1 = [x for x in Mx.values() if x["zu_am_richtigen"]]
        # Reflex-Abschlüsse liegen direkt hinter der Aussage: falsche Fälle ≤ 8 Tokens danach, WT-A und MIT gepoolt
        gf = [x for M_ in (L["WT-A"], Mx) for x in M_.values() if x["zu_am_falschen"] and x["abstand_letzte_zu"] <= 8]
        pi_r = sum(x["korrekt"] for x in g1) / max(1, len(g1))
        pi_f = sum(x["korrekt"] for x in gf) / max(1, len(gf))
        print(f"\n== SCHÄTZUNG MIT+WT (keine Messung). Abgabe-Erfolg nach Abschluss am richtigen Wert π_r = {pi_r:.2f} "
              f"({sum(x['korrekt'] for x in g1)}/{len(g1)}, MIT), am falschen Wert π_f = {pi_f:.2f} ({sum(x['korrekt'] for x in gf)}/{len(gf)}, ≤ 8 Tokens, beide)")
        E_u, E_o, E_n = 0.0, 0.0, 0.0
        je = {}
        for r in R:
            A = sorted(r["aussagen"], key=lambda s: s["t"])
            c = r["zu_tok"]
            grenze = (c - 1) if c is not None else r["n_mess"]
            ueber, e = 1.0, 0.0
            for x in r["stellen"]:
                q, ps, ps_a = x[0], x[5], x[7]
                if q >= grenze or ps_a is None:
                    continue
                qz = max(0.0, (ps - ps_a) / max(1e-9, 1.0 - ps_a))
                if qz <= 1e-6:
                    continue
                letzte = [s for s in A if s["t"] <= q]
                pi = 0.0 if not letzte else (pi_r if letzte[-1]["ok"] else pi_f if letzte[-1]["ok"] is False else 0.0)
                e += ueber * qz * pi
                ueber *= (1.0 - qz)
            u = 0.0
            if c is not None and r["n_mess"] >= c:
                xc = [x for x in r["stellen"] if x[0] == c - 1]
                rr = 1.0 if not xc or not xc[0][7] else min(1.0, xc[0][5] / xc[0][7])
                e += ueber * rr * float(r["korrekt"])
                u = ueber * (1.0 - rr)
            else:
                e += ueber * float(r["korrekt"])
            je[r["id"]] = {"erwartet_richtig": e, "unklar": u, "p_frueh_zu": 1.0 - ueber, "mit": r["korrekt"], "wta": r["wta_korrekt"], "gruppe": r["gruppe"]}
            E_u += e
            E_o += e + u
            E_n += e + u * float(r["korrekt"])
        n = len(R)
        B["schaetzung_mit_wt"] = {"n": n, "unten": E_u, "oben": E_o, "neutral": E_n, "mit_tatsaechlich": sum(r["korrekt"] for r in R),
                                  "pi_r": pi_r, "pi_f": pi_f}
        print(f"   erwartet richtig: {E_n:.1f} von {n} (Spanne {E_u:.1f}–{E_o:.1f}; „unklar“ = Reflex hätte MITs eigenen Abschluss verhindert) | "
              f"MIT tatsächlich {B['schaetzung_mit_wt']['mit_tatsaechlich']}, WT-A tatsächlich {sum(r['wta_korrekt'] for r in R)}")
        for gname in ("nur MIT richtig", "nur WT-A richtig", "gleich"):
            X = [v for v in je.values() if v["gruppe"] == gname]
            if X:
                print(f"   {gname:16s}: n {len(X):3d} | erwartet richtig {sum(v['erwartet_richtig'] for v in X):5.1f} | MIT {sum(v['mit'] for v in X)} | "
                      f"WT-A {sum(v['wta'] for v in X)} | Reflex-Abschluss vor MITs eigenem (Summe p) {sum(v['p_frueh_zu'] for v in X):5.1f}")
        B["schaetzung_je_aufgabe"] = je
    # 5b) Stellschraube „mehr Mut“ (erkundend, 08.11. ~01:45): Wahrheits-Schwelle um δ (in z-Einheiten) gesenkt. Wo läge der ERSTE
    #     Zucker (S' = SiLU(zT_arg + δ)·up_arg/SiLU(3) ≥ 0,5) – an einem richtigen oder an einem falschen Wert? Nur bis zum ersten
    #     Zucker gültig, danach wäre der Lauf anders verlaufen.
    silu3 = 3.0 * float(sig(3.0))
    print("\n== Stellschraube Wahrheits-Schwelle (erkundend): erster Zucker S' ≥ 0,5 bei gesenkter Schwelle")
    B["stellschraube"] = {}
    # 08.11. ~07:45: auch STRENGERE Schwellen (δ < 0); für Quelle MIT dazu eine grobe Schätzung je δ (erster Zucker richtig → π_r,
    # falsch → π_f, kein Zucker → MITs eigenes Ergebnis; S' ≥ 0,5 bedeutet laut Messung p ≈ 1)
    for delta in (-3.0, -2.0, -1.0, -0.5, 0.0, 0.5, 1.0, 2.0, 3.0):
        k = collections.Counter()
        e_grob = 0.0
        for r in R:
            erst = None
            for s in sorted(r["aussagen"], key=lambda s: s["t"]):
                z = s["zT_arg"] + delta
                if z * float(sig(z)) * s["up_arg"] / silu3 >= 0.5:
                    erst = s
                    break
            k["kein Zucker" if erst is None else ("erster Zucker richtig" if erst["ok"] else "erster Zucker falsch" if erst["ok"] is False else "unbekannt")] += 1
            if erst is None or (r["zu_tok"] is not None and erst["t"] >= r["zu_tok"]):
                e_grob += float(r["korrekt"])
            else:
                e_grob += 0.89 if erst["ok"] else 0.16
        B["stellschraube"][str(delta)] = dict(k)
        B["stellschraube"][str(delta)]["grobe_schaetzung_richtig"] = e_grob
        print(f"   δ {delta:4.1f}: " + " | ".join(f"{n} {v}" for n, v in sorted(k.items())) +
              (f" | grobe Schätzung richtig {e_grob:.1f} (tatsächlich {sum(r['korrekt'] for r in R)})" if a.quelle == "MIT" else ""))
    # 5c) „Nachsicht“-Simulation (erkundend, 08.11. ~07:50; Nutzer-Idee: erst bei Bestätigung abgeben). Nur für Quelle MIT sinnvoll,
    #     weil MIT an Zuckern nicht schließt und sein Verlauf bis zum eigenen Abschluss gilt. Der Reflex feuert erst beim k-ten
    #     Zucker (S' ≥ 0,5) auf DENSELBEN Wert (Text-Gleichheit nach Bereinigung). Grobe Schätzung wie oben.
    if a.quelle == "MIT":
        print("\n== Nachsicht-Simulation (erkundend): Reflex erst beim k-ten Zucker auf denselben Wert")
        B["nachsicht_sim"] = {}

        def norm(w):
            return w.replace(" ", "").replace("$", "").replace("\\!", "").rstrip(".").lower()
        for delta in (-1.0, 0.0, 0.5):
            for k_n in (1, 2, 3, 5):
                kz = collections.Counter()
                e_grob = 0.0
                for r in R:
                    zaehl = collections.Counter()
                    feuer = None
                    for s in sorted(r["aussagen"], key=lambda s: s["t"]):
                        if r["zu_tok"] is not None and s["t"] >= r["zu_tok"]:
                            break
                        z = s["zT_arg"] + delta
                        if z * float(sig(z)) * s["up_arg"] / silu3 >= 0.5:
                            zaehl[norm(s["wert"])] += 1
                            if zaehl[norm(s["wert"])] >= k_n:
                                feuer = s
                                break
                    if feuer is None:
                        kz["kein Feuer"] += 1
                        e_grob += float(r["korrekt"])
                    else:
                        kz["Feuer richtig" if feuer["ok"] else "Feuer falsch"] += 1
                        e_grob += 0.89 if feuer["ok"] else 0.16
                B["nachsicht_sim"][f"d{delta}_k{k_n}"] = {**dict(kz), "grob": e_grob}
                print(f"   δ {delta:4.1f}, k {k_n}: " + " | ".join(f"{n} {v}" for n, v in sorted(kz.items())) +
                      f" | grobe Schätzung richtig {e_grob:.1f} (MIT tatsächlich {sum(r['korrekt'] for r in R)})")
    # 6) Einzelaufgaben der Gruppen
    for gname in ("nur MIT richtig", "nur WT-A richtig"):
        print(f"\n== {gname}:")
        for r in [r for r in R if r["gruppe"] == gname]:
            ok = [s for s in r["aussagen"] if s["ok"]]
            f = [s for s in r["aussagen"] if s["ok"] is False]
            print(f"   {r['id']:>36s} {r['art']:38s} | richtiger Wert zuerst {min((s['t'] for s in ok), default=None)} | S max richtig "
                  f"{max([s['S_max'] for s in ok], default=float('nan')):.2f} (Tor offen {sum(s['zT_max'] > 0 for s in ok)}/{len(ok)}, zT max "
                  f"{max([s['zT_max'] for s in ok], default=float('nan')):.1f}) | S max falsch {max([s['S_max'] for s in f], default=float('nan')):.2f} | "
                  f"Abschluss {r['zu_tok']}")
    zb = aus.replace(".jsonl", "_bewertung.json")
    json.dump(B, open(zb, "w", encoding="utf-8"), indent=1, ensure_ascii=False, default=str)
    print(f"\ngespeichert: {zb}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quelle", choices=list(QUELLEN), default="WT-A")
    ap.add_argument("--modell", default="Qwen3.5-0.8B-ergo-zigA")
    ap.add_argument("--geraet", default="cpu")
    ap.add_argument("--dtype", choices=["f32", "bf16"], default="f32")
    ap.add_argument("--ablation", action="store_true")
    ap.add_argument("--max-tokens", type=int, default=32768)
    ap.add_argument("--nur", type=int, default=0)
    ap.add_argument("--ids", default="")
    ap.add_argument("--aus", default="")
    ap.add_argument("--auswerten", action="store_true")
    a = ap.parse_args()
    if a.auswerten:
        auswerten(a)
    else:
        messen(a)


if __name__ == "__main__":
    main()
