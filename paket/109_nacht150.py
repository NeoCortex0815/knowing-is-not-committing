"""(N30) Nachtlauf: Beratung im Vorderzimmer + eigenes Hinterzimmer auf 150 frischen MATH-Trainingsaufgaben
(08.11.; Lesart vorab in ANNAHMEN, öffentlich im Bericht v0.2 unter „Next steps“).
B+H: Mehrheit aus drei Intuitionen (Seeds 0/1/2, gleichwertig nach math-verify in beide Richtungen) → diese Antwort, sonst WT-A mit
Denken.
  (H1) gegen INT allein (Seed 0): „trägt“ bei ≥ +5, „widerlegt“ bei ≤ +1, sonst „offen“.
  (H2) gegen MIT allein: „schlägt MIT“ bei ≥ +5 UND McNemar einseitig p < 0,05; „mindestens gleichauf“ bei ≥ 0; „unter MIT“ bei ≤ −5;
       sonst „offen“.
  (H3) Einigkeit zweier Intuitionen (0/1): „hält“ bei Präzision ≥ 85 %, „widerlegt“ bei < 75 %.
  (H4) Mehrheit aus drei: „trägt“ bei Präzision ≥ 85 % UND Abdeckung ≥ Einigkeit aus zwei + 10 Punkte; „trägt nicht“ bei < 80 %.
Beschreibend: Mehrheit + MIT-Hinterzimmer; Einstimmigkeit; Tokens je richtiger Antwort; Sonde als Schiedsrichterin (falls Zustände).
  python 109_nacht150.py            → Urteile erst, wenn alle fünf Läufe vollständig sind (keine Zwischenblicke)
"""
import importlib.util
import json
import os
import sys
from math import comb

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(HIER)
ERG = os.path.join(WURZEL, "ergebnisse")
N = 150
INT = {s: f"nacht150-int-eigen-s{s}" for s in (0, 1, 2)}
WTA, MIT = "nacht150-wta", "nacht150-mit"


def laufe(d):
    R = {}
    p = os.path.join(ERG, d, "ergebnisse.jsonl")
    if os.path.exists(p):
        for z in open(p, encoding="utf-8"):
            r = json.loads(z)
            R[r["id"]] = r
    return R


def mcnemar_einseitig(b, c):
    """P(X ≥ b) bei X ~ Bin(b + c, 1/2): b = nur B+H richtig, c = nur MIT richtig."""
    n = b + c
    return 1.0 if n == 0 else sum(comb(n, i) for i in range(b, n + 1)) / 2 ** n


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    L = {s: laufe(d) for s, d in INT.items()}
    W, M = laufe(WTA), laufe(MIT)
    stand = {f"INT s{s}": len(L[s]) for s in L} | {"WT-A": len(W), "MIT": len(M)}
    print("Stand: " + ", ".join(f"{k} {v}/{N}" for k, v in stand.items()))
    if min(stand.values()) < N:
        print("noch nicht vollständig – keine Urteile")
        return
    s = importlib.util.spec_from_file_location("ev", os.path.join(WURZEL, "eval", "03_eval.py"))
    ev = importlib.util.module_from_spec(s)
    s.loader.exec_module(ev)
    ids = sorted(set(L[0]) & set(L[1]) & set(L[2]) & set(W) & set(M))

    def gl(a, b):
        return a["pred"] is not None and b["pred"] is not None and (ev.korrekt(a["pred"], b["pred"]) or ev.korrekt(b["pred"], a["pred"]))

    def mehrheit(i):
        r = [L[0][i], L[1][i], L[2][i]]
        for a, b in ((0, 1), (0, 2), (1, 2)):
            if gl(r[a], r[b]):
                return r[a]
        return None
    mh = {i: mehrheit(i) for i in ids}
    bh = {i: (mh[i] if mh[i] is not None else W[i]) for i in ids}
    bm = {i: (mh[i] if mh[i] is not None else M[i]) for i in ids}
    k = lambda D: sum(D[i]["korrekt"] for i in ids)
    r_bh, r_int, r_mit, r_wta, r_bm = k(bh), k(L[0]), k(M), k(W), k(bm)
    print(f"\nrichtig von {len(ids)}: B+H {r_bh} | INT Seed 0 {r_int} (Seeds 1/2: {k(L[1])}/{k(L[2])}) | MIT {r_mit} | WT-A {r_wta} | "
          f"Mehrheit + MIT-Hinterzimmer {r_bm}")
    d1 = r_bh - r_int
    u1 = "trägt" if d1 >= 5 else ("widerlegt" if d1 <= 1 else "offen")
    b = sum(1 for i in ids if bh[i]["korrekt"] and not M[i]["korrekt"])
    c = sum(1 for i in ids if M[i]["korrekt"] and not bh[i]["korrekt"])
    p = mcnemar_einseitig(b, c)
    d2 = r_bh - r_mit
    u2 = ("schlägt MIT" if (d2 >= 5 and p < 0.05) else ("mindestens gleichauf" if d2 >= 0 else ("unter MIT" if d2 <= -5 else "offen")))
    G2 = [i for i in ids if gl(L[0][i], L[1][i])]
    p3 = sum(L[0][i]["korrekt"] for i in G2) / max(1, len(G2))
    u3 = "hält" if p3 >= 0.85 else ("widerlegt" if p3 < 0.75 else "offen")
    G3 = [i for i in ids if mh[i] is not None]
    p4 = sum(mh[i]["korrekt"] for i in G3) / max(1, len(G3))
    abd2, abd3 = len(G2) / len(ids), len(G3) / len(ids)
    u4 = "trägt" if (p4 >= 0.85 and abd3 >= abd2 + 0.10) else ("trägt nicht" if p4 < 0.80 else "offen")
    print(f"URTEIL N30 H1 (B+H gegen INT): {r_bh} gegen {r_int} ({d1:+d}) → {u1}")
    print(f"URTEIL N30 H2 (B+H gegen MIT): {r_bh} gegen {r_mit} ({d2:+d}); nur B+H {b}, nur MIT {c}, McNemar einseitig p = {p:.4f} → {u2}")
    print(f"URTEIL N30 H3 (Einigkeit 0/1): {len(G2)} einig, Präzision {100 * p3:.0f} % → {u3}")
    print(f"URTEIL N30 H4 (Mehrheit aus drei): {len(G3)} Abgaben ({100 * abd3:.0f} % gegen {100 * abd2:.0f} %), Präzision {100 * p4:.0f} % → {u4}")
    E3 = [i for i in ids if gl(L[0][i], L[1][i]) and gl(L[0][i], L[2][i])]
    print(f"\nbeschreibend: einstimmig {len(E3)}, richtig {sum(L[0][i]['korrekt'] for i in E3)}")

    def tok(D, extra=None):
        return sum(D[i]["tokens"] for i in ids) + (extra or 0)
    t_int3 = sum(L[s][i]["tokens"] for s in L for i in ids)
    t_bh = t_int3 + sum(W[i]["tokens"] for i in ids if mh[i] is None)
    print(f"Tokens je richtiger Antwort: B+H {t_bh / max(1, r_bh):.0f} | INT {tok(L[0]) / max(1, r_int):.0f} | MIT {tok(M) / max(1, r_mit):.0f} | "
          f"WT-A {tok(W) / max(1, r_wta):.0f}")
    json.dump({"B+H": r_bh, "INT": r_int, "MIT": r_mit, "WT-A": r_wta, "B+MIT": r_bm, "H1": u1, "H2": [u2, p], "H3": [u3, p3],
               "H4": [u4, p4, abd3, abd2]}, open(os.path.join(ERG, "nacht150.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
