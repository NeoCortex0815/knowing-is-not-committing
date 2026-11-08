"""Wahrheitsspur (Nutzer 06.11. ~11:45): „Das Modell zuckt, aber das Ergebnis kann nur falsch sein, weil es keine Hinweise auf eine
Wahrheit gibt wie bei den bisher gelösten Aufgaben.“ – Welche Hinweise im Denktext trennen wahres von falschem Zucken?

Nur Text, keine GPU. Für jeden Lauf, der eine Antwort abgegeben hat (pred vorhanden), aus dem Denkteil:
  kandidaten  – Zahl der Antwort-Kandidaten im Denken (\\boxed, „answer is …“; 23_klingel_regel.kandidaten)
  verschieden – Zahl verschiedener Kandidaten
  anteil      – Anteil der Kandidaten, die der abgegebenen Antwort entsprechen (Stabilität)
  bestaetigt  – abgegebene Antwort stand mindestens zweimal im Denken
  im_denken   – abgegebene Antwort stand überhaupt im Denken
Zielgröße: abgegebene Antwort richtig/falsch. Kennzahl je Merkmal: AUC (richtig gegen falsch); 0,5 = kein Hinweis.
  python 41_wahrheitsspur.py name=ergebnisse/<lauf>/ergebnisse.jsonl ...
"""
import importlib.util
import json
import os
import sys

HIER = os.path.dirname(os.path.abspath(__file__))


def lade(name, datei):
    s = importlib.util.spec_from_file_location(name, os.path.join(HIER, datei))
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


def auc(pos, neg):
    if not pos or not neg:
        return None
    gr = sum((p > n) + 0.5 * (p == n) for p in pos for n in neg)
    return gr / (len(pos) * len(neg))


def main():
    kr = lade("kr", "23_klingel_regel.py")
    alle = []
    for arg in sys.argv[1:]:
        name, pfad = arg.split("=", 1)
        zeilen = []
        for z in open(pfad, encoding="utf-8"):
            r = json.loads(z)
            if not r.get("pred") or "</think>" not in r["text"]:
                continue
            denk = r["text"].split("</think>")[0]
            k = [kr.norm(c) for _, c in kr.kandidaten(denk)]
            p = kr.norm(r["pred"])
            treffer = sum(c == p for c in k)
            zeilen.append({"richtig": bool(r["korrekt"]), "kandidaten": len(k), "verschieden": len(set(k)),
                           "anteil": treffer / len(k) if k else 0.0, "bestaetigt": float(treffer >= 2),
                           "im_denken": float(treffer >= 1)})
        alle += zeilen
        bericht(name, zeilen)
    if len(sys.argv) > 2:
        bericht("ALLE zusammen", alle)


def bericht(name, zeilen):
    r = [z for z in zeilen if z["richtig"]]
    f = [z for z in zeilen if not z["richtig"]]
    print(f"\n== {name}: {len(zeilen)} Abgaben ({len(r)} richtig, {len(f)} falsch)")
    for m in ("kandidaten", "verschieden", "anteil", "bestaetigt", "im_denken"):
        a = auc([z[m] for z in r], [z[m] for z in f])
        mr = sum(z[m] for z in r) / max(1, len(r))
        mf = sum(z[m] for z in f) / max(1, len(f))
        print(f"   {m:11s} Mittel richtig {mr:6.2f} | falsch {mf:6.2f} | AUC {a if a is None else round(a, 3)}")
    # einfache Regel: „abgeben nur, wenn bestätigt“ – was bliebe übrig?
    rb = sum(z["bestaetigt"] for z in r)
    fb = sum(z["bestaetigt"] for z in f)
    print(f"   Regel „nur bestätigt abgeben“: behält {int(rb)}/{len(r)} richtige, lässt {int(fb)}/{len(f)} falsche durch")


if __name__ == "__main__":
    main()
