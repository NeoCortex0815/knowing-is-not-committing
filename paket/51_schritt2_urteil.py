"""Schritt 2 – Urteil Entwicklungs-Test ERGO-Gatter auf Set B (60 frische MATH-Train-Aufgaben, 32k, Seed 0).
Lesart (vorab in ANNAHMEN festzulegen, bevor der Test startet):
  K1 falsches Zucken (Denken zu, aber keine Antwort abgegeben) beim Gatter ≤ 6 von 60, bei 0,6 UND bei 1,0;
  K2 Treffer: Gatter ≥ ERGORE − 2 bei 0,6 und Gatter ≥ MIT − 2 bei 1,0;
  K3 Sonden-Abnahme: eingefrorene Wahrheitssonde (Schicht 13) auf den Kandidaten der Gatter-Läufe AUC ≥ 0,93;
  beschreibend: Gatter gegen MIT bei 1,0 (McNemar), Tokens.
  python 51_schritt2_urteil.py [--sonden-sammlung ergebnisse/schritt2_gatter_kandidaten.npz]
"""
import argparse
import json
import os
from math import comb

import numpy as np

ERG = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ergebnisse")
BOX = chr(92) + "boxed{"
LAEUFE = {("Gatter", "1,0"): "setB-gatter-t10", ("MIT", "1,0"): "setB-mit-t10", ("ERGORE", "1,0"): "setB-ergore-t10",
          ("Gatter", "0,6"): "setB-gatter-t06", ("ERGORE", "0,6"): "setB-ergore-t06", ("MIT", "0,6"): "setB-mit-t06",
          ("Gatter3", "1,0"): "setB-gatter3-t10", ("Gatter3", "0,6"): "setB-gatter3-t06"}
PFLICHT = [("Gatter", "1,0"), ("MIT", "1,0"), ("Gatter", "0,6"), ("ERGORE", "0,6")]


def lade(d):
    p = os.path.join(ERG, d, "ergebnisse.jsonl")
    return {json.loads(z)["id"]: json.loads(z) for z in open(p, encoding="utf-8")} if os.path.exists(p) else None


def mcnemar(a, b):
    n = a + b
    return min(1.0, 2 * sum(comb(n, x) for x in range(0, min(a, b) + 1)) / 2 ** n) if n else 1.0


def kennz(R):
    zucken = sum(1 for r in R.values() if "</think>" in r["text"] and not (BOX in r["text"].split("</think>", 1)[1] and r["ende"] == "eos")
                 and not r["korrekt"])
    return {"richtig": sum(bool(r["korrekt"]) for r in R.values()), "laeufe": len(R), "zucken": zucken,
            "nie_zu": sum("</think>" not in r["text"] for r in R.values()),
            "tokens": round(float(np.mean([r.get("tokens", 0) for r in R.values()])))}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sonden-sammlung", default=os.path.join(ERG, "setB_kandidaten.npz"))
    ap.add_argument("--sonde", default=os.path.join(ERG, "wahrheitsmelder_eingefroren.npz"))
    a = ap.parse_args()
    D = {k: lade(v) for k, v in LAEUFE.items()}
    K = {}
    for k, R in D.items():
        if R is None:
            print(f"  {k[0]:6s} {k[1]}: fehlt")
            continue
        K[k] = kennz(R)
        print(f"  {k[0]:6s} {k[1]}: {K[k]}")
    def vergleich(k1, k2):
        A, B = D[k1], D[k2]
        ids = sorted(set(A) & set(B))
        x = sum(bool(A[i]["korrekt"]) and not B[i]["korrekt"] for i in ids)
        y = sum(bool(B[i]["korrekt"]) and not A[i]["korrekt"] for i in ids)
        print(f"  {k1[0]} {k1[1]} gegen {k2[0]} {k2[1]}: {K[k1]['richtig']} gegen {K[k2]['richtig']} | nur links {x}, nur rechts {y}, "
              f"McNemar p = {mcnemar(x, y):.4f}")
        return x, y
    erg = {"kennzahlen": {f"{k[0]} {k[1]}": v for k, v in K.items()}}
    if all(k in K for k in PFLICHT):
        for k1, k2 in ((("Gatter", "1,0"), ("MIT", "1,0")), (("Gatter", "1,0"), ("ERGORE", "1,0")), (("Gatter", "0,6"), ("ERGORE", "0,6")),
                       (("Gatter", "0,6"), ("MIT", "0,6")), (("Gatter3", "1,0"), ("MIT", "1,0")), (("Gatter3", "0,6"), ("ERGORE", "0,6")),
                       (("Gatter3", "1,0"), ("Gatter", "1,0")), (("Gatter3", "0,6"), ("Gatter", "0,6"))):
            if k1 in K and k2 in K:
                vergleich(k1, k2)
        k1 = K[("Gatter", "0,6")]["zucken"] <= 6 and K[("Gatter", "1,0")]["zucken"] <= 6
        k2 = (K[("Gatter", "0,6")]["richtig"] >= K[("ERGORE", "0,6")]["richtig"] - 2
              and K[("Gatter", "1,0")]["richtig"] >= K[("MIT", "1,0")]["richtig"] - 2)
        print(f"URTEIL K1 falsches Zucken ≤ 6/60 bei beiden Temperaturen: {'ERFÜLLT' if k1 else 'NICHT erfüllt'} "
              f"(0,6: {K[('Gatter', '0,6')]['zucken']}, 1,0: {K[('Gatter', '1,0')]['zucken']})")
        print(f"URTEIL K2 Treffer (≥ ERGORE − 2 bei 0,6; ≥ MIT − 2 bei 1,0): {'ERFÜLLT' if k2 else 'NICHT erfüllt'}")
        erg.update({"K1": k1, "K2": k2})
    if os.path.exists(a.sonden_sammlung):
        import importlib.util
        s = importlib.util.spec_from_file_location("wm", os.path.join(os.path.dirname(os.path.abspath(__file__)), "42_wahrheitsmelder.py"))
        wm = importlib.util.module_from_spec(s)
        s.loader.exec_module(wm)
        Z, S = np.load(a.sonden_sammlung), np.load(a.sonde)
        sc = ((Z["X_13"].astype(np.float64) - S["mu"]) / S["sd"]) @ S["w"] + S["b"]
        yy, lauf = Z["y"].astype(bool), Z["lauf"].astype(str)
        for prefix, name in (("setB-gatter-t", "Gatter"), ("setB-gatter3-t", "Gatter3 (Dosis-Arm)"), ("setB-ergore-t", "ERGORE"), ("setB-mit-t", "MIT")):
            m = np.array([l.startswith(prefix) for l in lauf])
            if m.any():
                auc = wm.auc(sc[m], yy[m])
                print(f"   Sonde auf {name}-Läufen: AUC {auc:.3f} ({m.sum()} Kandidaten)")
                erg[f"auc_{name}"] = auc
        if "auc_Gatter" in erg:
            auc = erg["auc_Gatter"]
            print(f"URTEIL K3 Sonden-Abnahme (AUC ≥ 0,93 auf Gatter-Läufen): {'ERFÜLLT' if auc >= 0.93 else 'NICHT erfüllt'} (AUC {auc:.3f})")
    json.dump(erg, open(os.path.join(ERG, "schritt2_urteil.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
