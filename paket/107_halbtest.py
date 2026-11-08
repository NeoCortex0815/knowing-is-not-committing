"""(N26) Halber Test auf unberührten Aufgaben MATH-500 301–370 (08.11.; Lesart vorab in ANNAHMEN 15:02, Aufteilung 15:0x).
(a) Zweifach-Intuition wie N20; (b) eingefrorene Vorderzimmer-Sonde wie N24 (103 --bestaetigen); (c) gekoppelte Regel gegen die
Längen-Regel: abgeben, wenn beide Seeds gleich ODER (Seed 0 ≤ 2.000 Tokens UND Sonde(Seed 0) ≥ 0,0524), sonst „weiß ich nicht“.
  python 107_halbtest.py
"""
import importlib.util
import json
import os
import sys

import numpy as np

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(HIER)
ERG = os.path.join(WURZEL, "ergebnisse")
S0 = ["ht-int-eigen-301-328-s0", "ht-int-eigen-329-355-s0", "ht-int-eigen-356-370-s0"]
S1 = ["ht-int-eigen-301-328-s1", "ht-int-eigen-329-355-s1", "ht-int-eigen-356-370-s1"]
SCHWELLE = 0.0524


def lade_mod(name, pfad):
    s = importlib.util.spec_from_file_location(name, pfad)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


