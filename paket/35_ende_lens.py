"""Ende-Token-Lens (Argon 06.11. ~04:30, Erklärung der Fehlerart „Denken zu, Antwort rechnet weiter“): Der wirksame
MIT-Rest stützt </think> UND das Antwort-Ende (<|endoftext|>/<|im_end|>), unsere Entschluss-Achse nur </think>?

Rang der Ende-Tokens in der Logit-Lens (0 = am stärksten angehoben, Unembedding mit γ der finalen Norm) für:
wirksamen MIT-Rest (−r⊥), unsere Kopplungs-Richtung e⊥ (Entschluss-Achse orthogonal zu u_e) und die Klingel-Achse.
Logit-Lens an Schicht 15/19 ist nur der direkte Pfad (grober Hinweis).
  python 35_ende_lens.py --modell modelle/Qwen3.5-0.8B --mit minipc/mit_richtung.npz --eigen ergebnisse/eigene_richtung-vL.npz \
      --entschluss ergebnisse/richtung-entschluss.npz --klingel ergebnisse/richtung-klingel.npz
"""
import argparse
import importlib.util
import os

import numpy as np

HIER = os.path.dirname(os.path.abspath(__file__))


def main():
    ap = argparse.ArgumentParser()
    for n in ("--modell", "--mit", "--eigen", "--entschluss", "--klingel"):
        ap.add_argument(n, required=True)
    a = ap.parse_args()
    s = importlib.util.spec_from_file_location("ll", os.path.join(HIER, "21_logit_lens.py"))
    ll = importlib.util.module_from_spec(s)
    s.loader.exec_module(ll)
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(a.modell)
    _, WU = ll.tensor(a.modell, ["lm_head.weight", "model.language_model.embed_tokens.weight", "model.embed_tokens.weight"])
    _, g = ll.tensor(a.modell, ["model.language_model.norm.weight", "model.norm.weight"])
    gamma = 1.0 + g if abs(g.mean()) < 0.5 else g
    ids = {t: tok.convert_tokens_to_ids(t) for t in ("</think>", "<|im_end|>", "<|endoftext|>")}
    M, E, A, K = (np.load(p) for p in (a.mit, a.eigen, a.entschluss, a.klingel))
    norm = lambda v: v / np.linalg.norm(v)
    print("Rang (0 = am stärksten angehoben) von", len(WU), "Tokens")
    for L in (15, 19):
        um, ue = norm(M[f"u_{L}"].astype(np.float64)), norm(E[f"u_{L}"].astype(np.float64))
        if um @ ue < 0:
            ue = -ue
        r = norm(um - (um @ ue) * ue)
        e = A[f"u_{L}"].astype(np.float64)
        e = norm(e - (e @ ue) * ue)
        k = norm(K[f"u_{L}"].astype(np.float64))
        for name, v in (("MIT-Rest wirksam (−r⊥)", -r), ("Kopplung e⊥ (Entschluss)", e), ("Klingel-Achse", k)):
            sc = WU @ (gamma * v)
            rang = np.empty(len(sc), int)
            rang[np.argsort(-sc)] = np.arange(len(sc))
            print(f"  Schicht {L} · {name:26s}", {t: int(rang[i]) for t, i in ids.items()})


if __name__ == "__main__":
    main()
