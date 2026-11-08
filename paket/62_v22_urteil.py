"""Schritt 2c (kompakt) – Urteil V2.2 (ERGORE-WT) und V2.1 (eigen-WT) auf den ersten 30 Aufgaben von Set B, 0,6, 32k, Seed 0.
Lesart vorab festgelegt (ANNAHMEN 07.11. 10:58, bevor ein V2.1/V2.2-Lauf existierte):
  K1 kein Schaden: V2.2 ≥ ERGORE − 2 und V2.1 ≥ Gatter − 2 (Gatter = Stellvertreter der eigen-Basis), je auf denselben Aufgaben;
  K2 WT wirkt: Zünd-Quote (Anteil der Läufe mit richtigem Kandidaten im Denken, deren letzter Kandidat vor `</think>` richtig ist
     und höchstens 64 Tokens davor endet) ≥ 60 % bei V2.2 UND V2.1; dazu ≥ 75 % aller schnellen Abschlüsse (≤ 64 Tokens nach
     irgendeinem Kandidaten, beide Modelle zusammen) an richtigen Kandidaten;
  K3 Ersparnis: beidseits gelöste Aufgaben (V2.2–ERGORE und V2.1–Gatter zusammen) mit weniger Tokens, Vorzeichentest einseitig p < 0,05;
  K4 Sonde (Schicht 13, eingefroren) auf den neuen Kandidaten AUC ≥ 0,93;
  beschreibend: V2.1 gegen V2.2, McNemar, leeres Zucken, nie zu, Tokens.
  python 62_v22_urteil.py [--sonden-sammlung ergebnisse/setB30_wt_kandidaten.npz]
"""
import argparse
import importlib.util
import json
import os
from math import comb

import numpy as np

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(HIER)
ERG = os.path.join(WURZEL, "ergebnisse")
NEU = {"V2.2": "setB30-v22-t06", "V2.1": "setB30-v21-t06"}
BASIS = {"V2.2": ("ERGORE", "setB-ergore-t06"), "V2.1": ("Gatter", "setB-gatter-t06")}