def laufe(dirs):
    R = {}
    for d in dirs:
        p = os.path.join(ERG, d, "ergebnisse.jsonl")
        if os.path.exists(p):
            for z in open(p, encoding="utf-8"):
                r = json.loads(z)
                R[r["id"]] = r
    return R


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ev = lade_mod("ev", os.path.join(WURZEL, "eval", "03_eval.py"))
    m = lade_mod("m", os.path.join(HIER, "103_vorderzimmer_sonde.py"))
    A, C = laufe(S0), laufe(S1)
    ids = sorted(set(A) & set(C))
    print(f"Paare {len(ids)} von 70 | INT Seed 0 richtig {sum(A[i]['korrekt'] for i in ids)}, Seed 1 {sum(C[i]['korrekt'] for i in ids)}")
    if len(ids) < 70:
        print("noch nicht vollständig – kein Urteil")
        return

    def gleich(i):
        pa, pc = A[i]["pred"], C[i]["pred"]
        return pa is not None and pc is not None and (ev.korrekt(pa, pc) or ev.korrekt(pc, pa))
    G = [i for i in ids if gleich(i)]
    V = [i for i in ids if i not in G]
    pg = 100 * sum(A[i]["korrekt"] for i in G) / max(1, len(G))
    pv = 100 * sum(A[i]["korrekt"] for i in V) / max(1, len(V))
    ua = "trägt" if (pg - pv >= 30 and pg >= 70) else ("widerlegt" if pg - pv <= 15 else "offen")
    print(f"\n(a) Zweifach-Intuition: gleich {len(G)} (richtig {pg:.0f} %) | verschieden {len(V)} (Seed 0 richtig {pv:.0f} %) | "
          f"Δ {pg - pv:+.0f} Punkte → URTEIL N26 (a): {ua}")
    print("\n(b) Vorderzimmer-Sonde, eingefroren:")
    m.bestaetigen("N26b", S0 + S1)
    # (c) gekoppelte Regel
    st = m.stufen()
    D = m.verbinden([m.lade_satz(d, st) for d in S0])
    F = np.load(os.path.join(ERG, "vorderzimmer_sonde_eingefroren.npz"))
    k = m.SCHICHTEN.index(int(F["schicht"]))
    sonde = dict(zip(D["ids"], ((D["X"][:, k] - F["mu"]) / F["sd"]) @ F["w"] + F["b"]))
    n = len(ids)

    def bewerte(regel):
        ab = [i for i in ids if regel(i)]
        r = sum(A[i]["korrekt"] for i in ab)
        f = sum(1 for i in ab if not A[i]["korrekt"])
        return len(ab), r, f, (r - 2 * f) / n
    regeln = {"immer (INT allein)": lambda i: A[i]["pred"] is not None,
              "Länge (≤ 2.000)": lambda i: A[i]["tokens"] <= 2000,
              "Einigkeit allein": gleich,
              "Sonde allein (schnell + ≥ Median)": lambda i: A[i]["tokens"] <= 2000 and sonde.get(i, -9) >= SCHWELLE,
              "Kette (Einigkeit ODER Sonde)": lambda i: gleich(i) or (A[i]["tokens"] <= 2000 and sonde.get(i, -9) >= SCHWELLE)}
    print("\n(c) Abgabe-Regeln (sonst „weiß ich nicht“), S₂ = (richtig − 2·falsch)/70:")
    E = {}
    for nm, rg in regeln.items():
        E[nm] = bewerte(rg)
        a_, r_, f_, s2 = E[nm]
        print(f"   {nm:34s}: abgegeben {a_:2d}, richtig {r_:2d} ({100 * r_ / max(1, a_):3.0f} %), falsch {f_:2d} | S₂ {s2:+.3f}")
    _, rk, fk, sk = E["Kette (Einigkeit ODER Sonde)"]
    sl = E["Länge (≤ 2.000)"][3]
    prae = rk / max(1, rk + fk)
    uc = "Kette trägt" if (sk >= sl + 0.05 and prae >= 0.80) else ("trägt nicht" if sk <= sl else "offen")
    print(f"URTEIL N26 (c): S₂ Kette {sk:+.3f} gegen Länge {sl:+.3f}, Präzision {100 * prae:.0f} % → {uc}")
    n29(ev, m, A, C, E)
    n28(ev, A, C)
    json.dump({"a": [len(G), pg, pv, ua], "c": {k_: list(v) for k_, v in E.items()}, "urteil_c": uc},
              open(os.path.join(ERG, "halbtest.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)


def n28(ev, A, C):
    """(N28, Lesart 15:40): einig → INT Seed 0, sonst MIT mit Denken. Hält bei (i) Gesamt ≥ MIT allein UND (ii) Präzision der
    Einigkeits-Abgaben ≥ 90 % UND (iii) Tokens je richtiger < MIT allein; widerlegt, wenn (i) oder (ii) verfehlt; sonst offen."""
    M = laufe(["ht-mit-301-328", "ht-mit-329-355", "ht-mit-356-370"])
    ids = sorted(set(A) & set(C) & set(M))
    print()
    print(f"(N28) gekoppelte Regel mit MIT-Hinterzimmer: {len(ids)} von 70 Aufgaben mit allen drei Läufen")
    if len(ids) < 70:
        print("   noch nicht vollständig – kein Urteil")
        return
    g = [i for i in ids if A[i]["pred"] is not None and C[i]["pred"] is not None
         and (ev.korrekt(A[i]["pred"], C[i]["pred"]) or ev.korrekt(C[i]["pred"], A[i]["pred"]))]
    r = [i for i in ids if i not in g]
    k = lambda R, L: sum(R[i]["korrekt"] for i in L)
    regel = k(A, g) + k(M, r)
    mit = k(M, ids)
    prae = k(A, g) / max(1, len(g))
    tok_regel = (sum(A[i]["tokens"] + C[i]["tokens"] for i in ids) + sum(M[i]["tokens"] for i in r)) / max(1, regel)
    tok_mit = sum(M[i]["tokens"] for i in ids) / max(1, mit)
    i_, ii, iii = regel >= mit, prae >= 0.90, tok_regel < tok_mit
    urteil = "hält" if (i_ and ii and iii) else ("widerlegt" if not (i_ and ii) else "offen")
    print(f"   Zerlegung: Einigkeit n {len(g)}: INT {k(A, g)}, MIT {k(M, g)} | Rest n {len(r)}: INT {k(A, r)}, MIT {k(M, r)}")
    print(f"   Regel {regel} gegen MIT allein {mit} (INT allein {k(A, ids)}) | Präzision Einigkeit {100 * prae:.0f} % | "
          f"Tokens je richtiger {tok_regel:.0f} gegen MIT {tok_mit:.0f}")
    print(f"URTEIL N28 (vorab): (i) {'ja' if i_ else 'nein'}, (ii) {'ja' if ii else 'nein'}, (iii) {'ja' if iii else 'nein'} → {urteil}")


def n29(ev, m, A, C, E):
    """(N29, Lesart vorab): Sonde als Schiedsrichter bei Uneinigkeit; kein Nachteil in der Kette."""
    st = m.stufen()
    F = np.load(os.path.join(ERG, "vorderzimmer_sonde_eingefroren.npz"))
    k = m.SCHICHTEN.index(int(F["schicht"]))

    def werte(saetze):
        D = m.verbinden([m.lade_satz(d, st) for d in saetze])
        return dict(zip(D["ids"], ((D["X"][:, k] - F["mu"]) / F["sd"]) @ F["w"] + F["b"])) if D else {}
    s0, s1 = werte(S0), werte(S1)
    ids = sorted(set(A) & set(C))

    def gleich(i):
        pa, pc = A[i]["pred"], C[i]["pred"]
        return pa is not None and pc is not None and (ev.korrekt(pa, pc) or ev.korrekt(pc, pa))
    U = [i for i in ids if not gleich(i) and A[i]["pred"] is not None and C[i]["pred"] is not None and i in s0 and i in s1]
    sonde = sum((A[i] if s0[i] >= s1[i] else C[i])["korrekt"] for i in U)
    seed0 = sum(A[i]["korrekt"] for i in U)
    kurz = sum((A[i] if A[i]["tokens"] <= C[i]["tokens"] else C[i])["korrekt"] for i in U)
    beide = sum(1 for i in U if A[i]["korrekt"] or C[i]["korrekt"])
    ua = "Mehrwert" if (sonde >= seed0 + 3 and sonde >= kurz + 2) else ("kein Mehrwert" if sonde <= seed0 else "offen")
    print()
    print(f"(N29 a) Schiedsrichter auf {len(U)} uneinigen Aufgaben (beide mit Antwort; eine der beiden richtig: {beide}): "
          f"Sonde {sonde} | Seed 0 {seed0} | kürzere {kurz} → URTEIL: {ua}")
    s2_k, s2_e = E["Kette (Einigkeit ODER Sonde)"][3], E["Einigkeit allein"][3]
    ub = "kein Nachteil" if s2_k >= s2_e else "Nachteil"
    print(f"(N29 b) S₂ Kette {s2_k:+.3f} gegen Einigkeit allein {s2_e:+.3f} → URTEIL: {ub}")
    G = [i for i in ids if gleich(i)]
    W = [i for i in U if max(s0[i], s1[i]) >= SCHWELLE]
    r = sum(A[i]["korrekt"] for i in G) + sum((A[i] if s0[i] >= s1[i] else C[i])["korrekt"] for i in W)
    f = (len(G) - sum(A[i]["korrekt"] for i in G)) + (len(W) - sum((A[i] if s0[i] >= s1[i] else C[i])["korrekt"] for i in W))
    print(f"   beschreibend: einig → abgeben, uneinig → Sonden-Wahl wenn ≥ Median: abgegeben {len(G) + len(W)}, richtig {r}, "
          f"falsch {f}, S₂ {(r - 2 * f) / len(ids):+.3f}")

if __name__ == "__main__":
    main()
