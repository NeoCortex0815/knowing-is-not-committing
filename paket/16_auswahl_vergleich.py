"""Neuronen-Auswahl gegen die MIT-Musterlösung vergleichen (nur CPU, Sekunden).

Aus richtung.npz (04s): u_L (Richtung) und score_L = da * (u_L @ W_down). Mit W_down aus dem Modell lässt sich
w = u_L @ W_down berechnen und daraus da = score / w (Aktivierungsdifferenz Schleife − produktiv je Neuron) zurückgewinnen.
Dann werden verschiedene Auswahlregeln (Top-64) gegen die MIT-Spalten (mit_richtung.npz: spalten_L) verglichen.

  python 16_auswahl_vergleich.py --modell modelle/Qwen3.5-0.8B --richtung ergebnisse/richtung-vL-alle.npz \
      --mit minipc/mit_richtung.npz --schichten 15,19
"""
import argparse
import json
import os

import numpy as np
from safetensors import safe_open


def lade_wd(modell, L, muster):
    idx = json.load(open(os.path.join(modell, "model.safetensors.index.json")))["weight_map"] \
        if os.path.exists(os.path.join(modell, "model.safetensors.index.json")) else None
    name = muster.format(L=L)
    datei = idx[name] if idx else "model.safetensors"
    with safe_open(os.path.join(modell, datei), framework="pt") as f:
        return f.get_tensor(name).float().numpy().astype(np.float64)  # [hidden, intermediate]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--modell", required=True)
    ap.add_argument("--richtung", required=True)
    ap.add_argument("--mit", required=True)
    ap.add_argument("--schichten", default="15,19")
    ap.add_argument("--k", type=int, default=64)
    ap.add_argument("--muster", default="model.language_model.layers.{L}.mlp.down_proj.weight")
    a = ap.parse_args()
    R, M = dict(np.load(a.richtung)), dict(np.load(a.mit))
    k = a.k
    for L in map(int, a.schichten.split(",")):
        Wd = lade_wd(a.modell, L, a.muster)
        u, um = R[f"u_{L}"].astype(np.float64), M[f"u_{L}"].astype(np.float64)
        score = R[f"score_{L}"].astype(np.float64)
        w, wm = u @ Wd, um @ Wd
        da = np.where(np.abs(w) > 1e-12, score / np.where(np.abs(w) > 1e-12, w, 1), 0.0)
        mit = set(M[f"spalten_{L}"].tolist())
        regeln = {
            "bisher: da*w (größte)": da * w,
            "|da*w|": np.abs(da * w),
            "da*w (kleinste)": -(da * w),
            "nur |w| (schreibt in Richtung)": np.abs(w),
            "nur w (größte)": w,
            "nur da (größte)": da,
            "nur |da|": np.abs(da),
            "da*w mit MIT-Richtung": da * wm,
            "|da*w| mit MIT-Richtung": np.abs(da * wm),
            "nur |w| mit MIT-Richtung": np.abs(wm),
            "|w|*Spaltennorm": np.abs(w) * np.linalg.norm(Wd, axis=0),
        }
        print(f"\n== Schicht {L}: {Wd.shape[1]} Neuronen, Top-{k}, Treffer = gemeinsame Neuronen mit MIT (Zufall ~{k*k/Wd.shape[1]:.1f})")
        for name, s in sorted(regeln.items(), key=lambda kv: -len(set(np.argsort(-kv[1])[:k].tolist()) & mit)):
            top = set(np.argsort(-s)[:k].tolist())
            print(f"  {len(top & mit):2d}/{k}  {name}")
        # Wo stehen die MIT-Neuronen in unserer bisherigen Rangfolge? Und welche Vorzeichen haben da und w dort?
        rang = np.empty(len(score), int); rang[np.argsort(-(da * w))] = np.arange(len(score))
        mr = np.sort(rang[sorted(mit)])
        print(f"  MIT-Neuronen in unserer Rangfolge: Median Rang {int(np.median(mr))}, schlechtester {mr[-1]}, "
              f"Anteil in Top-128 {np.mean(mr < 128):.0%}")
        ms = sorted(mit)
        print(f"  MIT-Neuronen: da>0 {np.mean(da[ms] > 0):.0%}, w>0 {np.mean(w[ms] > 0):.0%}, da*w>0 {np.mean(da[ms]*w[ms] > 0):.0%}"
              f" | alle Neuronen: da>0 {np.mean(da > 0):.0%}, w>0 {np.mean(w > 0):.0%}")


if __name__ == "__main__":
    main()
