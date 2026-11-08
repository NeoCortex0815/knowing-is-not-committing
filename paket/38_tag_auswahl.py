"""Tag-Auswahl (06.11. ~05:10, VORAB FESTGELEGT vor den Gitter-Ergebnissen; Nutzer: „Puzzle näher kommen, welches unsere
Kriterien erfüllt“).

waehlen:   Kandidaten = Kopplungs-Varianten mit beiden Seeds auf den 60 Übungsaufgaben (ergebnisse/tag1-<name>-s0/-s1,
           ergebnisse/tag2-<name>-s0/-s1). Punktzahl = richtig über beide Seeds (120 Läufe); Gleichstand → weniger falsche
           Abgaben → weniger „Flur“ (Denken zu, Antwort am Limit). Teilnahme nur, wenn die Punktzahl die von eigen
           übertrifft (Seed 0: ergebnisse/entschluss-uebung-eigen, Seed 1: ergebnisse/tag1-eigen-s1).
           Ausgabe: Tabelle + ergebnisse/tag_auswahl.json; Exit 0 = Kandidat gewählt, 3 = keiner.
vergleich: gewählte Variante auf den 40 MATH-500-Testaufgaben gegen eigen-vL und MIT (mit-vstil-L), gepaart (McNemar exakt).
  python 38_tag_auswahl.py waehlen
  python 38_tag_auswahl.py vergleich --test ergebnisse/tag2-test40-b5
"""
import argparse
import glob
import importlib.util
import json
import os
import sys
from math import comb

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(HIER)
ERG = os.path.join(WURZEL, "ergebnisse")


def lade_jsonl(pfad):
    return {json.loads(z)["id"]: json.loads(z) for z in open(pfad, encoding="utf-8")}


def kennzahlen(rs, am):
    k = {"richtig": 0, "abgegeben": 0, "falsch_abgegeben": 0, "flur": 0, "denken_zu": 0, "loesung_im_denken": 0}
    for r in rs.values():
        zu = "</think>" in r["text"]
        k["richtig"] += bool(r["korrekt"])
        k["abgegeben"] += r["ende"] == "eos"
        k["falsch_abgegeben"] += r["ende"] == "eos" and not r["korrekt"]
        k["flur"] += zu and r["ende"] != "eos"
        k["denken_zu"] += zu
        k["loesung_im_denken"] += am.tau(r["text"].split("</think>")[0], r.get("gold")) is not None
    return k


def mcnemar(a, b):
    n = a + b
    return min(1.0, 2 * sum(comb(n, x) for x in range(0, min(a, b) + 1)) / 2 ** n) if n else 1.0


def waehlen(a):
    s = importlib.util.spec_from_file_location("am", os.path.join(HIER, "22_angstmarker.py"))
    am = importlib.util.module_from_spec(s)
    s.loader.exec_module(am)
    seeds = [int(x) for x in a.seeds.split(",")]
    eigen_d = {0: os.path.join(ERG, "entschluss-uebung-eigen"), 1: os.path.join(ERG, "tag1-eigen-s1")}
    laeufe = {"eigen": [eigen_d[s] for s in seeds]}
    for d in sorted(glob.glob(os.path.join(ERG, "tag[12]-*-s0"))):
        name = os.path.basename(d)[5:-3]
        if name == "eigen" or name.startswith("test40"):
            continue
        if not os.path.exists(os.path.join(d, "zusammenfassung.json")):
            continue
        ds = [d[:-1] + str(s) for s in seeds]
        if not all(os.path.exists(os.path.join(x, "zusammenfassung.json")) for x in ds):
            # Regel 06.11. ~05:55: verglichen wird nur auf Seeds, die für ALLE Kandidaten vorliegen → Rückfall auf Seed 0
            print(f"{name}: nicht alle Seeds {a.seeds} vorhanden – Vergleich nur auf gemeinsamen Seeds")
            sys.exit(4)
        laeufe[name] = ds
    tab = {}
    for name, ds in laeufe.items():
        if not all(os.path.exists(os.path.join(d, "zusammenfassung.json")) for d in ds):
            continue
        summe = None
        for d in ds:
            k = kennzahlen(lade_jsonl(os.path.join(d, "ergebnisse.jsonl")), am)
            summe = k if summe is None else {x: summe[x] + k[x] for x in k}
        tab[name] = summe
    print(f"{'Variante':10s} " + " ".join(f"{x:>17s}" for x in next(iter(tab.values()))))
    for name, k in tab.items():
        print(f"{name:10s} " + " ".join(f"{v:17d}" for v in k.values()))
    if "eigen" not in tab:
        print(f"eigen (Seeds {a.seeds}) fehlt – keine Auswahl")
        sys.exit(4)
    if len(tab) < 2:
        print(f"keine Kopplungs-Variante mit vollständigen Seeds {a.seeds}")
        sys.exit(4)
    kand = [n for n in tab if n != "eigen" and tab[n]["richtig"] > tab["eigen"]["richtig"]]
    if not kand:
        json.dump({"gewaehlt": None, "tabelle": tab}, open(os.path.join(ERG, "tag_auswahl.json"), "w"), indent=1)
        print("KEINE Variante schlägt eigen auf den Übungsaufgaben – kein Testlauf")
        sys.exit(3)
    best = sorted(kand, key=lambda n: (-tab[n]["richtig"], tab[n]["falsch_abgegeben"], tab[n]["flur"]))[0]
    json.dump({"gewaehlt": best, "tabelle": tab}, open(os.path.join(ERG, "tag_auswahl.json"), "w"), indent=1)
    print(f"GEWÄHLT: {best} (richtig {tab[best]['richtig']} gegen eigen {tab['eigen']['richtig']} von {60 * len(seeds)}, Seeds {a.seeds})")
    print(best, file=sys.stderr)


def vergleich(a):
    t = lade_jsonl(os.path.join(a.test, "ergebnisse.jsonl"))
    for ref in ("eigen-vL", "mit-vstil-L"):
        r = lade_jsonl(os.path.join(ERG, ref, "ergebnisse.jsonl"))
        ids = [i for i in t if i in r]
        nt = sum(bool(t[i]["korrekt"]) for i in ids)
        nr = sum(bool(r[i]["korrekt"]) for i in ids)
        b = sum(bool(t[i]["korrekt"]) and not r[i]["korrekt"] for i in ids)
        c = sum(bool(r[i]["korrekt"]) and not t[i]["korrekt"] for i in ids)
        print(f"Test gegen {ref:12s}: {nt}/{len(ids)} gegen {nr}/{len(ids)} | nur Test {b}, nur {ref} {c}, McNemar p = {mcnemar(b, c):.3f}")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    w = sub.add_parser("waehlen")
    w.add_argument("--seeds", default="0,1", help="Rückfall 06.11. ~05:45 (Zeit): nur Seed 0")
    v = sub.add_parser("vergleich")
    v.add_argument("--test", required=True)
    a = ap.parse_args()
    waehlen(a) if a.cmd == "waehlen" else vergleich(a)


if __name__ == "__main__":
    main()
