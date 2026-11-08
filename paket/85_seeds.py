"""(N5) Zweiter Seed auf Set B (vorab festgelegt 07.11. 15:25, Korrektur 15:37; beschreibend: Sampling-Streuung gegen
Modell-Unterschiede).
Blöcke: Laptop 1–30, MiniPC 31–60. MIT nur Seed 0, weil es auf Set B keinen MIT-Lauf bei 0,6 gab. ERGORE läuft ganz auf dem
Laptop (Seed 0 = setB-ergore-t06; Seed 1 = zwei Hälften).
Ausgabe je Modell:
  - Treffer Seed 0 und Seed 1;
  - Übereinstimmung je Aufgabe: beide richtig, nur s0, nur s1, keiner;
  - Tokens (Mittel).
Dazu Modellvergleiche je Seed (McNemar exakt).
  python 85_seeds.py → ergebnisse/seeds_setB.json
"""
import json
import os
from math import comb

HIER = os.path.dirname(os.path.abspath(__file__))
ERG = os.path.join(os.path.dirname(HIER), "ergebnisse")
SAETZE = {
    "MIT": {0: ["setB30-mit-t06", "minipc-b2-mit-t06"]},
    "eigen": {0: ["setB30-eigen-t06", "minipc-b2-eigen-t06"], 1: ["setB30-eigen-t06-s1", "minipc-b2-eigen-t06-s1"]},
    "WT-A": {0: ["setB30-wta-t06", "minipc-b2-wta-t06"], 1: ["setB30-wta-t06-s1", "minipc-b2-wta-t06-s1"]},
    "ERGORE": {0: ["setB-ergore-t06"], 1: ["setB-ergore-t06-s1-a", "setB-ergore-t06-s1-b"]},
}


def lade(dirs):
    R = {}
    for d in dirs:
        for z in open(os.path.join(ERG, d, "ergebnisse.jsonl"), encoding="utf-8"):
            r = json.loads(z)
            R[r["id"]] = r
    return R


def mcnemar(b, c):
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    return min(1.0, 2 * sum(comb(n, i) for i in range(k + 1)) / 2 ** n)


FRISCH = {  # 08.11. (N7/N6, beschreibend): frische Aufgaben, je Maschinen-Block getrennt
    "frischA": {"WT-A": {0: ["s3-wta-161-210", "s3-wta-211-260"], 1: ["s3-wta-161-210-s1", "s3-wta-211-260-s1"]},
                "MIT": {0: ["s3-mit-161-260"]}, "ERGORE": {0: ["s3-ergore-161-260"]}},
    "frischB": {"MIT": {0: ["s3-mit-261-300"], 1: ["s3-mit-261-300-s1"]}, "ERGORE": {0: ["s3-ergore-261-300"], 1: ["s3-ergore-261-300-s1"]},
                "WT-A": {0: ["s3-wta-261-300"]}},
}


def main():
    import sys
    global SAETZE
    satz = sys.argv[sys.argv.index("--satz") + 1] if "--satz" in sys.argv else "setB"
    if satz in FRISCH:
        SAETZE = FRISCH[satz]
    SAETZE = {m: {s: d for s, d in v.items() if all(os.path.exists(os.path.join(ERG, x, "ergebnisse.jsonl")) for x in d)}
              for m, v in SAETZE.items()}
    print(f"Satz {satz}: " + "; ".join(f"{m} Seeds {sorted(v)}" for m, v in SAETZE.items()))
    D = {m: {s: lade(d) for s, d in v.items()} for m, v in SAETZE.items()}
    B = {"modelle": {}, "vergleiche": {}}
    print(f"== Je Modell: Seed 0 gegen Seed 1 ({satz})")
    for m, S in D.items():
        e = {f"s{s}": {"n": len(R), "richtig": sum(r["korrekt"] for r in R.values()),
                       "tokens_mittel": round(sum(r["tokens"] for r in R.values()) / max(1, len(R)))} for s, R in S.items()}
        if 0 in S and 1 in S:
            ids = sorted(set(S[0]) & set(S[1]))
            a = sum(1 for i in ids if S[0][i]["korrekt"] and S[1][i]["korrekt"])
            b = sum(1 for i in ids if S[0][i]["korrekt"] and not S[1][i]["korrekt"])
            c = sum(1 for i in ids if not S[0][i]["korrekt"] and S[1][i]["korrekt"])
            d = len(ids) - a - b - c
            e["paar"] = {"n": len(ids), "beide": a, "nur_s0": b, "nur_s1": c, "keiner": d, "p": mcnemar(b, c),
                         "uebereinstimmung": (a + d) / max(1, len(ids))}
        B["modelle"][m] = e
        zeile = " | ".join(f"Seed {k[1]}: {v['richtig']}/{v['n']} (Ø {v['tokens_mittel']} Tokens)" for k, v in e.items() if k.startswith("s"))
        if "paar" in e:
            p = e["paar"]
            zeile += (f" | gepaart: beide {p['beide']}, nur s0 {p['nur_s0']}, nur s1 {p['nur_s1']}, keiner {p['keiner']}, "
                      f"p = {p['p']:.3f}, Übereinstimmung {100 * p['uebereinstimmung']:.0f} %")
        print(f"   {m:6s}: {zeile}")
    print("\n== Modellvergleiche je Seed (gepaart, McNemar exakt)")
    for (m1, m2) in (("WT-A", "eigen"), ("WT-A", "MIT"), ("WT-A", "ERGORE"), ("ERGORE", "MIT"), ("eigen", "MIT")):
        if m1 not in D or m2 not in D:
            continue
        for s in (0, 1):
            if s in D[m1] and s in D[m2]:
                ids = sorted(set(D[m1][s]) & set(D[m2][s]))
                b = sum(1 for i in ids if D[m1][s][i]["korrekt"] and not D[m2][s][i]["korrekt"])
                c = sum(1 for i in ids if not D[m1][s][i]["korrekt"] and D[m2][s][i]["korrekt"])
                r1 = sum(D[m1][s][i]["korrekt"] for i in ids)
                r2 = sum(D[m2][s][i]["korrekt"] for i in ids)
                B["vergleiche"][f"{m1}-{m2}-s{s}"] = {"n": len(ids), m1: r1, m2: r2, "nur1": b, "nur2": c, "p": mcnemar(b, c)}
                print(f"   Seed {s}: {m1} {r1} gegen {m2} {r2} von {len(ids)} | nur {m1} {b}, nur {m2} {c}, p = {mcnemar(b, c):.3f}")
    # Seed-übergreifend: Mittel aus beiden Seeds, wo vorhanden
    print("\n== Mittel über die Seeds (richtig von 60)")
    for m, S in D.items():
        werte = [sum(r["korrekt"] for r in R.values()) for R in S.values()]
        print(f"   {m:6s}: {' / '.join(str(w) for w in werte)} → Mittel {sum(werte) / len(werte):.1f}")
    json.dump(B, open(os.path.join(ERG, f"seeds_{satz}.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(f"gespeichert: {os.path.join(ERG, f'seeds_{satz}.json')}")


if __name__ == "__main__":
    main()
