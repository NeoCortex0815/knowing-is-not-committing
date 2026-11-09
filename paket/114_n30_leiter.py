"""(N30, nachträglich, BESCHREIBEND) Vertrauensleiter des Vorderzimmers, 09.11.2026 nach dem gemeinsamen Lesen.

Zerlegt die 150 Aufgaben von N30 nach der Einigkeit der drei Intuitionen (Seeds 0/1/2; gleichwertig = math-verify in beide
Richtungen, genau wie in 109_nacht150.py):
  einstimmig      alle drei gleichwertig
  zwei gegen eine mindestens ein Paar gleichwertig, aber nicht alle drei
  keine Mehrheit  kein Paar gleichwertig (B+H nimmt dann WT-A mit Denken)
Je Stufe: Anzahl, richtig nach B+H, richtig für INT Seed 0 allein, MIT allein. Keine Lesart, kein Urteil; nachträglich gefunden.
  python 114_n30_leiter.py   → ergebnisse/n30_leiter.json
"""
import importlib.util
import json
import os
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(HIER)
ERG = os.path.join(WURZEL, "ergebnisse")
INT = {s: f"nacht150-int-eigen-s{s}" for s in (0, 1, 2)}
WTA, MIT = "nacht150-wta", "nacht150-mit"


def laufe(d):
    return {r["id"]: r for r in (json.loads(z) for z in open(os.path.join(ERG, d, "ergebnisse.jsonl"), encoding="utf-8"))}


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    s = importlib.util.spec_from_file_location("ev", os.path.join(WURZEL, "eval", "03_eval.py"))
    ev = importlib.util.module_from_spec(s)
    s.loader.exec_module(ev)
    if getattr(ev, "mv_parse", None) is None:
        sys.exit("math-verify fehlt: ohne es vergleicht 03_eval.py nur Text und findet weniger Einigkeiten. Bitte venv-Python nehmen.")
    L = {k: laufe(d) for k, d in INT.items()}
    W, M = laufe(WTA), laufe(MIT)
    ids = sorted(set(L[0]) & set(L[1]) & set(L[2]) & set(W) & set(M))

    def gl(a, b):
        return a["pred"] is not None and b["pred"] is not None and (ev.korrekt(a["pred"], b["pred"]) or ev.korrekt(b["pred"], a["pred"]))

    stufen = {"einstimmig": [], "zwei gegen eine": [], "keine Mehrheit": []}
    bh = {}
    for i in ids:
        r = [L[0][i], L[1][i], L[2][i]]
        paare = [(a, b) for a, b in ((0, 1), (0, 2), (1, 2)) if gl(r[a], r[b])]
        if gl(r[0], r[1]) and gl(r[0], r[2]):
            stufen["einstimmig"].append(i)
            bh[i] = r[0]["korrekt"]
        elif paare:
            stufen["zwei gegen eine"].append(i)
            bh[i] = r[paare[0][0]]["korrekt"]
        else:
            stufen["keine Mehrheit"].append(i)
            bh[i] = W[i]["korrekt"]
    erg = {"stand": "nachträglich, beschreibend, keine Lesart", "n": len(ids), "stufen": {}}
    for name, S in stufen.items():
        e = {"aufgaben": len(S), "B+H_richtig": sum(bh[i] for i in S), "INT_s0_richtig": sum(L[0][i]["korrekt"] for i in S),
             "MIT_richtig": sum(M[i]["korrekt"] for i in S), "WT-A_richtig": sum(W[i]["korrekt"] for i in S)}
        erg["stufen"][name] = e
        print(f"{name:16s} {e['aufgaben']:3d} Aufgaben | B+H {e['B+H_richtig']:3d} | INT s0 {e['INT_s0_richtig']:3d} | "
              f"MIT {e['MIT_richtig']:3d} | WT-A {e['WT-A_richtig']:3d}")
    tot = {k: sum(e[k] for e in erg["stufen"].values()) for k in ("aufgaben", "B+H_richtig", "INT_s0_richtig", "MIT_richtig")}
    print(f"{'gesamt':16s} {tot['aufgaben']:3d} Aufgaben | B+H {tot['B+H_richtig']:3d} | INT s0 {tot['INT_s0_richtig']:3d} | "
          f"MIT {tot['MIT_richtig']:3d}")
    json.dump(erg, open(os.path.join(ERG, "n30_leiter.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
