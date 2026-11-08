"""Auswertung der Gatter-Aktivität je Token (Nachtlauf Schritt 2; Daten aus 50_ergo_gatter.py pruefen --aus).
Fragen für die Ableitung der Schub-Stärke (beschreibend, keine Kriterien):
  1. Feuert das Gatter an richtigen Kandidaten-Enden (Summe > +θ) – und schließt das Modell danach bald (`</think>` innerhalb
     von N Tokens)? Wenn selten: Schub zu schwach (oder das Modell braucht mehrere Anstöße).
  2. Wie oft wird nach einem starken positiven Anstoß NICHT geschlossen, und was folgt dann (Weiterdenken, Antwort, Limit)?
  3. Negative Anstöße an falschen Kandidaten: Wie oft folgt dennoch ein Schließen kurz danach (Gegenschub zu schwach)?
  python 52_gatter_aktivitaet.py --daten ergebnisse/setB_gatter_aktivitaet_s1 [--daten2 ergebnisse/setB_gatter_aktivitaet_s3]
"""
import argparse
import json

import numpy as np


def auswerten(pfad, theta, fenster):
    A = np.load(pfad + ".npz")
    M = json.load(open(pfad + ".json", encoding="utf-8"))
    pos_feuer = pos_zu = neg_feuer = neg_zu = 0
    laeufe_mit_pos = laeufe_zu_nach_pos = 0
    abstand = []
    for m in M:
        key = m["lauf"].replace("/", "|", 1)
        g = A[key].astype(np.float32) if key in A.files else None
        if g is None:
            continue
        zu = m["zu_token"]
        hatte_pos = False
        for k in m["kandidaten"]:
            t = k["t"]
            if t >= len(g):
                continue
            wert = float(g[t])
            if k["richtig"] and wert > theta:
                pos_feuer += 1
                hatte_pos = True
                if 0 <= zu - t <= fenster:
                    pos_zu += 1
                if zu > t:
                    abstand.append(zu - t)
            if (not k["richtig"]) and wert < -theta:
                neg_feuer += 1
                if 0 <= zu - t <= fenster:
                    neg_zu += 1
        if hatte_pos:
            laeufe_mit_pos += 1
            laeufe_zu_nach_pos += int(zu >= 0)
    print(f"== {pfad}: {len(M)} Läufe")
    print(f"   starke Anstöße an RICHTIGEN Kandidaten (> {theta}): {pos_feuer}; danach `</think>` binnen {fenster} Tokens: {pos_zu} "
          f"({100 * pos_zu / max(1, pos_feuer):.0f} %); Läufe mit Anstoß {laeufe_mit_pos}, davon später geschlossen {laeufe_zu_nach_pos}")
    if abstand:
        print(f"   Abstand Anstoß → `</think>` (nur geschlossene): Median {np.median(abstand):.0f} Tokens, 90 %-Quantil {np.quantile(abstand, 0.9):.0f}")
    print(f"   starke Gegenanstöße an FALSCHEN Kandidaten (< -{theta}): {neg_feuer}; trotzdem `</think>` binnen {fenster} Tokens: {neg_zu} "
          f"({100 * neg_zu / max(1, neg_feuer):.0f} %)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--daten", required=True)
    ap.add_argument("--daten2", default="")
    ap.add_argument("--theta", type=float, default=10.0, help="Schwelle für die Gatter-Summe (16 Neuronen; Ziel ≈ 46)")
    ap.add_argument("--fenster", type=int, default=200)
    a = ap.parse_args()
    auswerten(a.daten, a.theta, a.fenster)
    if a.daten2:
        auswerten(a.daten2, a.theta, a.fenster)


if __name__ == "__main__":
    main()
