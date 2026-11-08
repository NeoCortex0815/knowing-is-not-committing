"""(N8) INT auf frischen Aufgaben: eigen OHNE Denken gegen MIT MIT Denken auf MATH-500 161–300 (Lesart vorab in ANNAHMEN).
„INT hält auf frischen Aufgaben“ bei ≥ MIT − 7 (≥ 73/140); „widerlegt“ bei ≤ MIT − 14 (≤ 66/140); sonst „offen“.
Beschreibend: gegen WT-A und ERGORE; je Block; Tokens; strenge Wertung (nur reguläres Ende).
  python 94_int_frisch.py
"""
import json
import os
from math import comb

ERG = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ergebnisse")
INT = ["s3-int-eigen-161-210", "s3-int-eigen-211-260", "s3-int-eigen-261-300"]
VGL = {"MIT": ["s3-mit-161-260", "s3-mit-261-300"], "WT-A": ["s3-wta-161-210", "s3-wta-211-260", "s3-wta-261-300"],
       "ERGORE": ["s3-ergore-161-260", "s3-ergore-261-300"]}


def laufe(dirs):
    R = {}
    for d in dirs:
        p = os.path.join(ERG, d, "ergebnisse.jsonl")
        if os.path.exists(p):
            for z in open(p, encoding="utf-8"):
                r = json.loads(z)
                R[r["id"]] = r
    return R


def mcnemar(b, c):
    n = b + c
    return 1.0 if n == 0 else min(1.0, 2 * sum(comb(n, i) for i in range(min(b, c) + 1)) / 2 ** n)


def main():
    I = laufe(INT)
    print(f"INT-Läufe: {len(I)} von 140 | richtig {sum(r['korrekt'] for r in I.values())} | streng (nur eos) "
          f"{sum(1 for r in I.values() if r['korrekt'] and r['ende'] == 'eos')} | Ø Tokens {sum(r['tokens'] for r in I.values()) / max(1, len(I)):.0f}")
    B = {"n": len(I)}
    for name, dirs in VGL.items():
        V = laufe(dirs)
        ids = sorted(set(I) & set(V))
        b = sum(1 for i in ids if I[i]["korrekt"] and not V[i]["korrekt"])
        c = sum(1 for i in ids if not I[i]["korrekt"] and V[i]["korrekt"])
        ri, rv = sum(I[i]["korrekt"] for i in ids), sum(V[i]["korrekt"] for i in ids)
        beide = [i for i in ids if I[i]["korrekt"] and V[i]["korrekt"]]
        ti = sum(I[i]["tokens"] for i in beide) / max(1, len(beide))
        tv = sum(V[i]["tokens"] for i in beide) / max(1, len(beide))
        print(f"INT {ri} gegen {name} {rv} von {len(ids)} | nur INT {b}, nur {name} {c}, p = {mcnemar(b, c):.4f} | "
              f"Tokens auf gemeinsam gelösten ({len(beide)}): INT {ti:.0f}, {name} {tv:.0f}")
        B[name] = {"n": len(ids), "int": ri, name: rv, "nur_int": b, "nur_vgl": c, "p": mcnemar(b, c)}
        for blk, lo, hi in (("161–260", 160, 260), ("261–300", 260, 300)):
            pass
    M = laufe(VGL["MIT"])
    ids = sorted(set(I) & set(M))
    if len(ids) == 140:
        ri, rm = sum(I[i]["korrekt"] for i in ids), sum(M[i]["korrekt"] for i in ids)
        urteil = "HÄLT" if ri >= rm - 7 else ("WIDERLEGT" if ri <= rm - 14 else "offen")
        print(f"URTEIL N8 (vorab): INT {ri} gegen MIT {rm} → {urteil}")
        B["urteil_N8"] = {"int": ri, "mit": rm, "urteil": urteil}
    else:
        print("URTEIL N8: noch nicht alle 140 Aufgaben")
    json.dump(B, open(os.path.join(ERG, "int_frisch.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
