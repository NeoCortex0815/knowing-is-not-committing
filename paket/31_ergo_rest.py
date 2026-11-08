"""Schnelltest ERGO-Kante (Nutzer 06.11.: fehlendes Puzzlestück „Sicherheit ERGO gib jetzt ab“).

Frage: Erklärt unsere eigene, unabhängig gemessene Klingel-/Entschluss-Achse den Teil der MIT-Richtung, den unsere
Reparatur-Richtung nicht hat (Rest r⊥; Logit-Lens 05.11.: thereby/results/answers/</think>)?
Je Schicht: cos(MIT, eigen); r⊥ = MIT-u ohne eigenen Anteil; cos(r⊥, Achse); Anteil der r⊥-Energie, den die Achse
zusätzlich erklärt; Logit-Lens-Vorzeichen (Abschluss- minus Zweifel-Tokens, >0 = schiebt Richtung Abschluss).
Kontrollen: Zufallsbasis |cos| ~ 1/sqrt(1024) = 0,03, Energieanteil einer Zufallsrichtung ~ 0,001; Permutation der
Achse (gleiche Werte, zerstörte Lage); cos ohne die 10 größten Koordinaten der Achse (Ausreißer-Dimensionen).
Nur Diagnose (keine Bewertung), läuft auf der CPU in Sekunden.
  python 31_ergo_rest.py --modell modelle/Qwen3.5-0.8B --mit minipc/mit_richtung.npz \
      --eigen ergebnisse/eigene_richtung-vL.npz --achsen klingel=ergebnisse/richtung-klingel.npz \
      entschluss=ergebnisse/richtung-entschluss.npz --aus ergebnisse/ergo_rest.json
"""
import argparse
import json
import os

import numpy as np
from safetensors import safe_open

ABSCHLUSS = ("</think>", " Therefore", " Thus", " So")
ZWEIFEL = (" Wait", "Wait", " Alternatively", " Hmm", " But")


def zeilen(modell, namen, ids=None):
    idx = json.load(open(os.path.join(modell, "model.safetensors.index.json")))["weight_map"]
    for n in namen:
        if n in idx:
            with safe_open(os.path.join(modell, idx[n]), framework="pt") as f:
                sl = f.get_slice(n)
                if ids is None:
                    return sl[:].float().numpy().astype(np.float64)
                return np.stack([sl[i:i + 1].float().numpy()[0] for i in ids]).astype(np.float64)
    raise SystemExit(f"keiner gefunden: {namen}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--modell", required=True)
    ap.add_argument("--mit", required=True)
    ap.add_argument("--eigen", required=True)
    ap.add_argument("--achsen", nargs="+", required=True)
    ap.add_argument("--schichten", default="15,19")
    ap.add_argument("--aus", default="")
    a = ap.parse_args()
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(a.modell)
    ids, art = [], []
    for w in ABSCHLUSS + ZWEIFEL:
        ii = [tok.convert_tokens_to_ids(w)] if w == "</think>" else tok.encode(w, add_special_tokens=False)
        if len(ii) == 1:
            ids.append(ii[0])
            art.append(1 if w in ABSCHLUSS else -1)
    art = np.array(art)
    WU = zeilen(a.modell, ["lm_head.weight", "model.language_model.embed_tokens.weight", "model.embed_tokens.weight"], ids)
    g = zeilen(a.modell, ["model.language_model.norm.weight", "model.norm.weight"])
    gamma = 1.0 + g if abs(g.mean()) < 0.5 else g

    def lens(v):
        s = WU @ (gamma * v)
        return float(s[art > 0].mean() - s[art < 0].mean())

    norm = lambda v: v / np.linalg.norm(v)
    M = dict(np.load(a.mit))
    E = dict(np.load(a.eigen))
    A = {k: dict(np.load(p)) for k, p in (s.split("=", 1) for s in a.achsen)}
    rng = np.random.default_rng(0)
    erg = {}
    for L in map(int, a.schichten.split(",")):
        um = norm(M[f"u_{L}"].astype(np.float64))
        ue = norm(E[f"u_{L}"].astype(np.float64))
        if um @ ue < 0:
            ue = -ue
        r = um - (um @ ue) * ue
        rn2 = r @ r
        rh = r / np.sqrt(rn2)
        z = {"cos_mit_eigen": um @ ue, "rest_energie": rn2, "lens_mit": lens(um), "lens_eigen": lens(ue), "lens_rest": lens(rh)}
        alle = [ue]
        for k, D in A.items():
            ua = norm(D[f"u_{L}"].astype(np.float64))
            alle.append(ua)
            z[f"cos_rest_{k}"] = rh @ ua
            z[f"cos_mit_{k}"] = um @ ua
            z[f"cos_eigen_{k}"] = ue @ ua
            z[f"lens_{k}"] = lens(ua)
            Q = np.linalg.qr(np.stack([ue, ua], 1))[0]
            r2 = um - Q @ (Q.T @ um)
            z[f"rest_erklaert_{k}"] = 1 - (r2 @ r2) / rn2
            perm = [abs(rh @ ua[rng.permutation(len(ua))]) for _ in range(1000)]
            z[f"perm_cos_{k}_p95"] = float(np.quantile(perm, 0.95))
            ohne = ua.copy()
            ohne[np.argsort(-np.abs(ua))[:10]] = 0
            z[f"cos_rest_{k}_ohne_top10"] = rh @ norm(ohne)
        Q = np.linalg.qr(np.stack(alle, 1))[0]
        r2 = um - Q @ (Q.T @ um)
        z["rest_erklaert_alle_achsen"] = 1 - (r2 @ r2) / rn2
        erg[L] = {k: round(float(v), 4) for k, v in z.items()}
        print(f"\n== Schicht {L}")
        for k, v in erg[L].items():
            print(f"  {k:28s} {v:+.4f}")
    if a.aus:
        json.dump(erg, open(a.aus, "w"), indent=1)
        print("\ngespeichert:", a.aus)


if __name__ == "__main__":
    main()
