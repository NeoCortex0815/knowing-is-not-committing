"""Meilenstein-Urteil auf 80 MATH-500-Aufgaben (06.11. ~10:30; Meilenstein-Regel des Nutzers: Kandidat + MIT-Edit auf 40 weiteren
Aufgaben, Vergleich je Aufgabe). VORAB FESTGELEGTE Lesart (vor den Ergebnissen 41–80):
  geknackt          – kw75 > MIT auf 80 und gepaarter McNemar-Test p < 0,05
  MIT-Niveau erreicht – kw75 ≥ MIT − 2 auf 80 und MIT NICHT signifikant besser (p ≥ 0,05)
  nicht erreicht    – sonst
Teil 1 = Aufgaben 1–40, Teil 2 = 41–80. Fehlende Teile werden gemeldet (dann nur Teilurteil).
  python 40_urteil80.py
"""
import json
import math
import os
from math import comb

HIER = os.path.dirname(os.path.abspath(__file__))
ERG = os.path.join(os.path.dirname(HIER), "ergebnisse")
LAEUFE = {"kw75": ("tag2-test40-kw75", "kw75-b"), "MIT": ("mit-vstil-L", "mit-vstil-L-b"), "eigen": ("eigen-vL", "eigen-vL-b")}


def lade(d):
    p = os.path.join(ERG, d, "ergebnisse.jsonl")
    if not os.path.exists(p):
        return None
    return {json.loads(z)["id"]: bool(json.loads(z)["korrekt"]) for z in open(p, encoding="utf-8")}


def mcnemar(a, b):
    n = a + b
    return min(1.0, 2 * sum(comb(n, x) for x in range(0, min(a, b) + 1)) / 2 ** n) if n else 1.0


def wilson(k, n, z=1.96):
    if not n:
        return (0.0, 0.0)
    p = k / n
    m = (p + z * z / (2 * n)) / (1 + z * z / n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return (m - h, m + h)


def main():
    daten = {}
    for name, teile in LAEUFE.items():
        d = {}
        for i, t in enumerate(teile):
            x = lade(t)
            print(f"{name:6s} Teil {i + 1} ({t}): {'fehlt' if x is None else f'{sum(x.values())}/{len(x)}'}")
            if x:
                d.update(x)
        daten[name] = d
    # Urteil kw75 gegen MIT braucht nur diese beiden (eigen ist Vergleichsbasis und darf später fertig werden)
    gemeinsam = set(daten["kw75"]) & set(daten["MIT"])
    if daten["eigen"] and set(daten["eigen"]) >= gemeinsam:
        print("(eigen liegt für alle gemeinsamen Aufgaben vor)")
    else:
        print("(eigen fehlt für einen Teil – eigen-Vergleiche nur auf den Aufgaben mit eigen)")
    n = len(gemeinsam)
    print(f"\nGemeinsame Aufgaben: {n}")
    for name in LAEUFE:
        ids = [i for i in gemeinsam if i in daten[name]]
        k = sum(daten[name][i] for i in ids)
        lo, hi = wilson(k, len(ids))
        print(f"  {name:6s} {k}/{len(ids)} = {100 * k / max(len(ids), 1):.1f} %  (95 %-Wilson {100 * lo:.0f}–{100 * hi:.0f} %)")
    for x, y in (("kw75", "MIT"), ("kw75", "eigen"), ("MIT", "eigen")):
        ids = [i for i in gemeinsam if i in daten[x] and i in daten[y]]
        a = sum(daten[x][i] and not daten[y][i] for i in ids)
        b = sum(daten[y][i] and not daten[x][i] for i in ids)
        print(f"  {x} gegen {y} ({len(ids)} Aufgaben): nur {x} {a}, nur {y} {b}, McNemar p = {mcnemar(a, b):.4f}")
    kk = sum(daten["kw75"][i] for i in gemeinsam)
    km = sum(daten["MIT"][i] for i in gemeinsam)
    a = sum(daten["kw75"][i] and not daten["MIT"][i] for i in gemeinsam)
    b = sum(daten["MIT"][i] and not daten["kw75"][i] for i in gemeinsam)
    p = mcnemar(a, b)
    if n < 80:
        print(f"\nTEILURTEIL (nur {n} Aufgaben) – Meilenstein-Urteil braucht 80.")
    if kk > km and p < 0.05:
        urteil = "GEKNACKT – kw75 signifikant besser als MIT"
    elif kk >= km - 2 and not (km > kk and p < 0.05):
        urteil = "MIT-NIVEAU ERREICHT – kw75 gleichauf (MIT nicht signifikant besser)"
    else:
        urteil = "NICHT ERREICHT"
    print(f"URTEIL ({n} Aufgaben): {urteil}  [kw75 {kk} gegen MIT {km}]")


if __name__ == "__main__":
    main()
