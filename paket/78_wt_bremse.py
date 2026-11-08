"""WT-B = WT-A + Reparatur gegen das zweite `</think>` (07.11. abends; Nutzer-Go „Ja, so machen“). Nur Bau und Offline-Messung,
kein Lauf. Daten: ergebnisse/phase_sammlung.npz (77_phase_sammeln.py; Schicht-15-MLP-Eingang, Denken gegen Antwortteil).
Phasen-Sonde s_P (logistisch, 5-fach nach Lauf gruppiert) trennt „vor dem ersten `</think>`“ von „danach“.
Zwei Bauarten:
  a  WT-Gate dämpfen: Die 16 WT-Neuronen bekommen −κ_P·(s_P − c) ins Gate (c = Median im Denken). Im Antwortteil wird das Gate
     tief negativ (SiLU ≈ 0, WT stumm); im Denken verschiebt es sich nur um ±κ_P·σ. Nur machbar, wenn die Trennung sehr groß
     gegenüber der Streuung im Denken ist.
  b  Antwort-Bremse: 8 weitere ruhige Neuronen; Gate = κ_B·(s_P − τ_P) (im Denken ≤ −6 → SiLU ≈ 0), up ≈ 1 (Bias-Ersatz v),
     down = −κ_b·ĝ → schiebt im Antwortteil weg vom Abschluss.
  python 78_wt_bremse.py --analyse
  python 78_wt_bremse.py --bauen a --aus modelle/Qwen3.5-0.8B-ergo-zigB2      (bzw. --bauen b)
"""
import argparse
import importlib.util
import os
import sys

import numpy as np

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(HIER)
ERG = os.path.join(WURZEL, "ergebnisse")
sys.path.insert(0, HIER)
import wsp_lib as W  # noqa: E402

L = 15
ZIGA = os.path.join(WURZEL, "modelle", "Qwen3.5-0.8B-ergo-zigA")


def lade_mod(name, pfad):
    s = importlib.util.spec_from_file_location(name, pfad)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


def silu(z):
    return z / (1 + np.exp(-np.clip(z, -60, 60)))


