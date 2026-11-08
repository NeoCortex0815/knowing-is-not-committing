"""Relative (rollierende) Wahrheits-Schwelle (08.11.; Vorschlag Poow V2: „Wenn die Werte nur knapp über der Schwelle liegen, ist
eine feste Schwelle das Problem“; NACHTRÄGLICH, erkundend, nur Auswertung vorhandener Daten).
Je Lauf, Wert-Aussagen in Zeitfolge: z_rel = (zT_max − Mittel der früheren Aussagen) / (Streuung der früheren + 0,5);
mindestens 5 frühere Aussagen, sonst kein Wert.
Vergleich: AUC richtig gegen falsch für zT (fest) und z_rel (relativ). Außerdem der erste Zucker unter einer Regel „z_rel ≥ c UND
up_arg ≥ 0,5“ (an richtigem / falschem Wert), auf WT-A- und MIT-Texten.
  python 90_relative_schwelle.py
"""
import json
import os

import numpy as np

ERG = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ergebnisse")
DATEIEN = {"WT-A": "zucken_WT-A_ergo-zigA.jsonl", "MIT": "zucken_MIT_mit-wt.jsonl"}


def auc(a, b):
    if not a or not b:
        return float("nan")
    x = np.concatenate([a, b])
    r = x.argsort().argsort() + 1.0
    return float((r[:len(a)].sum() - len(a) * (len(a) + 1) / 2) / (len(a) * len(b)))


def main():
    for q, datei in DATEIEN.items():
        Rf, Ff, Rr, Fr = [], [], [], []
        laeufe = []
        for z in open(os.path.join(ERG, datei), encoding="utf-8"):
            r = json.loads(z)
            A = sorted([s for s in r["aussagen"] if s["ok"] is not None], key=lambda s: s["t"])
            vor = []
            folge = []
            for s in A:
                zrel = None
                if len(vor) >= 5:
                    zrel = (s["zT_max"] - np.mean(vor)) / (np.std(vor) + 0.5)
                    (Rr if s["ok"] else Fr).append(zrel)
                (Rf if s["ok"] else Ff).append(s["zT_max"])
                folge.append((s, zrel))
                vor.append(s["zT_max"])
            laeufe.append(folge)
        print(f"== {q}-Texte: AUC richtig/falsch – fest zT {auc(Rf, Ff):.3f} | relativ z_rel {auc(Rr, Fr):.3f} "
              f"(n richtig {len(Rr)}, falsch {len(Fr)})")
        for c in (1.5, 2.0, 2.5, 3.0):
            k = {"richtig": 0, "falsch": 0, "kein": 0}
            for folge in laeufe:
                erst = None
                for s, zrel in folge:
                    if zrel is not None and zrel >= c and s["up_arg"] >= 0.5:
                        erst = s
                        break
                k["kein" if erst is None else ("richtig" if erst["ok"] else "falsch")] += 1
            print(f"   erster Zucker bei z_rel ≥ {c} und Kandidaten-Ende: richtig {k['richtig']}, falsch {k['falsch']}, kein {k['kein']}")
        k = {"richtig": 0, "falsch": 0, "kein": 0}
        for folge in laeufe:
            erst = None
            for s, _ in folge:
                if s["S_max"] >= 0.5:
                    erst = s
                    break
            k["kein" if erst is None else ("richtig" if erst["ok"] else "falsch")] += 1
        print(f"   zum Vergleich feste Schwelle (S ≥ 0,5): richtig {k['richtig']}, falsch {k['falsch']}, kein {k['kein']}")


if __name__ == "__main__":
    main()
