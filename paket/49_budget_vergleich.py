"""Schritt 1c (vorab festgelegt 06.11. ~20:05, ANNAHMEN): Ist der Einbruch bei Temperatur 1,0 ein Budget-Artefakt?
ERGORE und MIT bei 1,0 mit 12k (vorhanden) und 32k (neu), 60 Übungsaufgaben. Lesart (nach WREN): Budget-Artefakt = bei 32k
ERGORE ≥ MIT − 2 UND leere Schließungen (Flur: Denken zu, Antwort nie fertig) von ERGORE < 5; sonst nicht die Hauptursache.
  python 49_budget_vergleich.py --e12 temp10-kw75 --m12 temp10-mit --e32 temp10-32k-kw75 --m32 temp10-32k-mit
"""
import argparse
import json
import os
from math import comb

import numpy as np

ERG = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ergebnisse")


def lade(d):
    return {json.loads(z)["id"]: json.loads(z) for z in open(os.path.join(ERG, d, "ergebnisse.jsonl"), encoding="utf-8")}


def mcnemar(a, b):
    n = a + b
    return min(1.0, 2 * sum(comb(n, x) for x in range(0, min(a, b) + 1)) / 2 ** n) if n else 1.0


def kennz(d, ids):
    r = [d[i] for i in ids]
    zu_pos = [x["text"].find("</think>") for x in r if "</think>" in x["text"]]
    return {"richtig": sum(bool(x["korrekt"]) for x in r), "flur": sum("</think>" in x["text"] and x["ende"] != "eos" for x in r),
            "nie_zu": sum("</think>" not in x["text"] for x in r), "abgegeben": sum(x["ende"] == "eos" for x in r),
            "tokens": round(float(np.mean([x.get("tokens", 0) for x in r]))),
            "zu_zeichen_median": int(np.median(zu_pos)) if zu_pos else None}


def main():
    ap = argparse.ArgumentParser()
    for n in ("--e12", "--m12", "--e32", "--m32"):
        ap.add_argument(n, required=True)
    ap.add_argument("--aus", default=os.path.join(ERG, "budget_vergleich.json"))
    a = ap.parse_args()
    D = {k: lade(getattr(a, k)) for k in ("e12", "m12", "e32", "m32")}
    ids = sorted(set.intersection(*(set(d) for d in D.values())))
    print(f"{len(ids)} gemeinsame Aufgaben")
    K = {k: kennz(d, ids) for k, d in D.items()}
    namen = {"e12": "ERGORE 12k", "m12": "MIT 12k", "e32": "ERGORE 32k", "m32": "MIT 32k"}
    for k, v in K.items():
        print(f"  {namen[k]:11s} {v}")
    vg = {}
    for x, y in (("e32", "m32"), ("e12", "m12"), ("e32", "e12"), ("m32", "m12")):
        A, B = D[x], D[y]
        nx = sum(bool(A[i]["korrekt"]) and not B[i]["korrekt"] for i in ids)
        ny = sum(bool(B[i]["korrekt"]) and not A[i]["korrekt"] for i in ids)
        vg[f"{namen[x]} gegen {namen[y]}"] = {"a": K[x]["richtig"], "b": K[y]["richtig"], "nur_a": nx, "nur_b": ny, "p": mcnemar(nx, ny)}
        print(f"  {namen[x]} gegen {namen[y]}: {K[x]['richtig']} gegen {K[y]['richtig']} | nur links {nx}, nur rechts {ny}, "
              f"McNemar p = {mcnemar(nx, ny):.4f}")
    artefakt = K["e32"]["richtig"] >= K["m32"]["richtig"] - 2 and K["e32"]["flur"] < 5
    print(f"URTEIL 1c: {'BUDGET-ARTEFAKT' if artefakt else 'Budget NICHT die Hauptursache'} (ERGORE 32k {K['e32']['richtig']} gegen "
          f"MIT 32k {K['m32']['richtig']}; leere Schließungen ERGORE 32k: {K['e32']['flur']})")
    json.dump({"kennzahlen": K, "vergleiche": vg, "budget_artefakt": artefakt}, open(a.aus, "w", encoding="utf-8"), indent=1,
              ensure_ascii=False)


if __name__ == "__main__":
    main()
