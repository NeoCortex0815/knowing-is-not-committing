"""Stufe 0, eigene Diagnose: Loop-Richtung aus Teacher-Forcing auf den Basis-Transkripten finden.

  python 04_richtung.py --modell MODELLE/Qwen3.5-0.8B --ergebnisse ergebnisse/basis/ergebnisse.jsonl \
      --mit ergebnisse/mit_richtung.npz --aus ergebnisse/eigene_richtung.npz

Vorgehen (Kontrast im Residual Stream, wie der MIT-Lauf p50c es beschreibt):
  1. Token-Positionen labeln: "repetitiv" = das nächste Token setzt ein schon gesehenes 8-Gramm fort und
     liegt in einer Wiederholungsstrecke (>= --min-lauf Tokens); "produktiv" = neues 8-Gramm, vor
     Beginn der ersten Schleife.
  2. Ein Forward-Pass je Transkript (CPU, ohne Gradienten); Hooks sammeln den Residual Stream am Ausgang
     jeder Schicht und die MLP-Neuron-Aktivierungen (Eingang von down_proj) in den Edit-Schichten.
  3. u_L = normierte Mittelwert-Differenz (repetitiv - produktiv) je Schicht, Trennschärfe d' entlang u_L.
  4. Neuron-Score je Spalte j: (a_rep_j - a_prod_j) * (u_L . W_down[:, j]) -> Top-k "Schreiber"-Neuronen.
  5. Abgleich mit der MIT-Richtung (Kosinus) und den MIT-Spalten (Überschneidung).
Keine Gewichtsänderung, keine Backpropagation.
"""
import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wsp_lib as W  # noqa: E402


def labels(gen, min_lauf):
    """rep[t]: Token t beendet ein 8-Gramm, das vorher schon vorkam."""
    n = len(gen)
    rep = np.zeros(n, dtype=bool)
    gesehen = set()
    for t in range(7, n):
        g = tuple(gen[t - 7:t + 1])
        rep[t] = g in gesehen
        gesehen.add(g)
    # Wiederholungsstrecken >= min_lauf
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


