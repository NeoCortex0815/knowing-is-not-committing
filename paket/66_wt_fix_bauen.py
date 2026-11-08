"""WT-Fix gegen das Prompt-Leck (07.11. ~14:00, Nutzer-Go „Fix vorbereiten“; nur Bau, kein Lauf).
Befund (65_wt_leck_diagnose.py): Am letzten Prompt-Token ist das V2.1-Gate „halb zu“ (Vor-Aktivierung ≈ −0,55 → SiLU ≈ −0,2,
negativer Ast) und up ≈ −1,8 (Kandidaten-Ende-Melder negativ) → Produkt ≈ +0,37 je Neuron → Schub ≈ +0,9 entlang ĝ an der
empfindlichsten Stelle (p(`</think>`) dort ohnehin ~10⁻³) → p ≈ 0,7. Zwei Bauarten:
  A (minimal, V2.1-Bedeutung): gate = Wahrheit über τ_T (wie V2.1); Nullpunkt von up an den MEDIAN gewöhnlicher Denk-Tokens statt
    an das 5-%-Quantil der Kandidaten-Enden → up ist abseits von Kandidaten ≈ 0 oder positiv → Produkt mit dem negativen
    SiLU-Ast ≤ 0 (Schub weg vom Abschluss, winzig).
  B (dreiwertig, Nutzer-Idee „WAHR → abgeben, FALSCH → weiterdenken“): gate = Kandidaten-Ende (an Nicht-Kandidaten tief negativ →
    SiLU ≈ 0), up = Wahrheit um τ_T mit Vorzeichen → am richtigen Kandidaten Schub zum Abschluss, am falschen Schub weg davon.
Gleiche 16 Neuronen, gleiches ĝ, gleiche Gesamtstärke κ wie V2.1; Basis = Grundmodell + eigen-Umkehr (bitgleich geprüft).
  python 66_wt_fix_bauen.py --bauart A --aus modelle/Qwen3.5-0.8B-ergo-zigA
"""
import argparse
import os
import sys

import numpy as np

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(HIER)
ERG = os.path.join(WURZEL, "ergebnisse")
sys.path.insert(0, HIER)
import wsp_lib as W  # noqa: E402

L = 15


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bauart", choices=["A", "B"], required=True)
    ap.add_argument("--aus", required=True)
    ap.add_argument("--basis", default=os.path.join(WURZEL, "modelle", "Qwen3.5-0.8B"))
    ap.add_argument("--vergleich", default=os.path.join(WURZEL, "modelle", "Qwen3.5-0.8B-eigen-vL"))
    ap.add_argument("--lern", default=os.path.join(ERG, "gatter_lern.npz"))
    ap.add_argument("--gradient", default=os.path.join(ERG, "abschluss_gradient.npz"))
    ap.add_argument("--richtung", default=os.path.join(ERG, "eigene_richtung-vL.npz"))
    ap.add_argument("--alpha", type=float, default=6.0)
    ap.add_argument("--kappa", type=float, default=7.0)
    ap.add_argument("--z-ziel", type=float, default=3.0)
    ap.add_argument("--fehl-falsch", type=float, default=0.02)
    a = ap.parse_args()
    Lz = np.load(a.lern)
    wT, bT, wC, bC, v = Lz["wT"], float(Lz["bT"]), Lz["wC"], float(Lz["bC"]), Lz["v"]
    G = Lz["G"].astype(np.int64)
    oof_T, yk, sC_k, sC_n = Lz["oof_T"], Lz["yk"].astype(bool), Lz["sC_k"], Lz["sC_n"]
    tau_T = float(np.quantile(oof_T[~yk], 1 - a.fehl_falsch))
    silu = a.z_ziel / (1 + np.exp(-a.z_ziel))
    kappa_d = a.kappa / (len(G) * silu)
    g = np.load(a.gradient)["g_15"].astype(np.float64)
    g /= np.linalg.norm(g)
    if a.bauart == "A":
        ueber = oof_T[yk & (oof_T > tau_T)]
        kappa_g = a.z_ziel / (float(np.median(ueber)) - tau_T)
        tau_C = float(np.median(sC_n))
        kappa_u = 1.0 / (float(np.median(sC_k)) - tau_C)
        zeile_gate = kappa_g * (wT + (bT - tau_T) * v)
        zeile_up = kappa_u * (wC + (bC - tau_C) * v)
        info = f"A: gate = Wahrheit über τ_T {tau_T:.3f}; up-Nullpunkt = Median gewöhnlicher Tokens τ_C {tau_C:.3f}"
    else:
        tau_C = float(np.quantile(sC_k, 0.05))
        kappa_g = a.z_ziel / (float(np.median(sC_k)) - tau_C)
        kappa_u = 1.0 / (float(np.median(oof_T[yk])) - tau_T)
        zeile_gate = kappa_g * (wC + (bC - tau_C) * v)
        zeile_up = kappa_u * (wT + (bT - tau_T) * v)
        info = f"B: gate = Kandidaten-Ende (τ_C {tau_C:.3f}); up = Wahrheit um τ_T {tau_T:.3f} (mit Vorzeichen)"
    print(info + f" | κ_g {kappa_g:.3f}, κ_u {kappa_u:.3f}, κ_d {kappa_d:.4f}", flush=True)
    R = dict(np.load(a.richtung))
    patches, pruef = {}, {}
    for Ls in (15, 19):
        name = f"model.language_model.layers.{Ls}.mlp.down_proj.weight"
        W0 = np.asarray(W.bf16_to_f32(np.asarray(W.tensor_lesen(a.basis, name)[1])), dtype=np.float64)
        u_l = R[f"u_{Ls}"].astype(np.float64)
        u_l /= np.linalg.norm(u_l)
        W1 = np.asarray(W.rang1_edit(W0, u_l, np.asarray(R[f"spalten_{Ls}"], dtype=np.int64), a.alpha), dtype=np.float64)
        ref = W.tensor_lesen(a.vergleich, name)[1]
        pruef[f"umkehr_{Ls}_bitgleich"] = round(float(np.mean(np.asarray(ref) == W.bf16_bits(W1))), 6)
        if Ls == L:
            assert not (set(G.tolist()) & set(int(s) for s in R[f"spalten_{L}"]))
            W1 = W1.copy()
            W1[:, G] = (kappa_d * g)[:, None]
        patches[name] = W.bf16_bits(W1)
    for k, zeile in (("gate", zeile_gate), ("up", zeile_up)):
        name = f"model.language_model.layers.{L}.mlp.{k}_proj.weight"
        T = np.asarray(W.bf16_to_f32(np.asarray(W.tensor_lesen(a.basis, name)[1])), dtype=np.float64).copy()
        T[G, :] = zeile[None, :]
        patches[name] = W.bf16_bits(T)
    print(f"Umkehr bitgleich mit eigen: {pruef}", flush=True)
    meta = {"art": f"WT-Fix Bauart {a.bauart} gegen Prompt-Leck: {info}", "neuronen": G.tolist(), "tau_T": tau_T, "tau_C": tau_C,
            "kappa_g": kappa_g, "kappa_u": kappa_u, "kappa_d": kappa_d, "kappa": a.kappa, "z_ziel": a.z_ziel,
            "fehl_falsch": a.fehl_falsch, "pruefungen": pruef}
    W.modell_mit_patch(a.basis, a.aus, patches, meta)
    print(f"Modell: {a.aus}")


if __name__ == "__main__":
    main()