def lade_mod(name, pfad):
    s = importlib.util.spec_from_file_location(name, pfad)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sonden-sammlung", default=os.path.join(ERG, "setB30_wt_kandidaten.npz"))
    ap.add_argument("--sonde", default=os.path.join(ERG, "wahrheitsmelder_eingefroren.npz"))
    a = ap.parse_args()
    u = lade_mod("u", os.path.join(HIER, "51_schritt2_urteil.py"))
    wm = lade_mod("wm", os.path.join(HIER, "42_wahrheitsmelder.py"))
    ev = wm.lade("ev", os.path.join(WURZEL, "eval", "03_eval.py"))
    import transformers as tf
    tok = tf.AutoTokenizer.from_pretrained(os.path.join(WURZEL, "modelle", "Qwen3.5-0.8B"))

    def schliessen(R):
        gelegenheit = zuendung = schnell = schnell_richtig = 0
        for r in R.values():
            gen = r["gen_ids"]
            st = [tok.decode([t]) for t in gen]
            text = "".join(st)
            zc = text.find("</think>")
            gr = np.cumsum([len(s) for s in st])
            ks = [(s0, e, c) for (s0, e, c) in wm.kandidaten_mit_ende(text) if zc < 0 or s0 < zc]
            ok = [bool(ev.korrekt(c, r["gold"])) or bool(ev.korrekt(wm.bereinige_kandidat(c), r["gold"])) for (_, _, c) in ks]
            gelegenheit += any(ok)
            if zc < 0 or not ks:
                continue
            t_zu = int(np.searchsorted(gr, zc, side="right"))
            tl = min(int(np.searchsorted(gr, ks[-1][1] - 1, side="right")), len(st) - 1)
            if t_zu - tl <= 64:
                schnell += 1
                schnell_richtig += ok[-1]
                zuendung += ok[-1]
        return {"gelegenheiten": gelegenheit, "zuendungen": zuendung, "zuend_quote": zuendung / gelegenheit if gelegenheit else 0.0,
                "schnell": schnell, "schnell_richtig": schnell_richtig}

    D, K, erg = {}, {}, {"kennzahlen": {}}
    for m, lauf in NEU.items():
        R = u.lade(lauf)
        if R is None:
            raise SystemExit(f"Lauf fehlt: {lauf}")
        bname, blauf = BASIS[m]
        B = {i: r for i, r in u.lade(blauf).items() if i in R}
        D[m], D[bname] = R, B
    for name, R in D.items():
        K[name] = dict(u.kennz(R), **schliessen(R))
        print(f"  {name:6s} ({len(R)} Aufgaben): {K[name]}", flush=True)
        erg["kennzahlen"][name] = K[name]

    def paar(k1, k2):
        A, B = D[k1], D[k2]
        ids = sorted(set(A) & set(B))
        x = sum(bool(A[i]["korrekt"]) and not B[i]["korrekt"] for i in ids)
        y = sum(bool(B[i]["korrekt"]) and not A[i]["korrekt"] for i in ids)
        print(f"  {k1} gegen {k2}: {sum(bool(A[i]['korrekt']) for i in ids)} gegen {sum(bool(B[i]['korrekt']) for i in ids)} | "
              f"nur links {x}, nur rechts {y}, McNemar p = {u.mcnemar(x, y):.4f}")
        erg[f"{k1} gegen {k2}"] = {"nur_links": x, "nur_rechts": y, "p": u.mcnemar(x, y)}
    for k1, k2 in (("V2.2", "ERGORE"), ("V2.1", "Gatter"), ("V2.2", "V2.1")):
        paar(k1, k2)
    k1 = all(K[m]["richtig"] >= K[BASIS[m][0]]["richtig"] - 2 for m in NEU)
    schnell = sum(K[m]["schnell"] for m in NEU)
    praez = sum(K[m]["schnell_richtig"] for m in NEU) / schnell if schnell else 0.0
    k2 = all(K[m]["zuend_quote"] >= 0.60 for m in NEU) and praez >= 0.75
    weniger = mehr = 0
    for m in NEU:
        A, B = D[m], D[BASIS[m][0]]
        for i in set(A) & set(B):
            if A[i]["korrekt"] and B[i]["korrekt"]:
                weniger += A[i]["tokens"] < B[i]["tokens"]
                mehr += A[i]["tokens"] > B[i]["tokens"]
    n = weniger + mehr
    p3 = sum(comb(n, i) for i in range(weniger, n + 1)) / 2 ** n if n else 1.0
    k3 = p3 < 0.05 and weniger > mehr
    print(f"URTEIL K1 kein Schaden (V2.2 ≥ ERGORE − 2, V2.1 ≥ Gatter − 2): {'ERFÜLLT' if k1 else 'NICHT erfüllt'}")
    print(f"URTEIL K2 WT wirkt (Zünd-Quote ≥ 60 % je Modell, Präzision ≥ 75 %): {'ERFÜLLT' if k2 else 'NICHT erfüllt'} "
          f"(V2.2 {100 * K['V2.2']['zuend_quote']:.0f} % [{K['V2.2']['zuendungen']}/{K['V2.2']['gelegenheiten']}], "
          f"V2.1 {100 * K['V2.1']['zuend_quote']:.0f} % [{K['V2.1']['zuendungen']}/{K['V2.1']['gelegenheiten']}], "
          f"Basis ERGORE {100 * K['ERGORE']['zuend_quote']:.0f} %, Gatter {100 * K['Gatter']['zuend_quote']:.0f} %; Präzision {100 * praez:.0f} %)")
    print(f"URTEIL K3 Ersparnis (beidseits gelöst: weniger {weniger}, mehr {mehr}, p einseitig {p3:.4f}): {'ERFÜLLT' if k3 else 'NICHT erfüllt'}")
    erg.update({"K1": k1, "K2": k2, "K3": k3, "praezision": praez, "tokens_weniger": weniger, "tokens_mehr": mehr, "p_K3": p3})
    if os.path.exists(a.sonden_sammlung):
        # K4 relativ (Änderung 07.11. 12:11, VOR jedem V2.1/V2.2-Lauf festgehalten): Auf Set B liegt die Sonde schon bei den
        # Basisläufen unter 0,93 (ERGORE 0,925, Gatter 0,892, MIT 0,966). Maßstab daher: AUC auf den neuen Kandidaten ≥ AUC der
        # jeweiligen Basis auf denselben 30 Aufgaben − 0,03 (Basis-Kandidaten aus ergebnisse/setB_kandidaten.npz).
        S = np.load(a.sonde)

        def scores(Z):
            return ((Z["X_13"].astype(np.float64) - S["mu"]) / S["sd"]) @ S["w"] + S["b"]
        Zn = np.load(a.sonden_sammlung)
        Zb = np.load(os.path.join(ERG, "setB_kandidaten.npz"))
        scn, scb = scores(Zn), scores(Zb)
        ids30 = set(D["V2.2"]) | set(D["V2.1"])
        k4 = True
        for m, lauf in NEU.items():
            mn = np.array([l.split("/")[0] == lauf for l in Zn["lauf"]])
            bl = BASIS[m][1]
            mb = np.array([l.split("/")[0] == bl and l.split("/", 1)[1] in ids30 for l in Zb["lauf"]])
            a_n = wm.auc(scn[mn], Zn["y"][mn].astype(bool)) if mn.any() else float("nan")
            a_b = wm.auc(scb[mb], Zb["y"][mb].astype(bool)) if mb.any() else float("nan")
            ok = bool(a_n >= a_b - 0.03)
            k4 = k4 and ok
            print(f"   Sonde {m}: AUC {a_n:.3f} ({mn.sum()} Kandidaten) gegen Basis {BASIS[m][0]} {a_b:.3f} ({mb.sum()}) – "
                  f"{'intakt' if ok else 'SCHLECHTER als Basis − 0,03'}")
            erg[f"auc_{m}"], erg[f"auc_basis_{m}"] = a_n, a_b
        print(f"URTEIL K4 Sonde (AUC ≥ Basis − 0,03 je Modell): {'ERFÜLLT' if k4 else 'NICHT erfüllt'}")
        erg["K4"] = k4
    json.dump(erg, open(os.path.join(ERG, "schritt2c_urteil.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
