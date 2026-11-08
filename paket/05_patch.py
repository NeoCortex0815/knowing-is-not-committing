"""Rang-1-Patch aus einer Richtungsdatei bauen: W = W0 - alpha * outer(u, maske * (u @ W0)).

  # eigene Richtung (04_richtung.py), wie MIT: alpha 6, 64 Spalten
  python 05_patch.py --basis MODELLE/Qwen3.5-0.8B --richtung ergebnisse/eigene_richtung.npz \
      --schichten 15,19 --alpha 6 --aus MODELLE/Qwen3.5-0.8B-eigen

  # Kontrolle: Zufallsrichtung (orthogonal zu u, gleiche Spalten, gleiche Stärke)
  python 05_patch.py ... --zufall --aus MODELLE/Qwen3.5-0.8B-zufall

--muster legt den Tensornamen fest ({L} = Schicht). Für MoE-Modelle später z.B. den Shared Expert:
  "model.language_model.layers.{L}.mlp.shared_expert.down_proj.weight"
"""
import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wsp_lib as W  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--basis", required=True)
    ap.add_argument("--richtung", required=True, help=".npz mit u_L und spalten_L (oder score_L)")
    ap.add_argument("--schichten", default="15,19")
    ap.add_argument("--alpha", type=float, default=6.0)
    ap.add_argument("--top-k", type=int, default=0, help="0 = Spalten aus der Datei; sonst Top-k nach score_L")
    ap.add_argument("--muster", default="model.language_model.layers.{L}.mlp.down_proj.weight")
    ap.add_argument("--zufall", action="store_true", help="Kontrolle mit Zufallsrichtung")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--vergleich-mit", help="editierter Modellordner zum Bit-Vergleich (z.B. MIT-Nachbau)")
    ap.add_argument("--aus", required=True)
    a = ap.parse_args()

    R = dict(np.load(a.richtung))
    index = W.tensor_index(a.basis)
    rng = np.random.default_rng(a.seed)
    patches, info = {}, {}
    for L in [int(x) for x in a.schichten.split(",")]:
        name = W.tensorname(a.muster, L)
        dt, bits = W.tensor_lesen(a.basis, name, index)
        assert dt == "BF16", f"{name}: erwartet BF16, ist {dt}"
        W0 = W.bf16_to_f32(np.asarray(bits))
        u = R[f"u_{L}"].astype(np.float64)
        u /= np.linalg.norm(u)
        if a.top_k:
            spalten = np.sort(np.argsort(-R[f"score_{L}"])[:a.top_k])
        else:
            spalten = R[f"spalten_{L}"]
        if a.zufall:
            z = rng.standard_normal(u.shape)
            z -= (z @ u) * u
            u = z / np.linalg.norm(z)
        W1 = W.rang1_edit(W0, u, spalten, a.alpha)
        neu = W.bf16_bits(W1)
        patches[name] = neu
        rel = float(np.linalg.norm(W1 - W0) / np.linalg.norm(W0))
        i = {"spalten": int(len(spalten)), "alpha": a.alpha, "relative_aenderung": round(rel, 5),
             "geaenderte_gewichte": int(np.sum(neu != np.asarray(bits)))}
        if a.vergleich_mit:
            _, ref = W.tensor_lesen(a.vergleich_mit, name)
            i["bits_gleich_wie_vergleich"] = round(float(np.mean(np.asarray(ref) == neu)), 6)
        info[name] = i
        print(name, i)
    meta = {"richtung": os.path.abspath(a.richtung), "alpha": a.alpha, "zufall": a.zufall,
            "formel": "W = W0 - alpha*outer(u, maske*(u@W0))", "tensoren": info}
    W.modell_mit_patch(a.basis, a.aus, patches, meta)
    print(f"Gepatchtes Modell: {a.aus}")
    print(json.dumps({"gesamt_geaendert": sum(i["geaenderte_gewichte"] for i in info.values())}))


if __name__ == "__main__":
    main()
