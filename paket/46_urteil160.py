"""Urteil ERGORE gegen MIT auf frischen Testaufgaben 81–160 und auf 1–160 zusammen (06.11. ~15:58; Nutzer: „jap gerne
veranlassen“). VORAB FESTGELEGTE Lesart, gleich wie 40_urteil80.py:
  geknackt            – ERGORE > MIT und gepaarter McNemar-Test p < 0,05
  MIT-Niveau erreicht – ERGORE ≥ MIT − 2,5 % der Aufgaben (80: −2, 160: −4) und MIT NICHT signifikant besser (p ≥ 0,05)
  nicht erreicht      – sonst
Dazu beschreibend: gepaarte Differenz mit 95-%-Intervall (Newcombe/Wald für gepaarte Anteile), Tokens.
  python 46_urteil160.py
"""
import json
import math
import os
from math import comb

HIER = os.path.dirname(os.path.abspath(__file__))
ERG = os.path.join(os.path.dirname(HIER), "ergebnisse")
TEILE = {"ERGORE": ("tag2-test40-kw75", "kw75-b", "kw75-c"), "MIT": ("mit-vstil-L", "mit-vstil-L-b", "mit-vstil-L-c")}


def lade(d):
    p = os.path.join(ERG, d, "ergebnisse.jsonl")
    if not os.path.exists(p):
        return None
    out = {}
    for z in open(p, encoding="utf-8"):
        r = json.loads(z)
        out[r["id"]] = (bool(r["korrekt"]), int(r.get("tokens") or len(r["gen_ids"])))
    return out


def mcnemar(a, b):
    n = a + b
    return min(1.0, 2 * sum(comb(n, x) for x in range(0, min(a, b) + 1)) / 2 ** n) if n else 1.0


def urteil(name, A, B):
    ids = sorted(set(A) & set(B))
    n = len(ids)
    a = sum(A[i][0] for i in ids)
    b = sum(B[i][0] for i in ids)
    x = sum(A[i][0] and not B[i][0] for i in ids)
    y = sum(B[i][0] and not A[i][0] for i in ids)
    p = mcnemar(x, y)
    d = (x - y) / n if n else 0.0
    se = math.sqrt(max(0.0, (x + y) / n - d * d) / n) if n else 0.0
    toleranz = math.floor(0.025 * n)
    if a > b and p < 0.05:
        u = "GEKNACKT – ERGORE signifikant über MIT"
    elif a >= b - toleranz and not (b > a and p < 0.05):
        u = "MIT-NIVEAU ERREICHT"
    else:
        u = "NICHT ERREICHT"
    tok_a = sum(A[i][1] for i in ids) / max(1, n)
    tok_b = sum(B[i][1] for i in ids) / max(1, n)
    print(f"== {name}: {n} gemeinsame Aufgaben | ERGORE {a} ({100 * a / max(1, n):.1f} %) gegen MIT {b} ({100 * b / max(1, n):.1f} %) | "
          f"nur ERGORE {x}, nur MIT {y}, McNemar p = {p:.4f}")
    print(f"   Differenz {100 * d:+.1f} Punkte, 95 % [{100 * (d - 1.96 * se):+.1f}; {100 * (d + 1.96 * se):+.1f}] | Ø Tokens ERGORE {tok_a:.0f}, "
          f"MIT {tok_b:.0f}")
    print(f"URTEIL {name}: {u}")
    return {"n": n, "ergore": a, "mit": b, "nur_ergore": x, "nur_mit": y, "p": p, "urteil": u}


def main():
    D = {m: [lade(t) for t in ts] for m, ts in TEILE.items()}
    for m, teile in D.items():
        for t, d in zip(TEILE[m], teile):
            print(f"{m:6s} {t:18s}: {'fehlt' if d is None else f'{sum(v[0] for v in d.values())}/{len(d)}'}")
    erg = {}
    if D["ERGORE"][2] is not None and D["MIT"][2] is not None:
        erg["81–160"] = urteil("Aufgaben 81–160 (frisch)", D["ERGORE"][2], D["MIT"][2])
    alle = {m: {k: v for d in teile if d is not None for k, v in d.items()} for m, teile in D.items()}
    erg["1–160"] = urteil(f"alle vorhandenen Aufgaben (1–{len(set(alle['ERGORE']) & set(alle['MIT']))})", alle["ERGORE"], alle["MIT"])
    json.dump(erg, open(os.path.join(ERG, "urteil160.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
