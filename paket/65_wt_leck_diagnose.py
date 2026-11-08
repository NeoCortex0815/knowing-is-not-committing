"""Diagnose des WT-Lecks (07.11. ~13:50, Nutzer-Go „Fix vorbereiten“; CPU, nur Übungs-Prompts + Set-B-Prompts zum Gegencheck).
Die WT-Detektoren (gatter_lern.npz) wurden nur an Denk-Tokens gelernt (Kandidaten-Enden gegen gewöhnliche Tokens), der Bias-Ersatz v
(vᵀx ≈ 1) nur an gewöhnlichen Denk-Tokens. Prüft an Prompt-Tokens (Schicht-15-MLP-Eingang, eigen-vL = Basis bis Schicht 15):
vᵀx, s_T = wTᵀx + bT, s_C = wCᵀx + bC und die Gatter-Größen wie in bauen_zig (gate = κ_g(wT + (bT − τ_T)v)ᵀx, up = κ_u(wC + (bC − τ_C)v)ᵀx),
getrennt nach Vorlagen-Ende (letzte 8 Tokens) und übrigem Prompt; Vergleich mit gewöhnlichen Denk-Tokens und Kandidaten-Enden.
Speichert die Prompt-Vektoren für den Neu-Lern-Schritt (ergebnisse/wt_prompt_sammlung.npz).
  python 65_wt_leck_diagnose.py --uebung 120 --setb 30
"""
import argparse
import json
import os
import re

import numpy as np

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(HIER)
ERG = os.path.join(WURZEL, "ergebnisse")


class Stopp(Exception):
    pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--uebung", type=int, default=120, help="Anzahl Übungs-Prompts (zum Lernen)")
    ap.add_argument("--setb", type=int, default=30, help="Anzahl Set-B-Prompts (nur Gegencheck, nicht zum Lernen)")
    ap.add_argument("--uebungs-laeufe", nargs="+", default=[os.path.join(ERG, d, "ergebnisse.jsonl") for d in
                                                            ("tag1-eigen-s1", "entschluss-uebung-eigen", "temp10-eigen")])
    a = ap.parse_args()
    import torch
    import transformers as tf
    torch.set_num_threads(int(os.environ.get("WSP_THREADS", 4)))
    Lz = np.load(os.path.join(ERG, "gatter_lern.npz"))
    mz = json.load(open(os.path.join(WURZEL, "modelle", "Qwen3.5-0.8B-ergo-zig", "wsp_patch.json"), encoding="utf-8"))
    wT, bT, wC, bC, v = Lz["wT"], float(Lz["bT"]), Lz["wC"], float(Lz["bC"]), Lz["v"]
    tauT, tauC, kg, ku = mz["tau_T"], mz["tau_C"], mz["kappa_g"], mz["kappa_u"]
    cls = getattr(tf, "AutoModelForImageTextToText", None) or tf.AutoModelForCausalLM
    model = cls.from_pretrained(os.path.join(WURZEL, "modelle", "Qwen3.5-0.8B-eigen-vL"), dtype=torch.float32).eval()
    sp = {}
    for n, m in model.named_modules():
        if "visual" in n:
            continue
        if re.search(r"(language_model|model)\.layers\.15\.mlp$", n):
            m.register_forward_pre_hook(lambda mod, inp: sp.__setitem__("x", inp[0][0].detach().float().numpy()))
        if re.search(r"(language_model|model)\.layers\.15\.mlp\.down_proj$", n):
            def stopp(mod, inp):
                raise Stopp()
            m.register_forward_pre_hook(stopp)

    def prompts(pfade, n):
        out, gesehen = [], set()
        for p in pfade:
            if not os.path.exists(p):
                continue
            for z in open(p, encoding="utf-8"):
                r = json.loads(z)
                if r["id"] in gesehen:
                    continue
                gesehen.add(r["id"])
                out.append(r["prompt_ids"])
                if len(out) >= n:
                    return out
        return out
    sammel = {}
    for name, liste in (("uebung", prompts(a.uebungs_laeufe, a.uebung)),
                        ("setb", prompts([os.path.join(ERG, "setB-ergore-t06", "ergebnisse.jsonl")], a.setb))):
        Xe, Xr = [], []
        for ids in liste:
            sp.clear()
            try:
                with torch.no_grad():
                    model(input_ids=torch.tensor([ids]))
            except Stopp:
                pass
            X = sp["x"]
            Xe.append(X[-8:])
            Xr.append(X[:-8])
        sammel[name] = (np.vstack(Xe), np.vstack(Xr), len(liste))
    Z = np.load(os.path.join(ERG, "gatter_sammlung.npz"))
    vergleich = {"Denk-Tokens (gewöhnlich)": Z["Xn"][:5000].astype(np.float64),
                 "Kandidaten-Enden richtig": Z["Xk"][Z["yk"].astype(bool)][:2000].astype(np.float64),
                 "Kandidaten-Enden falsch": Z["Xk"][~Z["yk"].astype(bool)][:2000].astype(np.float64)}
    silu = lambda z: z / (1 + np.exp(-np.clip(z, -60, 60)))  # noqa: E731

    def zeile(name, X):
        X = np.asarray(X, dtype=np.float64)
        vx = X @ v
        sT, sC = X @ wT + bT, X @ wC + bC
        g = kg * (X @ wT + (bT - tauT) * vx)
        u = ku * (X @ wC + (bC - tauC) * vx)
        p = silu(g) * u
        print(f"{name:34s} n={len(X):6d} | vᵀx Median {np.median(vx):+6.2f} | s_T {np.median(sT):+6.2f} | s_C {np.median(sC):+6.2f} | "
              f"gate {np.median(g):+6.2f} | up {np.median(u):+6.2f} | Produkt Median {np.median(p):+6.2f}, 95 % {np.quantile(p, .95):+6.2f}, "
              f"Anteil > 1: {100 * float((p > 1).mean()):5.1f} %", flush=True)
    for name, X in vergleich.items():
        zeile(name, X)
    for name, (Xe, Xr, n) in sammel.items():
        zeile(f"{name}: Vorlagen-Ende (letzte 8)", Xe)
        zeile(f"{name}: übriger Prompt", Xr)
    np.savez_compressed(os.path.join(ERG, "wt_prompt_sammlung.npz"), Xe_uebung=sammel["uebung"][0].astype(np.float32),
                        Xr_uebung=sammel["uebung"][1].astype(np.float32), Xe_setb=sammel["setb"][0].astype(np.float32),
                        Xr_setb=sammel["setb"][1].astype(np.float32))
    print("gespeichert: ergebnisse/wt_prompt_sammlung.npz")


if __name__ == "__main__":
    main()
