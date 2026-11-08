"""Zustands-Tür, zweiter Anlauf (08.11.; Nutzer-Bild „verirrt erkennt man am Gesicht … kaum Antworten … dazu müsste man wissen,
dass man sich verlaufen hat“; Lesart N16 in ANNAHMEN; erkundend, nur vorhandene Daten).
Statt bloßer Wiederholung (95, gescheitert) öffnet die Tür, wenn beides gilt:
  - Schleifen-Grad w ≥ 0,5;
  - in den letzten 2.000 Tokens ist KEIN neuer Wert aufgetaucht, also nur Werte, die vorher schon genannt waren („kaum Antworten“).
Frühestens ab 2.000 Tokens.
Abgabe: (a) höchster Blitz wie N14; (b) „bestätigt“: nur ein Wert mit ≥ 2 Blitzen (zT_max > 0), sonst „weiß ich nicht“.
  python 97_tuer_kaum_antworten.py
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


def norm(w):
    return w.replace(" ", "").replace("$", "").replace("\\!", "").rstrip(".").lower()


def main():
    fl = lade_mod("fl", os.path.join(HIER, "88_flur.py"))
    for q, (datei, dirs) in QUELLEN.items():
        runs = {}
        for d in dirs:
            for z in open(os.path.join(ERG, d, "ergebnisse.jsonl"), encoding="utf-8"):
                r = json.loads(z)
                runs[r["id"]] = r
        Z = [json.loads(z) for z in open(os.path.join(ERG, datei), encoding="utf-8")]
        ist_r = sum(z["korrekt"] for z in Z)
        ist_f = sum(1 for z in Z if not z["korrekt"] and z["art"] == "geschlossen, falsche Antwort")
        print(f"== {q}: tatsächlich richtig {ist_r}, falsch {ist_f}, S₂ {(ist_r - 2 * ist_f) / len(Z):+.3f}")
        for regel in ("hoechster", "bestaetigt"):
            k = {"r": 0, "f": 0, "o": 0, "auf": 0}
            tok = []
            for z in Z:
                w = fl.schleifen_grad(runs[z["id"]]["gen_ids"][:z["n_mess"]])
                A = sorted([s for s in z["aussagen"] if s["ok"] is not None], key=lambda s: s["t"])
                erst = {}
                for s in A:
                    erst.setdefault(norm(s["wert"]), s["t"])
                neu_t = np.array(sorted(erst.values())) if erst else np.array([])
                t_auf = None
                for t in range(2000, len(w), 50):
                    if w[t] < 0.5:
                        continue
                    if not np.any((neu_t > t - 2000) & (neu_t <= t)):
                        t_auf = t
                        break
                if t_auf is None:
                    k["r" if z["korrekt"] else ("f" if z["art"] == "geschlossen, falsche Antwort" else "o")] += 1
                    tok.append(runs[z["id"]]["tokens"])
                    continue
                k["auf"] += 1
                tok.append(t_auf + 20)
                bl = [s for s in A if s["t"] < t_auf and s["zT_max"] > 0]
                wahl = None
                if regel == "hoechster" and bl:
                    wahl = max(bl, key=lambda s: s["zT_max"])
                elif regel == "bestaetigt" and bl:
                    from collections import Counter
                    c = Counter(norm(s["wert"]) for s in bl)
                    ok_w = [s for s in bl if c[norm(s["wert"])] >= 2]
                    wahl = max(ok_w, key=lambda s: s["zT_max"]) if ok_w else None
                if wahl is None:
                    k["o"] += 1
                else:
                    k["r" if wahl["ok"] else "f"] += 1
            s2 = (k["r"] - 2 * k["f"]) / len(Z)
            print(f"   Tür „kaum Antworten“, Abgabe {regel:10s}: Tür auf {k['auf']:3d} | richtig {k['r']:3d} ({k['r'] - ist_r:+d}), "
                  f"falsch {k['f']:3d}, ohne Abgabe {k['o']:3d} | S₂ {s2:+.3f} | Ø Tokens {np.mean(tok):.0f}")


if __name__ == "__main__":
    main()
