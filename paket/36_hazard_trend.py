"""Exakter Trendtest der Abgabe-Chance über die Weichen (Vorschlag Argon 06.11. ~04:30; Nutzer: „Urknall, der sekündlich
größer wird?“). Unter H0 (flache Abgabe-Chance je Weiche) verteilen sich die E Abgaben bei gegebener Gesamtzahl
multinomial auf die Weichen-Bereiche, mit p_k = N_k / Σ N (N_k = durchlaufene Weichen im Bereich k). Teststatistik
Σ Rang_k · E_k; einseitiger exakter p-Wert durch vollständige Aufzählung. Bereiche wie 34_weichen.py.
  python 36_hazard_trend.py mit=ergebnisse/mit-vstil-L/ergebnisse.jsonl eigen=ergebnisse/eigen-vL/ergebnisse.jsonl
"""
import importlib.util
import json
import math
import os
import sys

HIER = os.path.dirname(os.path.abspath(__file__))


def lade(name, datei):
    s = importlib.util.spec_from_file_location(name, os.path.join(HIER, datei))
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


def zerlegungen(n, k):
    if k == 1:
        yield (n,)
        return
    for i in range(n + 1):
        for rest in zerlegungen(n - i, k - 1):
            yield (i,) + rest


def main():
    w = lade("w", "34_weichen.py")
    am = w.lade_am()
    for arg in sys.argv[1:]:
        name, pfad = arg.split("=", 1)
        E, N = [0] * len(w.BINS), [0] * len(w.BINS)
        for z in open(pfad, encoding="utf-8"):
            r = json.loads(z)
            denk = r["text"].split("</think>")[0]
            t = am.tau(denk, r.get("gold"))
            if t is None:
                continue
            ws = w.weichen(denk, t, "</think>" in r["text"])
            for k, (a, b) in enumerate(w.BINS):
                N[k] += len(ws[a:b])
                E[k] += ws[a:b].count("Ende")
        n, gesamt = sum(E), sum(N)
        p = [x / gesamt for x in N]
        rang = list(range(1, len(E) + 1))
        beob = sum(r_ * e for r_, e in zip(rang, E))
        erw = sum(r_ * n * q for r_, q in zip(rang, p))
        pw = 0.0
        for c in zerlegungen(n, len(E)):
            if sum(r_ * x for r_, x in zip(rang, c)) >= beob:
                lp = math.lgamma(n + 1) + sum(x * math.log(q) - math.lgamma(x + 1) if q > 0 else (0 if x == 0 else -1e9)
                                              for x, q in zip(c, p))
                pw += math.exp(lp)
        print(f"{name}: Abgaben je Bereich {E}, Weichen je Bereich {N}")
        print(f"   Trend Σ Rang·E = {beob} (bei flacher Chance erwartet {erw:.1f}) · exakter einseitiger p = {pw:.4f}")


if __name__ == "__main__":
    main()
