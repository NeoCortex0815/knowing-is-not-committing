"""MIT + WT-Reflex (08.11. nachts; nur Bau, KEIN Lauf; Nutzer 01:05: „an WT-A festhalten … gleiche Präzision mit dem längeren
Atem“, „Offline was bauen“).
Idee: Die Text-Auswertung (83) zeigt, dass WT-A dort präzise ist, wo der Reflex am richtigen Wert zuckt. Ohne Zucken fehlt ihm aber
MITs zweiter Weg: finden, lange prüfen, natürlich abschließen, abgeben. MIT löst 44 von 65 solcher Läufe, WT-A 7 von 30.
Bau: Basis + MIT-Edit (Rang 1, L15/L19, MITs u/Spalten/α aus minipc/mit_richtung.npz, wie minipc/05_patch.py) + die 16 WT-Neuronen
von WT-A (Bauart A) BITGLEICH übernommen. Übernommen werden die gate- und up-Zeilen in L15 und die down-Spalten in L15.
Begründung, warum die WT-Eichung gilt: Alle Eingriffe (eigen, MIT, WT) sitzen in down_proj von L15/L19 bzw. in den 16 Neuronen.
Der MLP-Eingang von L15 ist damit für denselben Text bei Basis, eigen, MIT, WT-A und MIT+WT identisch. Die Schwellen τ_T und τ_C
gelten unverändert. Die Zeilen von WT-A sind nicht überlappend mit MITs L15-Spalten (geprüft: 0).
Prüfungen: (1) WT-Zeilen und -Spalten bitgleich mit WT-A. (2) Außerhalb der 16 Neuronen ist L15/L19 down_proj gleich dem MIT-Nachbau.
(3) Der MIT-Nachbau wird gegen das MIT-GGUF (q8_0, entquantisiert) verglichen, mit dem Basis-q8_0 als Rausch-Maßstab.
  python 84_mit_wt_bauen.py --aus modelle/Qwen3.5-0.8B-mit-wt
"""
import argparse
import os
import sys

import numpy as np

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(HIER)
sys.path.insert(0, HIER)
import wsp_lib as W  # noqa: E402

L = 15


def gguf_tensor(pfad, name):
    sys.path.insert(0, os.path.join(WURZEL, "llama", "gguf-py"))
    import gguf
    from gguf import quants
    r = gguf.GGUFReader(pfad)
    for t in r.tensors:
        if t.name == name:
            return np.asarray(quants.dequantize(t.data, t.tensor_type), dtype=np.float64).reshape([int(x) for x in reversed(t.shape)])
    raise KeyError(name)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--aus", required=True)
    ap.add_argument("--basis", default=os.path.join(WURZEL, "modelle", "Qwen3.5-0.8B"))
    ap.add_argument("--wta", default=os.path.join(WURZEL, "modelle", "Qwen3.5-0.8B-ergo-zigA"))
    ap.add_argument("--mit", default=os.path.join(WURZEL, "minipc", "mit_richtung.npz"))
    ap.add_argument("--mit-gguf", default=os.path.join(WURZEL, "gguf", "Qwen3.5-0.8B-mit-q8_0.gguf"))
    ap.add_argument("--basis-gguf", default=os.path.join(WURZEL, "gguf", "Qwen3.5-0.8B-q8_0.gguf"))
    a = ap.parse_args()
    import json
    meta_wta = json.load(open(os.path.join(a.wta, "wsp_patch.json"), encoding="utf-8"))
    G = np.asarray(meta_wta["neuronen"], dtype=np.int64)
    R = dict(np.load(a.mit))
    patches, pruef = {}, {}
    for Ls in (15, 19):
        name = f"model.language_model.layers.{Ls}.mlp.down_proj.weight"
        W0 = np.asarray(W.bf16_to_f32(np.asarray(W.tensor_lesen(a.basis, name)[1])), dtype=np.float64)
        u = R[f"u_{Ls}"].astype(np.float64)
        u /= np.linalg.norm(u)
        sp = np.asarray(R[f"spalten_{Ls}"], dtype=np.int64)
        W1 = W.rang1_edit(W0, u, sp, float(R[f"alpha_{Ls}"]))
        bits = W.bf16_bits(W1)
        if Ls == L:
            assert not (set(G.tolist()) & set(sp.tolist())), "WT-Neuronen überlappen MITs Spalten"
            wta_bits = np.asarray(W.tensor_lesen(a.wta, name)[1])
            bits = bits.copy()
            bits[:, G] = wta_bits[:, G]
            pruef["down15_wt_spalten_bitgleich_mit_WT-A"] = bool(np.array_equal(bits[:, G], wta_bits[:, G]))
        patches[name] = bits
        # MIT-Nachbau gegen MIT-GGUF (q8_0), Maßstab: Basis gegen Basis-q8_0 auf denselben Spalten
        try:
            Wm = gguf_tensor(a.mit_gguf, f"blk.{Ls}.ffn_down.weight")
            Wb = gguf_tensor(a.basis_gguf, f"blk.{Ls}.ffn_down.weight")
            neu = np.asarray(W.bf16_to_f32(bits), dtype=np.float64)
            spx = np.array([s for s in sp if s not in set(G.tolist())])
            d_mit = float(np.linalg.norm(neu[:, spx] - Wm[:, spx]) / np.linalg.norm(Wm[:, spx]))
            d_rausch = float(np.linalg.norm(W0[:, spx] - Wb[:, spx]) / np.linalg.norm(Wb[:, spx]))
            d_ohne_edit = float(np.linalg.norm(W0[:, spx] - Wm[:, spx]) / np.linalg.norm(Wm[:, spx]))
            pruef[f"L{Ls}_rel_abstand_nachbau_zu_MIT-GGUF"] = round(d_mit, 5)
            pruef[f"L{Ls}_rel_abstand_basis_zu_basis-q8_0 (Rauschmaß)"] = round(d_rausch, 5)
            pruef[f"L{Ls}_rel_abstand_basis_zu_MIT-GGUF (ohne Edit)"] = round(d_ohne_edit, 5)
        except Exception as e:  # noqa: BLE001
            pruef[f"L{Ls}_gguf_vergleich"] = f"nicht möglich: {type(e).__name__}: {e}"
    for k in ("gate", "up"):
        name = f"model.language_model.layers.{L}.mlp.{k}_proj.weight"
        T = np.asarray(W.tensor_lesen(a.basis, name)[1]).copy()
        wta_bits = np.asarray(W.tensor_lesen(a.wta, name)[1])
        T[G, :] = wta_bits[G, :]
        pruef[f"{k}15_wt_zeilen_bitgleich_mit_WT-A"] = bool(np.array_equal(T[G, :], wta_bits[G, :]))
        andere = np.setdiff1d(np.arange(T.shape[0]), G)
        pruef[f"{k}15_uebrige_zeilen_gleich_basis"] = bool(np.array_equal(T[andere, :], np.asarray(W.tensor_lesen(a.basis, name)[1])[andere, :]))
        patches[name] = T
    for k, v in pruef.items():
        print(f"  {k}: {v}", flush=True)
    meta = {"art": "MIT-Edit (L15/L19, minipc/mit_richtung.npz) + WT-Reflex Bauart A (16 Neuronen bitgleich aus WT-A)",
            "neuronen": G.tolist(), **{k: meta_wta[k] for k in ("tau_T", "tau_C", "kappa_g", "kappa_u", "kappa_d", "kappa", "z_ziel")},
            "pruefungen": pruef}
    W.modell_mit_patch(a.basis, a.aus, patches, meta)
    print(f"Modell: {a.aus}")


if __name__ == "__main__":
    main()
