"""Überlebt ein Gewichts-Edit die Quantisierung? Direkter Vergleich auf Gewichtsebene (Sekunden statt Eval-Stunden).

  python 07_quant_check.py --basis MODELLE/Qwen3.5-0.8B --edit MODELLE/Qwen3.5-0.8B-mit \
      --gguf-basis GGUF/Qwen3.5-0.8B-q6_k.gguf --gguf-edit GGUF/Qwen3.5-0.8B-mit-q6_k.gguf \
      --richtung ergebnisse/mit_richtung.npz --aus ergebnisse/quant_check_q6_k.json

Je Edit-Schicht L (W0 = Basis bf16, W1 = Edit bf16, Q() = aus der GGUF dequantisiert):
  quant_fehler_basis   |Q(W0) - W0| / |W0|            Rauschen der Quantisierung (Plausibilität: klein)
  edit_erhalt          <D_q, D> / <D, D>               Anteil des Edits, der ankommt (1 = vollständig)
  edit_restfehler      |D_q - D| / |D|                 wie stark der Edit verrauscht ist (0 = exakt)
  u_projektion_erhalt  wie edit_erhalt, aber nur u^T D auf den Edit-Spalten (der wirksame Teil)
  mit D = W1 - W0 und D_q = Q(W1) - Q(W0).
"""
import argparse
import json
import os
import sys

import numpy as np

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
import wsp_lib as W  # noqa: E402


def gguf_tensor(pfad, name):
    from gguf import GGUFReader
    from gguf.quants import dequantize
    r = GGUFReader(pfad)
    t = {x.name: x for x in r.tensors}[name]
    a = dequantize(t.data, t.tensor_type)
    return a.reshape(list(reversed([int(x) for x in t.shape]))).astype(np.float64), t.tensor_type.name


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--basis", required=True)
    ap.add_argument("--edit", required=True)
    ap.add_argument("--gguf-basis", required=True)
    ap.add_argument("--gguf-edit", required=True)
    ap.add_argument("--richtung", help=".npz mit u_L / spalten_L (für u_projektion_erhalt)")
    ap.add_argument("--schichten", default="15,19")
    ap.add_argument("--muster", default="model.language_model.layers.{L}.mlp.down_proj.weight")
    ap.add_argument("--gguf-muster", default="blk.{L}.ffn_down.weight")
    ap.add_argument("--llama-cpp", default=os.environ.get("LLAMA_CPP", "llama.cpp"))
    ap.add_argument("--aus", required=True)
    a = ap.parse_args()
    sys.path.insert(0, os.path.join(a.llama_cpp, "gguf-py"))

    R = dict(np.load(a.richtung)) if a.richtung else {}
    i0, i1 = W.tensor_index(a.basis), W.tensor_index(a.edit)
    out = {"gguf_basis": a.gguf_basis, "gguf_edit": a.gguf_edit, "schichten": {}}
    for L in [int(x) for x in a.schichten.split(",")]:
        hf, gg = W.tensorname(a.muster, L), a.gguf_muster.format(L=L)
        W0 = W.tensor_f32(a.basis, hf, i0).astype(np.float64)
        W1 = W.tensor_f32(a.edit, hf, i1).astype(np.float64)
        Q0, typ0 = gguf_tensor(a.gguf_basis, gg)
        Q1, typ1 = gguf_tensor(a.gguf_edit, gg)
        assert Q0.shape == W0.shape == Q1.shape, (Q0.shape, W0.shape, Q1.shape)
        D, Dq = W1 - W0, Q1 - Q0
        b = {"typ": [typ0, typ1],
             "quant_fehler_basis": round(float(np.linalg.norm(Q0 - W0) / np.linalg.norm(W0)), 5),
             "edit_rel_groesse": round(float(np.linalg.norm(D) / np.linalg.norm(W0)), 5),
             "edit_erhalt": round(float(np.sum(Dq * D) / np.sum(D * D)), 4),
             "edit_restfehler": round(float(np.linalg.norm(Dq - D) / np.linalg.norm(D)), 4)}
        if f"u_{L}" in R:
            u = R[f"u_{L}"].astype(np.float64); u /= np.linalg.norm(u)
            sp = R.get(f"spalten_{L}")
            pd, pq = u @ D, u @ Dq
            if sp is not None:
                pd, pq = pd[sp], pq[sp]
            b["u_projektion_erhalt"] = round(float(pq @ pd / (pd @ pd)), 4)
        out["schichten"][L] = b
        print(L, b, flush=True)
    os.makedirs(os.path.dirname(os.path.abspath(a.aus)), exist_ok=True)
    json.dump(out, open(a.aus, "w"), indent=1)


if __name__ == "__main__":
    main()
