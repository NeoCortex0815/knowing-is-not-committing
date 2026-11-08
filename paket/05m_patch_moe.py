"""Rang-1-Patch für MoE-Modelle (Qwen3.5/3.6-MoE: gebündelte Experten + Shared Expert).

Gleiche Formel wie der MIT-Edit, je Experte e auf dessen down_proj-Block W_e [d_model, d_ff_e]:
    W_e[:, j] <- W_e[:, j] - alpha * u * (u . W_e[:, j])      für die ausgewählten Neuronen (e, j)
und für den Shared Expert wie beim dichten Modell (05_patch.py).

  python 05m_patch_moe.py --basis MODELLE/Qwen3.6-35B-A3B --richtung ergebnisse/richtung_moe.npz \
      --schichten 15,19 --alpha 6 --aus MODELLE/Qwen3.6-35B-A3B-eigen
  # Kontrolle: Zufallsrichtung orthogonal zu u, gleiche Neuronen; --alpha-zufall für gleiche Änderungsstärke
  python 05m_patch_moe.py ... --zufall --aus MODELLE/Qwen3.6-35B-A3B-zufall

Richtungsdatei (aus 04s_richtung_schichtweise.py):
  u_L                 Einheitsvektor im Residual Stream
  exp_spalten_L       [k, 2] int  (Experte, Neuron) der gebündelten Experten
  shared_spalten_L    [k]    int  Neuronen des Shared Expert (optional)
Nur die Shards mit geänderten Tensoren werden kopiert (wsp_lib.modell_mit_patch), der Rest verlinkt.
"""
import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wsp_lib as W  # noqa: E402


def edit_experten(W0, u, paare, alpha):
    """W0 [E, d_model, d_ff] float32; paare [k, 2] (e, j). Gibt float32-Kopie mit Edit zurück."""
    W1 = np.array(W0, dtype=np.float32, copy=True)
    u = np.asarray(u, dtype=np.float64)
    u = u / np.linalg.norm(u)
    for e, j in np.asarray(paare, dtype=np.int64):
        col = W1[e, :, j].astype(np.float64)
        W1[e, :, j] = (col - alpha * (u @ col) * u).astype(np.float32)
    return W1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--basis", required=True)
    ap.add_argument("--richtung", required=True)
    ap.add_argument("--schichten", default="15,19")
    ap.add_argument("--alpha", type=float, default=6.0)
    ap.add_argument("--teile", default="experten,shared", help="welche Teile editiert werden: experten,shared")
    ap.add_argument("--exp-muster", default="model.language_model.layers.{L}.mlp.experts.down_proj")
    ap.add_argument("--shared-muster", default="model.language_model.layers.{L}.mlp.shared_expert.down_proj.weight")
    ap.add_argument("--zufall", action="store_true", help="Kontrolle: Zufallsrichtung orthogonal zu u")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--aus", required=True)
    a = ap.parse_args()

    R = dict(np.load(a.richtung))
    teile = set(a.teile.split(","))
    index = W.tensor_index(a.basis)
    rng = np.random.default_rng(a.seed)
    patches, info = {}, {}
    for L in [int(x) for x in a.schichten.split(",")]:
        u = R[f"u_{L}"].astype(np.float64)
        u /= np.linalg.norm(u)
        if a.zufall:
            z = rng.standard_normal(u.shape)
            z -= (z @ u) * u
            u = z / np.linalg.norm(z)
        ziele = []
        if "experten" in teile and f"exp_spalten_{L}" in R:
            ziele.append(("experten", W.tensorname(a.exp_muster, L), R[f"exp_spalten_{L}"]))
        if "shared" in teile and f"shared_spalten_{L}" in R:
            ziele.append(("shared", W.tensorname(a.shared_muster, L), R[f"shared_spalten_{L}"]))
        if not ziele:
            raise SystemExit(f"Schicht {L}: keine Neuronen in {a.richtung} (exp_spalten_{L} / shared_spalten_{L})")
        for teil, name, sel in ziele:
            if teil == "experten" and name not in index:  # Checkpoint mit Einzel-Experten: experts.{e}.down_proj.weight
                basis = name.rsplit(".", 1)[0]
                sel = np.asarray(sel, dtype=np.int64)
                for e in sorted(set(sel[:, 0].tolist())):
                    en = f"{basis}.{e}.down_proj.weight"
                    dt, bits = W.tensor_lesen(a.basis, en, index)
                    assert dt == "BF16", f"{en}: erwartet BF16, ist {dt}"
                    W0 = W.bf16_to_f32(np.asarray(bits))
                    W1 = W.rang1_edit(W0, u, sel[sel[:, 0] == e, 1], a.alpha)
                    patches[en] = W.bf16_bits(W1)
                n_geaendert = sum(int(np.sum(patches[f"{basis}.{e}.down_proj.weight"] !=
                                             np.asarray(W.tensor_lesen(a.basis, f"{basis}.{e}.down_proj.weight", index)[1])))
                                  for e in set(sel[:, 0].tolist()))
                info[basis + ".*.down_proj.weight"] = {"teil": teil, "format": "einzel", "neuronen": int(len(sel)),
                                                       "alpha": a.alpha, "geaenderte_gewichte": n_geaendert,
                                                       "experten_betroffen": int(len(set(sel[:, 0].tolist())))}
                print(basis, info[basis + ".*.down_proj.weight"], flush=True)
                continue
            dt, bits = W.tensor_lesen(a.basis, name, index)
            assert dt == "BF16", f"{name}: erwartet BF16, ist {dt}"
            W0 = W.bf16_to_f32(np.asarray(bits))
            if teil == "experten":
                assert W0.ndim == 3, f"{name}: erwartet [E, d_model, d_ff], ist {W0.shape}"
                W1 = edit_experten(W0, u, sel, a.alpha)
                anz = int(len(sel))
            else:
                W1 = W.rang1_edit(W0, u, sel, a.alpha)
                anz = int(len(sel))
            neu = W.bf16_bits(W1)
            patches[name] = neu
            rel = float(np.linalg.norm(W1 - W0) / np.linalg.norm(W0))
            i = {"teil": teil, "neuronen": anz, "alpha": a.alpha, "relative_aenderung": round(rel, 6),
                 "geaenderte_gewichte": int(np.sum(neu != np.asarray(bits)))}
            if teil == "experten":
                i["experten_betroffen"] = int(len(set(np.asarray(sel)[:, 0].tolist())))
            info[name] = i
            print(name, i, flush=True)
            del W0, W1
    meta = {"richtung": os.path.abspath(a.richtung), "alpha": a.alpha, "zufall": a.zufall,
            "formel": "W_e[:, j] -= alpha * u * (u . W_e[:, j]) fuer ausgewaehlte (e, j)", "tensoren": info}
    W.modell_mit_patch(a.basis, a.aus, patches, meta)
    print(f"Gepatchtes Modell: {a.aus}")
    print(json.dumps({"gesamt_geaendert": sum(i["geaenderte_gewichte"] for i in info.values())}))


if __name__ == "__main__":
    main()
