"""(N27) Dritte Intuition: „Mehrheit aus drei“ (08.11.; Lesart vorab in ANNAHMEN, Zusatz 15:40).
Abgeben, wenn mindestens zwei der drei Seeds (0, 1, 2) gleichwertige Antworten geben, sonst „weiß ich nicht“.
Vergleich „Einigkeit aus zwei“ (Seeds 0/1, N20: 38 abgegeben, 37 richtig).
„trägt“ bei ≥ 48 Abgaben UND ≥ 90 % richtig; „trägt nicht“ bei < 85 % richtig ODER < 43 Abgaben; sonst „offen“.
Zweite Lesart: S₂ = (richtig − 2·falsch)/100 der Mehrheit ≥ S₂ der Einigkeit aus zwei.
  python 108_drei_intuitionen.py
"""
import importlib.util
import json
import os
import sys

WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ERG = os.path.join(WURZEL, "ergebnisse")
SEEDS = {0: ["s3-int-eigen-161-210", "s3-int-eigen-211-260"],
         1: ["s3-int-eigen-161-185-s1", "s3-int-eigen-186-210-s1", "s3-int-eigen-211-260-s1"],
         2: ["s3-int-eigen-161-195-s2", "s3-int-eigen-196-230-s2", "s3-int-eigen-231-260-s2"]}
HINTER = {"MIT": ["s3-mit-161-260"], "WT-A": ["s3-wta-161-210", "s3-wta-211-260"]}


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
    s = importlib.util.spec_from_file_location("ev", os.path.join(WURZEL, "eval", "03_eval.py"))
    ev = importlib.util.module_from_spec(s)
    s.loader.exec_module(ev)
    L = {k: laufe(v) for k, v in SEEDS.items()}
    ids = sorted(set(L[0]) & set(L[1]) & set(L[2]))
    print(f"Aufgaben mit drei Seeds: {len(ids)} von 100 | richtig je Seed: " + ", ".join(f"S{k} {sum(L[k][i]['korrekt'] for i in ids)}" for k in L))
    if len(ids) < 100:
        print("noch nicht vollständig – kein Urteil")
        return

    def gl(a, b):
        return a["pred"] is not None and b["pred"] is not None and (ev.korrekt(a["pred"], b["pred"]) or ev.korrekt(b["pred"], a["pred"]))

    def mehrheit(i):
        r = [L[0][i], L[1][i], L[2][i]]
        for a, b in ((0, 1), (0, 2), (1, 2)):
            if gl(r[a], r[b]):
                return r[a]
        return None

    def zwei(i):
        return L[0][i] if gl(L[0][i], L[1][i]) else None

    def einstimmig(i):
        r = [L[0][i], L[1][i], L[2][i]]
        return r[0] if gl(r[0], r[1]) and gl(r[0], r[2]) else None
    B = {}
    for nm, f in (("Einigkeit aus zwei (0/1)", zwei), ("Mehrheit aus drei", mehrheit), ("Einstimmig aus drei", einstimmig)):
        ab = [i for i in ids if f(i) is not None]
        r = sum(f(i)["korrekt"] for i in ab)
        fa = len(ab) - r
        B[nm] = (len(ab), r, fa, (r - 2 * fa) / len(ids))
        print(f"   {nm:26s}: abgegeben {len(ab):3d}, richtig {r:3d} ({100 * r / max(1, len(ab)):3.0f} %), falsch {fa:2d} | S₂ {B[nm][3]:+.3f}")
    for a, b in ((0, 2), (1, 2)):
        G = [i for i in ids if gl(L[a][i], L[b][i])]
        print(f"   Paar {a}/{b} beschreibend: einig {len(G)}, richtig {sum(L[a][i]['korrekt'] for i in G)}")
    n, r, fa, s2 = B["Mehrheit aus drei"]
    p = r / max(1, n)
    u1 = "trägt" if (n >= 48 and p >= 0.90) else ("trägt nicht" if (p < 0.85 or n < 43) else "offen")
    u2 = "erfüllt" if s2 >= B["Einigkeit aus zwei (0/1)"][3] else "nicht erfüllt"
    print(f"URTEIL N27 (vorab): {n} Abgaben, {100 * p:.0f} % richtig → {u1}; zweite Lesart S₂ {s2:+.3f} gegen "
          f"{B['Einigkeit aus zwei (0/1)'][3]:+.3f} → {u2}")
    for hn, d in HINTER.items():
        H = laufe(d)
        if all(i in H for i in ids):
            rw = sum(mehrheit(i)["korrekt"] if mehrheit(i) is not None else H[i]["korrekt"] for i in ids)
            print(f"   beschreibend Weiche Mehrheit → sonst {hn}: {rw} (allein {sum(H[i]['korrekt'] for i in ids)})")
    json.dump({k: list(v) for k, v in B.items()} | {"urteil": u1, "zweite": u2},
              open(os.path.join(ERG, "drei_intuitionen.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
