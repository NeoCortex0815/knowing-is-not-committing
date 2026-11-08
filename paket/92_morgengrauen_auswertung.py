"""Morgengrauen auswerten (N10, Lesart vorab in ANNAHMEN). Notizen-Arm (eigen, Antwortmodus, mit Notizen aus der ersten
WT-A-Runde) gegen Kontrolle (INT-Lauf: eigen, Antwortmodus, ohne Notizen), gepaart auf denselben stummen Aufgaben.
Lesart:
  - „wertvoll am Signal“ bei Notizen − Kontrolle ≥ +5 richtige Läufe UND ≥ 10 richtigen Läufen mit Notizen;
  - „widerlegt“ bei Notizen ≤ Kontrolle;
  - sonst „offen“.
Beschreibend:
  - Übernahme eines Notiz-Werts als Antwort;
  - Aufgaben, deren Notizen den richtigen Wert enthalten;
  - Tokens.
  python 92_morgengrauen_auswertung.py
"""
import json
import os
from math import comb

WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ERG = os.path.join(WURZEL, "ergebnisse")
NOTIZ = ["mg-eigen-161-260-a", "mg-eigen-161-260-b", "mg-eigen-261-300"]
KONTROLLE = ["s3-int-eigen-161-210", "s3-int-eigen-211-260", "s3-int-eigen-261-300"]


def laufe(dirs):
    R = {}
    for d in dirs:
        p = os.path.join(ERG, d, "ergebnisse.jsonl")
        if os.path.exists(p):
            for z in open(p, encoding="utf-8"):
                r = json.loads(z)
                R[r["id"]] = r
    return R


def norm(w):
    return (w or "").replace(" ", "").replace("$", "").replace("\\!", "").rstrip(".").lower()


def mcnemar(b, c):
    n = b + c
    return 1.0 if n == 0 else min(1.0, 2 * sum(comb(n, i) for i in range(min(b, c) + 1)) / 2 ** n)


def main():
    D = {}
    for k in ("161-260", "261-300"):
        for z in open(os.path.join(WURZEL, "daten", f"morgengrauen_{k}.jsonl"), encoding="utf-8"):
            d = json.loads(z)
            D[d["unique_id"]] = d
    N, K = laufe(NOTIZ), laufe(KONTROLLE)
    ids = sorted(i for i in D if i in N and i in K)
    print(f"stumme Aufgaben {len(D)} | mit Notizen-Lauf {len(N)} | mit Kontrolle {len(K)} | gepaart {len(ids)}")
    a = sum(1 for i in ids if N[i]["korrekt"] and K[i]["korrekt"])
    b = sum(1 for i in ids if N[i]["korrekt"] and not K[i]["korrekt"])
    c = sum(1 for i in ids if not N[i]["korrekt"] and K[i]["korrekt"])
    n_n, n_k = a + b, a + c
    print(f"richtig: Notizen {n_n} | Kontrolle (INT ohne Notizen) {n_k} | beide {a}, nur Notizen {b}, nur Kontrolle {c}, "
          f"McNemar p = {mcnemar(b, c):.3f}")
    if len(ids) == len(D):
        urteil = ("WERTVOLL am Signal" if n_n - n_k >= 5 and n_n >= 10 else "WIDERLEGT" if n_n <= n_k else "offen")
        print(f"URTEIL N10 (vorab): {urteil} (Differenz {n_n - n_k:+d})")
    else:
        print("URTEIL N10: noch nicht alle Aufgaben fertig")
    mit_r = [i for i in ids if D[i]["notiz_enthaelt_richtig"]]
    print(f"Notizen enthalten den richtigen Wert: {len(mit_r)} Aufgaben → Notizen-Arm richtig {sum(N[i]['korrekt'] for i in mit_r)}, "
          f"Kontrolle richtig {sum(K[i]['korrekt'] for i in mit_r)}")
    uebern = [i for i in ids if D[i]["notiz_werte"] and norm(N[i].get("pred")) in {norm(w) for w in D[i]["notiz_werte"]}]
    print(f"Antwort übernimmt einen Notiz-Wert: {len(uebern)} (davon richtig {sum(N[i]['korrekt'] for i in uebern)})")
    tn = sum(N[i]["tokens"] for i in ids) / max(1, len(ids))
    tk = sum(K[i]["tokens"] for i in ids) / max(1, len(ids))
    print(f"Ø Tokens: Notizen {tn:.0f} | Kontrolle {tk:.0f}")
    json.dump({"gepaart": len(ids), "notizen": n_n, "kontrolle": n_k, "beide": a, "nur_notizen": b, "nur_kontrolle": c,
               "p": mcnemar(b, c), "notiz_mit_richtig": len(mit_r), "uebernahmen": len(uebern)},
              open(os.path.join(ERG, "morgengrauen.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
