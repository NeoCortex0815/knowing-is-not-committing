"""Schild-Reflex, offline simuliert (08.11.; Nutzer-Bilder „Schilder hängt der Hausbewohner auf“, „zur Tür begleiten“; Lesart
N18 in ANNAHMEN; erkundend, nur vorhandene Daten, keine Generierung).
Auslöser: Das Modell schreibt selbst ein Schild („the (final) answer is“, „so the answer“, „therefore the answer“). Hat der Wert
direkt dahinter (≤ 15 Tokens) ein Wahrheits-Tor zT_max ≥ τ, feuert der Reflex: Dieser Wert wird abgegeben.
Ohne Auslöser bleibt das tatsächliche Ergebnis. Variante „Nachsicht“: erst beim 2. Schild mit demselben Wert.
  python 100_schild_reflex.py
"""
import json
import os
import re

import numpy as np

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(HIER)
ERG = os.path.join(WURZEL, "ergebnisse")
SCHILD = re.compile(r"(?:the final answer is|the answer is|so the answer|therefore,? the answer)", re.I)
QUELLEN = {"WT-A": ("zucken_WT-A_ergo-zigA.jsonl", ["s3-wta-161-210", "s3-wta-211-260", "s3-wta-261-300"]),
           "MIT": ("zucken_MIT_mit-wt.jsonl", ["s3-mit-161-260", "s3-mit-261-300"])}


def norm(w):
    return w.replace(" ", "").replace("$", "").replace("\\!", "").rstrip(".").lower()


def main():
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(os.path.join(WURZEL, "modelle", "Qwen3.5-0.8B"))
    for q, (datei, dirs) in QUELLEN.items():
        runs = {}
        for d in dirs:
            for z in open(os.path.join(ERG, d, "ergebnisse.jsonl"), encoding="utf-8"):
                r = json.loads(z)
                runs[r["id"]] = r
        Z = [json.loads(z) for z in open(os.path.join(ERG, datei), encoding="utf-8")]
        hinter = {}  # je Lauf: Liste (t, wert, ok, zT) der Werte direkt hinter einem Schild, zeitlich geordnet
        for z in Z:
            g = runs[z["id"]]["gen_ids"][:z["n_mess"]]
            st = [tok.decode([t]) for t in g]
            gr = np.cumsum([len(s) for s in st]) if st else np.array([0])
            text = "".join(st)
            sch = [int(np.searchsorted(gr, m.end() - 1, side="right")) for m in SCHILD.finditer(text)]
            L = []
            for s in sorted(z["aussagen"], key=lambda s: s["t"]):
                if s["ok"] is None:
                    continue
                if any(0 <= s["t"] - t <= 15 for t in sch):
                    L.append(s)
            hinter[z["id"]] = L
        ist_r = sum(z["korrekt"] for z in Z)
        ist_f = sum(1 for z in Z if not z["korrekt"] and z["art"] == "geschlossen, falsche Antwort")
        ist_tok = np.mean([runs[z["id"]]["tokens"] for z in Z])
        print(f"== {q}: tatsächlich richtig {ist_r}, falsch {ist_f}, S₂ {(ist_r - 2 * ist_f) / len(Z):+.3f}, Ø Tokens {ist_tok:.0f}")
        for nachsicht in (False, True):
            for tau in (0.0, 1.0, 2.0):
                k = {"r": 0, "f": 0, "o": 0, "feuer": 0}
                tok_ = []
                for z in Z:
                    feuer = None
                    zaehl = {}
                    for s in hinter[z["id"]]:
                        if s["zT_max"] < tau:
                            continue
                        n = norm(s["wert"])
                        zaehl[n] = zaehl.get(n, 0) + 1
                        if not nachsicht or zaehl[n] >= 2:
                            feuer = s
                            break
                    if feuer is None:
                        k["r" if z["korrekt"] else ("f" if z["art"] == "geschlossen, falsche Antwort" else "o")] += 1
                        tok_.append(runs[z["id"]]["tokens"])
                    else:
                        k["feuer"] += 1
                        k["r" if feuer["ok"] else "f"] += 1
                        tok_.append(feuer["t"] + 30)
                s2 = (k["r"] - 2 * k["f"]) / len(Z)
                print(f"   τ {tau:3.1f} {'Nachsicht (2. Schild)' if nachsicht else 'erstes Schild        '}: feuert {k['feuer']:3d} | richtig "
                      f"{k['r']:3d} ({k['r'] - ist_r:+d}), falsch {k['f']:3d}, ohne Abgabe {k['o']:3d} | S₂ {s2:+.3f} | Ø Tokens {np.mean(tok_):.0f}")


if __name__ == "__main__":
    main()
