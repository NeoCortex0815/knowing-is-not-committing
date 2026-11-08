"""Zustands-Tür im Hinterzimmer (08.11.; Nutzer: „Hinterzimmer: eine Uhr und einen Ausgang … zurück ins Vorderzimmer oder
direkt Abgabe“, Weg 2 „halb innen“; Lesart N14 in ANNAHMEN; erkundend, nur vorhandene Daten, keine Generierung).
Die Tür öffnet nicht nach Zeit, sondern nach Zustand:
  - beim ersten Token mit Schleifen-Grad w ≥ W (wie 88), frühestens ab 1.000 Tokens;
  - mit Wahrheits-Blitz vorher (zT_max > 0 an einer Wert-Aussage): Abgabe des Werts mit dem höchsten (bzw. jüngsten) Blitz;
  - ohne Blitz: „weiß ich nicht“;
  - öffnet die Tür nie: tatsächliches Ergebnis des Laufs.
  python 95_zustandstuer.py   → ergebnisse/zustandstuer.json
"""
import importlib.util
import json
import os

import numpy as np

HIER = os.path.dirname(os.path.abspath(__file__))
ERG = os.path.join(os.path.dirname(HIER), "ergebnisse")
QUELLEN = {"WT-A": ("zucken_WT-A_ergo-zigA.jsonl", ["s3-wta-161-210", "s3-wta-211-260", "s3-wta-261-300"]),
           "MIT": ("zucken_MIT_mit-wt.jsonl", ["s3-mit-161-260", "s3-mit-261-300"])}


def lade_mod(name, pfad):
    s = importlib.util.spec_from_file_location(name, pfad)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


def main():
    fl = lade_mod("fl", os.path.join(HIER, "88_flur.py"))
    B = {}
    for q, (datei, dirs) in QUELLEN.items():
        runs = {}
        for d in dirs:
            for z in open(os.path.join(ERG, d, "ergebnisse.jsonl"), encoding="utf-8"):
                r = json.loads(z)
                runs[r["id"]] = r
        Z = [json.loads(z) for z in open(os.path.join(ERG, datei), encoding="utf-8")]
        W_ = {}
        for z in Z:
            W_[z["id"]] = fl.schleifen_grad(runs[z["id"]]["gen_ids"][:z["n_mess"]])
        ist = {"richtig": sum(z["korrekt"] for z in Z)}
        ist_f = sum(1 for z in Z if not z["korrekt"] and (z["art"] == "geschlossen, falsche Antwort"))
        ist["falsch"] = ist_f
        ist["enthalten"] = len(Z) - ist["richtig"] - ist_f
        ist["S2"] = (ist["richtig"] - 2 * ist_f) / len(Z)
        ist["tokens"] = float(np.mean([runs[z["id"]]["tokens"] for z in Z]))
        print(f"== {q}: tatsächlich richtig {ist['richtig']}, falsch {ist_f}, ohne Abgabe {ist['enthalten']}, S₂ {ist['S2']:+.3f}, "
              f"Ø Tokens {ist['tokens']:.0f}")
        B[q] = {"tatsaechlich": ist}
        for W in (0.3, 0.5, 0.7):
            for wahl in ("hoechster", "juengster"):
                k = {"richtig": 0, "falsch": 0, "enthalten": 0, "tuer_auf": 0, "abgabe_blitz": 0, "pausenraum": 0}
                tok = []
                for z in Z:
                    w = W_[z["id"]]
                    kandidat = np.where((w >= W) & (np.arange(len(w)) >= 1000))[0]
                    if len(kandidat) == 0:
                        art = "richtig" if z["korrekt"] else ("falsch" if z["art"] == "geschlossen, falsche Antwort" else "enthalten")
                        k[art] += 1
                        tok.append(runs[z["id"]]["tokens"])
                        continue
                    t_auf = int(kandidat[0])
                    k["tuer_auf"] += 1
                    tok.append(t_auf + 20)
                    blitze = [s for s in z["aussagen"] if s["t"] < t_auf and s["zT_max"] > 0 and s["ok"] is not None]
                    if blitze:
                        s = max(blitze, key=lambda s: s["zT_max"]) if wahl == "hoechster" else max(blitze, key=lambda s: s["t"])
                        k["abgabe_blitz"] += 1
                        k["richtig" if s["ok"] else "falsch"] += 1
                    else:
                        k["pausenraum"] += 1
                        k["enthalten"] += 1
                n = len(Z)
                k["S2"] = (k["richtig"] - 2 * k["falsch"]) / n
                k["tokens"] = float(np.mean(tok))
                B[q][f"W{W}_{wahl}"] = k
                print(f"   W {W} ({wahl:9s} Blitz): Tür auf {k['tuer_auf']:3d} → Abgabe {k['abgabe_blitz']:3d}, Pausenraum {k['pausenraum']:3d} | "
                      f"richtig {k['richtig']:3d} ({k['richtig'] - ist['richtig']:+d}), falsch {k['falsch']:3d}, ohne Abgabe {k['enthalten']:3d} | "
                      f"S₂ {k['S2']:+.3f} | Ø Tokens {k['tokens']:.0f}")
    json.dump(B, open(os.path.join(ERG, "zustandstuer.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(f"gespeichert: {os.path.join(ERG, 'zustandstuer.json')}")


if __name__ == "__main__":
    main()