def lade_modell(pfad, dtype):
    import torch
    import transformers as tf
    dt = {"bf16": torch.bfloat16, "f32": torch.float32}[dtype]
    for cls in ("AutoModelForImageTextToText", "AutoModelForCausalLM"):
        try:
            m = getattr(tf, cls).from_pretrained(pfad, dtype=dt)
            break
        except Exception as e:  # noqa: BLE001
            print(f"{cls}: {e}")
    else:
        raise SystemExit("Modell ließ sich nicht laden")
    m.eval()
    kand = [(n, mod) for n, mod in m.named_modules()
            if n.endswith("layers") and isinstance(mod, torch.nn.ModuleList)]
    kand.sort(key=lambda x: ("language_model" not in x[0], -len(x[1])))
    return m, kand[0][0], kand[0][1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--modell", required=True)
    ap.add_argument("--ergebnisse", required=True, help="ergebnisse.jsonl des Basis-Modells (03_eval.py)")
    ap.add_argument("--edit-schichten", default="15,19")
    ap.add_argument("--schichten", default="alle", help="Schichten für die Richtungs-Analyse")
    ap.add_argument("--max-len", type=int, default=8192, help="max. Antwort-Tokens je Transkript")
    ap.add_argument("--pos-je-text", type=int, default=400, help="max. Positionen je Klasse und Transkript")
    ap.add_argument("--min-lauf", type=int, default=32)
    ap.add_argument("--max-texte", type=int, default=64)
    ap.add_argument("--top-k", type=int, default=64)
    ap.add_argument("--dtype", default="bf16", choices=["bf16", "f32"])
    ap.add_argument("--threads", type=int, default=0)
    ap.add_argument("--mit", help="mit_richtung.npz aus 01_mit_edit.py (Abgleich)")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--aus", required=True)
    a = ap.parse_args()

    import torch
    if a.threads:
        torch.set_num_threads(a.threads)
    rng = np.random.default_rng(a.seed)
    model, lpfad, layers = lade_modell(a.modell, a.dtype)
    nL = len(layers)
    schichten = list(range(nL)) if a.schichten == "alle" else [int(x) for x in a.schichten.split(",")]
    edit = [int(x) for x in a.edit_schichten.split(",")]
    print(f"Decoder-Schichten: {lpfad} ({nL}); Analyse {schichten}; Edit {edit}")

    texte = [json.loads(z) for z in open(a.ergebnisse, encoding="utf-8")]
    d = None
    acc = {}          # L -> dict(sum_r, sum_p, sq_r, sq_p, n_r, n_p)
    nacc = {}         # L -> dict(a_r, a_p, n_r, n_p)
    stat = {"texte": 0, "pos_rep": 0, "pos_prod": 0}
    aktuell = {}

    def h_out(L):
        def f(mod, inp, out):
            x = out[0] if isinstance(out, tuple) else out
            aktuell[("h", L)] = x[0].float()
        return f

    def h_down(L):
        def f(mod, inp):
            aktuell[("a", L)] = inp[0][0].float()
        return f

    hooks = [layers[L].register_forward_hook(h_out(L)) for L in schichten]
    hooks += [layers[L].mlp.down_proj.register_forward_pre_hook(h_down(L)) for L in edit]

    for r in texte[:a.max_texte]:
        gen = r["gen_ids"][:a.max_len]
        rep, lauf, onset = labels(gen, a.min_lauf)
        P = len(r["prompt_ids"])
        # Position t (Eingabe-Token t) sagt Token t+1 voraus -> Label von t+1
        rep_pos = [t for t in range(len(gen) - 1) if lauf[t + 1]]
        prod_pos = [t for t in range(7, min(onset, len(gen)) - 1) if not rep[t + 1]]
        if not rep_pos and not prod_pos:
            continue
        if len(rep_pos) > a.pos_je_text:
            rep_pos = sorted(rng.choice(rep_pos, a.pos_je_text, replace=False).tolist())
        if len(prod_pos) > a.pos_je_text:
            prod_pos = sorted(rng.choice(prod_pos, a.pos_je_text, replace=False).tolist())
        ids = torch.tensor([r["prompt_ids"] + gen])
        with torch.no_grad():
            model(input_ids=ids, use_cache=False)
        ir = torch.tensor([P + t for t in rep_pos], dtype=torch.long)
        ip = torch.tensor([P + t for t in prod_pos], dtype=torch.long)
        for L in schichten:
            x = aktuell.pop(("h", L))
            d = x.shape[1]
            s = acc.setdefault(L, {"sr": np.zeros(d), "sp": np.zeros(d), "qr": np.zeros((d, d)),
                                   "qp": np.zeros((d, d)), "nr": 0, "np": 0})
            if len(ir):
                xr = x[ir].double().numpy()
                s["sr"] += xr.sum(0); s["qr"] += xr.T @ xr; s["nr"] += len(ir)
            if len(ip):
                xp = x[ip].double().numpy()
                s["sp"] += xp.sum(0); s["qp"] += xp.T @ xp; s["np"] += len(ip)
        for L in edit:
            av = aktuell.pop(("a", L))
            s = nacc.setdefault(L, {"ar": np.zeros(av.shape[1]), "ap": np.zeros(av.shape[1]), "nr": 0, "np": 0})
            if len(ir):
                s["ar"] += av[ir].double().numpy().sum(0); s["nr"] += len(ir)
            if len(ip):
                s["ap"] += av[ip].double().numpy().sum(0); s["np"] += len(ip)
        aktuell.clear()
        stat["texte"] += 1; stat["pos_rep"] += len(ir); stat["pos_prod"] += len(ip)
        print(f"{r['id']}: {len(gen)} Tok, Schleife ab {onset if onset < len(gen) else '-'}, "
              f"rep {len(ir)} / prod {len(ip)}", flush=True)
    for h in hooks:
        h.remove()
    if not acc or min(s["nr"] for s in acc.values()) == 0 or min(s["np"] for s in acc.values()) == 0:
        raise SystemExit("Zu wenig Positionen in einer der Klassen (braucht Schleifen UND produktive Abschnitte)")

    mit = dict(np.load(a.mit)) if a.mit else {}
    out, bericht = {}, {"statistik": stat, "schichten": {}}
    for L in schichten:
        s = acc[L]
        mr, mp = s["sr"] / s["nr"], s["sp"] / s["np"]
        Cr = s["qr"] / s["nr"] - np.outer(mr, mr)
        Cp = s["qp"] / s["np"] - np.outer(mp, mp)
        diff = mr - mp
        u = diff / np.linalg.norm(diff)
        dprime = float((diff @ u) / np.sqrt(0.5 * (u @ Cr @ u + u @ Cp @ u)))
        out[f"u_{L}"] = u.astype(np.float32)
        b = {"d_prime": round(dprime, 3), "abstand": round(float(np.linalg.norm(diff)), 3)}
        for k in [k for k in mit if k.startswith("u_")]:
            b[f"cos_mit_{k[2:]}"] = round(float(abs(u @ mit[k])), 3)
        bericht["schichten"][L] = b

    index = W.tensor_index(a.modell)
    name_by_L = {}
    for n in index:
        if n.endswith("mlp.down_proj.weight") and W.schicht_aus_name(n) in edit and "visual" not in n:
            name_by_L[W.schicht_aus_name(n)] = n
    for L in edit:
        Wd = W.tensor_f32(a.modell, name_by_L[L], index).astype(np.float64)
        u = out[f"u_{L}"].astype(np.float64)
        s = nacc[L]
        da = s["ar"] / s["nr"] - s["ap"] / s["np"]
        schreib = u @ Wd
        score = da * schreib
        top = np.argsort(-score)[:a.top_k]
        out[f"spalten_{L}"] = np.sort(top)
        out[f"score_{L}"] = score.astype(np.float32)
        b = bericht["schichten"][L]
        b["tensor"] = name_by_L[L]
        b["top_k"] = a.top_k
        if f"spalten_{L}" in mit:
            ref = set(mit[f"spalten_{L}"].tolist())
            b["ueberschneidung_mit_spalten"] = len(ref & set(top.tolist()))
            if f"u_{L}" in mit:
                sm = da * (mit[f"u_{L}"].astype(np.float64) @ Wd)
                b["ueberschneidung_bei_mit_u"] = len(ref & set(np.argsort(-sm)[:a.top_k].tolist()))

    os.makedirs(os.path.dirname(os.path.abspath(a.aus)), exist_ok=True)
    np.savez(a.aus, **out)
    rang = sorted(bericht["schichten"].items(), key=lambda kv: -kv[1]["d_prime"])
    bericht["staerkste_schichten"] = [L for L, _ in rang[:6]]
    json.dump(bericht, open(os.path.splitext(a.aus)[0] + ".json", "w"), indent=1)
    print(json.dumps(bericht, indent=1))


if __name__ == "__main__":
    main()
