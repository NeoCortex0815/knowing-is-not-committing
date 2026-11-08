"""(N13) MIT im Vorderzimmer: MIT OHNE Denken (offizielle Nicht-Denk-Vorlage, 03b) gegen MIT MIT Denken auf MATH-500 161–300,
Seed 0, gepaart (Lesart vorab in ANNAHMEN, 08.11. 10:48):
  „Das Hinterzimmer lohnt sich bei MIT“, wenn MIT mit Denken ≥ MIT ohne Denken + 7;
  „Auch bei MIT keine Hilfe“, wenn MIT ohne Denken ≥ MIT mit Denken − 2; sonst „offen“.
Beschreibend: gegen eigen ohne Denken (INT) und WT-A; je Block; Tokens; strenge Wertung (nur eos); Landkarte nach Fach und Stufe;
Obergrenze einer perfekten Zimmer-Wahl (nicht erreichbar, nur zur Einordnung).
  python 102_mit_int.py              → Urteil (erst bei allen 140 Aufgaben)
  python 102_mit_int.py --trocken    → nur prüfen, ob alles lädt (zeigt keine Treffer, keine Zwischenblicke)
"""
import collections
import json
import os
import sys
from math import comb

WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ERG = os.path.join(WURZEL, "ergebnisse")
MITINT = ["s3-mitint-161-210", "s3-mitint-211-260", "s3-mitint-261-300"]
VGL = {"MIT mit Denken": ["s3-mit-161-260", "s3-mit-261-300"],
       "INT (eigen ohne Denken)": ["s3-int-eigen-161-210", "s3-int-eigen-211-260", "s3-int-eigen-261-300"],
       "WT-A mit Denken": ["s3-wta-161-210", "s3-wta-211-260", "s3-wta-261-300"]}
BLOECKE = (("161–210", MITINT[0]), ("211–260", MITINT[1]), ("261–300", MITINT[2]))


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
    sys.stdout.reconfigure(encoding="utf-8")  # Pfeile und Gedankenstriche auch bei umgeleiteter Ausgabe (cp1252)
    M = laufe(MITINT)
    if "--trocken" in sys.argv:
        for blk, d in BLOECKE:
            print(f"{blk}: {len(laufe([d]))} Läufe")
        for name, dirs in VGL.items():
            print(f"{name}: {len(laufe(dirs))} Läufe")
        print(f"MIT ohne Denken gesamt: {len(M)} von 140")
        return
    if len(M) < 140:
        print(f"URTEIL N13: noch nicht alle 140 Aufgaben ({len(M)}) – keine Ausgabe vor dem Urteil")
        return
    stufe = {}
    for z in open(os.path.join(WURZEL, "daten", "math500.jsonl"), encoding="utf-8"):
        d = json.loads(z)
        stufe[d["unique_id"]] = int(d["level"])
    rm = sum(r["korrekt"] for r in M.values())
    tok = sum(r["tokens"] for r in M.values())
    print(f"MIT ohne Denken: {rm}/140 | streng (nur eos) {sum(1 for r in M.values() if r['korrekt'] and r['ende'] == 'eos')} | "
          f"Ende eos {sum(1 for r in M.values() if r['ende'] == 'eos')} | Ø Tokens {tok / 140:.0f} | Tokens je richtiger {tok / max(1, rm):.0f}")
    B = {"mit_ohne_denken": rm}
    for name, dirs in VGL.items():
        V = laufe(dirs)
        ids = sorted(set(M) & set(V))
        b = sum(1 for i in ids if M[i]["korrekt"] and not V[i]["korrekt"])
        c = sum(1 for i in ids if not M[i]["korrekt"] and V[i]["korrekt"])
        rv = sum(V[i]["korrekt"] for i in ids)
        beide = [i for i in ids if M[i]["korrekt"] and V[i]["korrekt"]]
        tv = sum(V[i]["tokens"] for i in ids)
        print(f"\n== gegen {name}: {rm} : {rv} von {len(ids)} | nur ohne Denken {b}, nur {name} {c}, McNemar p = {mcnemar(b, c):.4f}")
        print(f"   Tokens je richtiger: {tok / max(1, rm):.0f} gegen {tv / max(1, rv):.0f} | auf gemeinsam gelösten ({len(beide)}): "
              f"{sum(M[i]['tokens'] for i in beide) / max(1, len(beide)):.0f} gegen {sum(V[i]['tokens'] for i in beide) / max(1, len(beide)):.0f}")
        print(f"   Obergrenze perfekte Zimmer-Wahl (eines von beiden richtig): {sum(1 for i in ids if M[i]['korrekt'] or V[i]['korrekt'])}")
        bl = []
        for blk, d in BLOECKE:
            J = [i for i in laufe([d]) if i in V]
            bl.append(f"{blk} {sum(M[i]['korrekt'] for i in J)}:{sum(V[i]['korrekt'] for i in J)}")
        print("   je Block: " + " | ".join(bl))
        B[name] = {"n": len(ids), "vgl": rv, "nur_ohne": b, "nur_vgl": c, "p": mcnemar(b, c)}
        if name == "MIT mit Denken":
            fach = collections.defaultdict(lambda: [0, 0, 0])
            st = collections.defaultdict(lambda: [0, 0, 0])
            for i in ids:
                f = i.split("/")[1]
                for D, k in ((fach, f), (st, stufe.get(i, 0))):
                    D[k][0] += 1
                    D[k][1] += M[i]["korrekt"]
                    D[k][2] += V[i]["korrekt"]
            print("   Landkarte (n | ohne Denken : mit Denken):")
            print("     " + " | ".join(f"{k} {v[0]}: {v[1]}:{v[2]}" for k, v in sorted(fach.items())))
            print("     " + " | ".join(f"Stufe {k} {v[0]}: {v[1]}:{v[2]}" for k, v in sorted(st.items())))
            urteil = ("Das Hinterzimmer lohnt sich bei MIT" if rv >= rm + 7 else
                      ("Auch bei MIT keine Hilfe" if rm >= rv - 2 else "offen"))
            B["urteil_N13"] = {"ohne": rm, "mit": rv, "urteil": urteil}
    print(f"\nURTEIL N13 (vorab): MIT ohne Denken {rm} gegen MIT mit Denken {B['urteil_N13']['mit']} → {B['urteil_N13']['urteil']}")
    json.dump(B, open(os.path.join(ERG, "mit_int.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
