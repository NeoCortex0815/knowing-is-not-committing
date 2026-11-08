"""Kognitionswörter (Nutzer 06.11. ~04:10: „Kognitionswörter?“ – Messerschneide = „Deshalb …“ oder „Warte …“).

Wortfamilien im Denktext je 1.000 Wörter, gepoolt (Summe Treffer / Summe Wörter), getrennt vor und nach τy (erste Stelle,
an der die richtige Lösung im Denken steht, 22_angstmarker.tau). Nur Läufe mit τy und mindestens 200 Wörtern danach
gehen in „vor/nach“ ein. Familien (englische Denksprache des Modells, deutsche Namen):
  Deshalb (Folgern) · Warte (Prüfen) · Neuanfang · Alternativ · Hmm (Unsicherheit)
  python 33_kognitionswoerter.py eigen=ergebnisse/eigen-vL/ergebnisse.jsonl mit=ergebnisse/mit-vstil-L/ergebnisse.jsonl
"""
import importlib.util
import json
import os
import re
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
FAMILIEN = {
    "Deshalb": r"\b(?:therefore|thus|hence|thereby|consequently|accordingly|so the (?:answer|result|final))\b",
    "Warte": r"\b(?:wait|double[- ]check|re-?check|verify|let me check)\b",
    "Neuanfang": r"\b(?:first|initially|start over|from scratch|start again|again)\b",
    "Alternativ": r"\b(?:alternatively|another approach|another way|instead)\b",
    "Hmm": r"\b(?:hmm+|maybe|perhaps)\b",
}


def lade_am():
    s = importlib.util.spec_from_file_location("am", os.path.join(HIER, "22_angstmarker.py"))
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


def zaehle(text):
    return {f: len(re.findall(p, text, re.I)) for f, p in FAMILIEN.items()}, max(len(text.split()), 1)


def main():
    am = lade_am()
    for arg in sys.argv[1:]:
        name, pfad = arg.split("=", 1)
        rs = [json.loads(z) for z in open(pfad, encoding="utf-8")]
        summe = {k: {f: 0 for f in FAMILIEN} for k in ("ganz", "vor", "nach")}
        worte = {k: 0 for k in summe}
        n_tau = 0
        for r in rs:
            denk = r["text"].split("</think>")[0]
            c, w = zaehle(denk)
            for f in FAMILIEN:
                summe["ganz"][f] += c[f]
            worte["ganz"] += w
            t = am.tau(denk, r.get("gold"))
            if t is None or len(denk[t:].split()) < 200:
                continue
            n_tau += 1
            for teil, txt in (("vor", denk[:t]), ("nach", denk[t:])):
                c, w = zaehle(txt)
                for f in FAMILIEN:
                    summe[teil][f] += c[f]
                worte[teil] += w
        print(f"\n== {name}: {len(rs)} Läufe, davon {n_tau} mit Lösung im Denken und Text danach (je 1.000 Wörter)")
        print(f"   {'Familie':11s} {'gesamt':>7s} {'vor τy':>7s} {'nach τy':>8s}")
        for f in FAMILIEN:
            werte = [1000 * summe[k][f] / max(worte[k], 1) for k in ("ganz", "vor", "nach")]
            print(f"   {f:11s} {werte[0]:7.1f} {werte[1]:7.1f} {werte[2]:8.1f}")


if __name__ == "__main__":
    main()