def phasen_sonde(Z, wm, lam=50.0):
    X, y, lauf = Z["X"].astype(np.float64), Z["phase"].astype(bool), Z["lauf"].astype(str)
    eind = sorted(set(lauf))
    rng = np.random.default_rng(0)
    rng.shuffle(eind)
    falte = {t: i % 5 for i, t in enumerate(eind)}
    f = np.array([falte[t] for t in lauf])
    oof = np.zeros(len(y))
    for k in range(5):
        tr, te = f != k, f == k
        mu, sd = X[tr].mean(0), X[tr].std(0) + 1e-6
        w, b = wm.logreg((X[tr] - mu) / sd, y[tr].astype(float), lam)
        oof[te] = ((X[te] - mu) / sd) @ w + b
    mu, sd = X.mean(0), X.std(0) + 1e-6
    w, b = wm.logreg((X - mu) / sd, y.astype(float), lam)
    return oof, w / sd, b - float((w * mu / sd).sum())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--analyse", action="store_true")
    ap.add_argument("--bauen", choices=["a", "b"])
    ap.add_argument("--aus")
    ap.add_argument("--kappa-p", type=float, default=None, help="Bauart a: Stärke; Standard aus der Analyse")
    ap.add_argument("--kappa-b", type=float, default=7.0, help="Bauart b: Gesamtschub entlang −ĝ am Median-Antwort-Token")
    a = ap.parse_args()
    wm = lade_mod("wm", os.path.join(HIER, "42_wahrheitsmelder.py"))
    Z = np.load(os.path.join(ERG, "phase_sammlung.npz"))
    art = Z["art"].astype(str)
    oof, wP, bP = phasen_sonde(Z, wm)
    sP = Z["X"].astype(np.float64) @ wP + bP                       # endgültige Sonde (auf allen Daten)
    y = Z["phase"].astype(bool)
    print(f"Phasen-Sonde: AUC zurückgehalten {wm.auc(oof, y):.4f} ({(~y).sum()} Denken, {y.sum()} Antwort)")
    for k in ("denken", "spaet", "antwort", "vor_zweitem"):
        m = art == k
        if m.any():
            q = np.percentile(oof[m], [0.1, 1, 10, 50, 90, 99, 99.9])
            print(f"  {k:12s} n {m.sum():5d} | zurückgehalten s_P Quantile 0,1/1/10/50/90/99/99,9 %: {np.round(q, 1).tolist()}")
    den = np.isin(art, ["denken", "spaet"])
    ant = np.isin(art, ["antwort", "vor_zweitem"])
    c = float(np.median(oof[den]))
    sig = float(np.subtract(*np.percentile(oof[den], [75, 25])) / 1.349)
    lo_ant = float(np.percentile(oof[ant], 5))
    hi_den = float(np.percentile(oof[den], 99.9))
    print(f"Denken: Median {c:.2f}, robuste Streuung {sig:.2f}, 99,9 % {hi_den:.2f} | Antwort: 5 % {lo_ant:.2f}")
    Lz = np.load(os.path.join(ERG, "gatter_lern.npz"))
    v = Lz["v"]
    vx = Z["X"].astype(np.float64) @ v
    print(f"Bias-Ersatz vᵀx: Denken Median {np.median(vx[den]):.3f} (1–99 %: {np.percentile(vx[den], 1):.3f}–{np.percentile(vx[den], 99):.3f}), "
          f"Antwort Median {np.median(vx[ant]):.3f} (1–99 %: {np.percentile(vx[ant], 1):.3f}–{np.percentile(vx[ant], 99):.3f})")
    # WT-A-Gate auf diesen Stellen
    import json
    meta = json.load(open(os.path.join(ZIGA, "wsp_patch.json"), encoding="utf-8"))
    X = Z["X"].astype(np.float64)
    gWT = meta["kappa_g"] * (X @ Lz["wT"] + (float(Lz["bT"]) - meta["tau_T"]) * vx)
    uWT = meta["kappa_u"] * (X @ Lz["wC"] + (float(Lz["bC"]) - meta["tau_C"]) * vx)
    schub = meta["kappa"] / silu(meta["z_ziel"]) * silu(gWT) * uWT
    for k in ("denken", "spaet", "antwort", "vor_zweitem"):
        m = art == k
        print(f"  WT-A-Schub entlang ĝ {k:12s}: Median {np.median(schub[m]):+.3f}, 90 % {np.percentile(schub[m], 90):+.3f}, "
              f"Max {schub[m].max():+.2f} | Gate offen {100 * float((gWT[m] > 0).mean()):.1f} %")
    # Bauart a: κ_P so, dass das Antwort-5-%-Quantil das WT-Gate um ≥ 12 senkt
    kP = a.kappa_p or 12.0 / max(lo_ant - c, 1e-6)
    print(f"Bauart a: κ_P {kP:.3f} → Verschiebung im Denken ±{kP * sig:.2f} (robust 1σ), an „spät“ Median "
          f"{-kP * (np.median(oof[art == 'spaet']) - c):+.2f}; im Antwortteil 5 %: {-kP * (lo_ant - c):+.1f}")
    # Bauart b
    kB = 10.0 / max(float(np.median(oof[ant])) - hi_den, 1e-6)
    tauP = hi_den + 6.0 / kB
    gB = kB * (oof - tauP)
    print(f"Bauart b: κ_B {kB:.3f}, τ_P {tauP:.2f} → Gate Denken 99,9 % {np.percentile(gB[den], 99.9):+.1f}, Antwort Median "
          f"{np.median(gB[ant]):+.1f}, Antwort 99 % {np.percentile(gB[ant], 99):+.1f}")
    if a.analyse or not a.bauen:
        return
    # ---------------- Bau
    gdir = np.load(os.path.join(ERG, "abschluss_gradient.npz"))["g_15"].astype(np.float64)
    gdir /= np.linalg.norm(gdir)
    G = Lz["G"].astype(np.int64)
    patches, info = {}, {}
    if a.bauen == "a":
        name = f"model.language_model.layers.{L}.mlp.gate_proj.weight"
        T = np.asarray(W.bf16_to_f32(np.asarray(W.tensor_lesen(ZIGA, name)[1])), dtype=np.float64).copy()
        T[G, :] = T[G, :] - kP * (wP + (bP - c) * v)[None, :]
        patches[name] = W.bf16_bits(T)
        info = {"art": "WT-B Bauart a (WT-Gate im Antwortteil gedämpft)", "kappa_P": kP, "c": c, "sigma": sig}
    else:
        R = dict(np.load(os.path.join(ERG, "eigene_richtung-vL.npz")))
        S = set(int(s) for s in R[f"spalten_{L}"])
        rms = np.load(os.path.join(ERG, "gatter_sammlung.npz"))["neuron_rms"]
        B = np.array([j for j in np.argsort(rms) if int(j) not in S and int(j) not in set(G.tolist())][:8], dtype=np.int64)
        g_med = float(np.median(gB[ant]))
        kdb = a.kappa_b / (len(B) * silu(g_med))
        for k, zeile in (("gate", kB * (wP + (bP - tauP) * v)), ("up", v)):
            name = f"model.language_model.layers.{L}.mlp.{k}_proj.weight"
            T = np.asarray(W.bf16_to_f32(np.asarray(W.tensor_lesen(ZIGA, name)[1])), dtype=np.float64).copy()
            T[B, :] = zeile[None, :]
            patches[name] = W.bf16_bits(T)
        name = f"model.language_model.layers.{L}.mlp.down_proj.weight"
        T = np.asarray(W.bf16_to_f32(np.asarray(W.tensor_lesen(ZIGA, name)[1])), dtype=np.float64).copy()
        T[:, B] = (-kdb * gdir)[:, None]
        patches[name] = W.bf16_bits(T)
        info = {"art": "WT-B Bauart b (Antwort-Bremse)", "neuronen_bremse": B.tolist(), "kappa_B": kB, "tau_P": tauP,
                "kappa_b": a.kappa_b, "kappa_db": kdb, "rms_bremse": [float(rms[j]) for j in B]}
        print(f"Bremse: Neuronen {B.tolist()} (RMS {rms[B].min():.2e}–{rms[B].max():.2e}), κ_db {kdb:.4f}")
    info.update({"basis_wta": ZIGA, "phase_auc_cv": float(wm.auc(oof, y))})
    W.modell_mit_patch(ZIGA, a.aus, patches, info)
    np.savez(os.path.join(ERG, "phase_sonde.npz"), wP=wP, bP=bP, c=c, sig=sig, tauP=tauP, kB=kB, kP=kP)
    print(f"Modell: {a.aus}")


if __name__ == "__main__":
    main()
