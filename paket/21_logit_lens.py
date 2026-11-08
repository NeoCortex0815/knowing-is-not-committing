"""Stufe A (Vorschlag Argon, 05.11.): Logit-Lens des Rests der MIT-Richtung, den unsere Richtungen nicht erklären.

r⊥ = MIT-u minus seine Projektion auf span(eigene Richtungen), normiert. Projektion über die finale RMSNorm (γ) auf die
Unembedding-Matrix W_U: s_v = r⊥ · (γ ⊙ W_U[v]). Ausgabe: Tokens mit den höchsten und niedrigsten Werten.
Entschluss-Hypothese gestützt, wenn an den Enden Abschluss-Tokens (</think>, Therefore, boxed …) Reflexions-Tokens
(Wait, Alternatively, Hmm …) gegenüberstehen. Zum Vergleich dieselbe Projektion für MIT-u und die eigene Richtung.
Hinweis: Logit-Lens an mittleren Schichten (15/19 von 24) ist nur ein grober Blick.

  python 21_logit_lens.py --modell modelle/Qwen3.5-0.8B --mit minipc/mit_richtung.npz \
      --eigene ergebnisse/richtung-vL-alle.npz ergebnisse/richtung-messer3.npz
"""
import argparse
import json
import os

import numpy as np
from safetensors import safe_open


def tensor(modell, namen):
    idx = json.load(open(os.path.join(modell, "model.safetensors.index.json")))["weight_map"]
    for n in namen:
        if n in idx:
            with safe_open(os.path.join(modell, idx[n]), framework="pt") as f:
                return n, f.get_tensor(n).float().numpy().astype(np.float64)
    raise SystemExit(f"keiner gefunden: {namen}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--modell", required=True)
    ap.add_argument("--mit", required=True)
    ap.add_argument("--eigene", nargs="+", required=True)
    ap.add_argument("--schichten", default="15,19")
    ap.add_argument("--top", type=int, default=20)
    a = ap.parse_args()
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(a.modell)
    n_u, WU = tensor(a.modell, ["lm_head.weight", "model.language_model.embed_tokens.weight", "model.embed_tokens.weight"])
    n_g, g = tensor(a.modell, ["model.language_model.norm.weight", "model.norm.weight"])
    gamma = 1.0 + g if abs(g.mean()) < 0.5 else g  # Qwen3.5/Next: nullzentrierte Norm (1 + w)
    print(f"Unembedding: {n_u} {WU.shape} | Norm: {n_g}, Mittel w = {g.mean():.3f} -> gamma = {'1+w' if abs(g.mean()) < 0.5 else 'w'}")
    M = dict(np.load(a.mit))
    E = [dict(np.load(p)) for p in a.eigene]
    zeig = lambda ids: ", ".join(repr(tok.decode([int(i)])) for i in ids)
    for L in map(int, a.schichten.split(",")):
        um = M[f"u_{L}"].astype(np.float64); um /= np.linalg.norm(um)
        Q = np.linalg.qr(np.stack([e[f"u_{L}"].astype(np.float64) for e in E], 1))[0]
        r = um - Q @ (Q.T @ um); r /= np.linalg.norm(r)
        ue = E[0][f"u_{L}"].astype(np.float64); ue /= np.linalg.norm(ue)
        for name, v in (("REST r⊥", r), ("MIT-u", um), ("eigene u", ue)):
            s = WU @ (gamma * v)
            o = np.argsort(s)
            print(f"\n== Schicht {L} · {name}\n  hoch:   {zeig(o[::-1][:a.top])}\n  niedrig: {zeig(o[:a.top])}")
        ids = {t: tok.convert_tokens_to_ids(t) for t in ("</think>",)}
        for w in ("Wait", " Wait", "Therefore", " Therefore", " So", "Alternatively", " Hmm"):
            ii = tok.encode(w, add_special_tokens=False)
            if len(ii) == 1:
                ids[w] = ii[0]
        s = WU @ (gamma * r)
        rang = np.empty(len(s), int); rang[np.argsort(-s)] = np.arange(len(s))
        print("  Rang im REST (0 = höchster Wert, von", len(s), "):", {k: int(rang[v]) for k, v in ids.items()})


if __name__ == "__main__":
    main()
