"""Empfindlichkeitstest Temperatur (Nutzer 06.11. ~12:55: „schauen, was mit unseren Erkenntnissen wirklich eine deutliche Änderung gibt,
wenn man den Parameter ändert oder nicht“). Gleiche 60 Übungsaufgaben, Seed 0, 12k, vLLM-Stil; nur die Temperatur ändert sich
(0,6 = MIT-Protokoll, 1,0 = Herstellerempfehlung Qwen3.6 Denkmodus). VORAB FESTGELEGT: „deutliche Änderung“, wenn der gepaarte
Gewinn ERGORE − eigen bei 1,0 um mindestens 8 Aufgaben vom Gewinn bei 0,6 abweicht ODER die Signifikanz (p < 0,05) kippt.
  python 43_temperatur_vergleich.py --eigen06 entschluss-uebung-eigen --ergore06 tag2-kw75-s0 --eigen10 temp10-eigen --ergore10 temp10-kw75
"""
import argparse
import json
import os
from math import comb

ERG = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ergebnisse")


def lade(d):
    return {json.loads(z)["id"]: json.loads(z) for z in open(os.path.join(ERG, d, "ergebnisse.jsonl"), encoding="utf-8")}


def mcnemar(a, b):
    n = a + b
    return min(1.0, 2 * sum(comb(n, x) for x in range(0, min(a, b) + 1)) / 2 ** n) if n else 1.0


def kennz(d, ids):
    r = [d[i] for i in ids]
    return {"richtig": sum(bool(x["korrekt"]) for x in r), "abgegeben": sum(x["ende"] == "eos" for x in r),
            "falsch_abg": sum(x["ende"] == "eos" and not x["korrekt"] for x in r),
            "flur": sum("</think>" in x["text"] and x["ende"] != "eos" for x in r),
            "denken_nie_zu": sum("</think>" not in x["text"] for x in r),
            "tokens": round(sum(x.get("tokens", 0) for x in r) / max(1, len(r)))}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", default="ERGORE", help="Bezeichnung des Eingriffs in der Ausgabe")
    for n in ("--eigen06", "--ergore06", "--eigen10", "--ergore10"):
        ap.add_argument(n, required=True)
    a = ap.parse_args()
    D = {k: lade(getattr(a, k)) for k in ("eigen06", "ergore06", "eigen10", "ergore10")}
    ids = sorted(set.intersection(*(set(d) for d in D.values())))
    print(f"{len(ids)} gemeinsame Aufgaben")
    for k, d in D.items():
        print(f"  {k:9s} {kennz(d, ids)}")
    gew = {}
    for t in ("06", "10"):
        e, g = D["eigen" + t], D["ergore" + t]
        x = sum(bool(g[i]["korrekt"]) and not e[i]["korrekt"] for i in ids)
        y = sum(bool(e[i]["korrekt"]) and not g[i]["korrekt"] for i in ids)
        gew[t] = (x - y, mcnemar(x, y))
        print(f"  Temperatur {t[0]},{t[1]}: {a.name} − eigen = {x - y:+d} (nur {a.name} {x}, nur eigen {y}), McNemar p = {gew[t][1]:.4f}")
    kippt = (gew["06"][1] < 0.05) != (gew["10"][1] < 0.05)
    deutlich = abs(gew["10"][0] - gew["06"][0]) >= 8 or kippt
    print(f"URTEIL: {'DEUTLICHE ÄNDERUNG' if deutlich else 'keine deutliche Änderung'} durch die Temperatur "
          f"(Gewinn {gew['06'][0]:+d} → {gew['10'][0]:+d}{', Signifikanz kippt' if kippt else ''})")


if __name__ == "__main__":
    main()
