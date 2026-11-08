"""Schritt 1b (vorab festgelegt 06.11. ~20:05, ANNAHMEN): Hält der Wahrheitsmelder (Schicht 13) bei Temperatur 1,0?

Sonde nur auf 0,6-Kandidaten gelernt (wahrheit_sammlung.npz), Etiketten neu bereinigt (roh ODER bereinigt richtig).
Zurückgehaltene Werte nach Aufgabe, gleiche 5 Faltungen wie beim Einfrieren: Für Faltung k wird auf 0,6-Kandidaten der
übrigen Aufgaben gelernt und (a) die 0,6-Kandidaten, (b) die 1,0-Kandidaten der Aufgaben in Faltung k bewertet.
Lesart: invariant = AUC-Abfall < 0,05 UND Paar-Trefferquote im selben Lauf fällt um ≤ 10 pp; nicht invariant = AUC < 0,85 ODER
Paar-Abfall > 10 pp; sonst eingeschränkt.
  python 48_sonde_invarianz.py --s06 ergebnisse/wahrheit_sammlung.npz --s10 ergebnisse/wahrheit_t10_sammlung.npz --aus ergebnisse/sonde_invarianz.json
"""
import argparse
import importlib.util
import json
import os

import numpy as np

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(HIER)
ERG = os.path.join(WURZEL, "ergebnisse")


def lade(name, pfad):
    s = importlib.util.spec_from_file_location(name, pfad)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


wm = lade("wm", os.path.join(HIER, "42_wahrheitsmelder.py"))
ev = wm.lade("ev", os.path.join(WURZEL, "eval", "03_eval.py"))


def gold_je_lauf(laeufe):
    g = {}
    for t in sorted({str(l).split("/")[0] for l in laeufe}):
        for z in open(os.path.join(ERG, t, "ergebnisse.jsonl"), encoding="utf-8"):
            r = json.loads(z)
            g[f"{t}/{r['id']}"] = r["gold"]
    return g


def paar_quote(s, y, lauf):
    paare = treffer = 0
    for l in set(lauf):
        m = lauf == l
        r_, f_ = s[m & y], s[m & ~y]
        if len(r_) and len(f_):
            paare += len(r_) * len(f_)
            treffer += int((r_[:, None] > f_[None, :]).sum())
    return (treffer / paare if paare else float("nan")), paare


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--s06", default=os.path.join(ERG, "wahrheit_sammlung.npz"))
    ap.add_argument("--s10", required=True)
    ap.add_argument("--lam", type=float, default=50.0)
    ap.add_argument("--aus", required=True)
    a = ap.parse_args()
    Z6, Z10 = np.load(a.s06), np.load(a.s10)
    X6, X10 = Z6["X_13"].astype(np.float64), Z10["X_13"].astype(np.float64)
    lauf6, lauf10 = Z6["lauf"].astype(str), Z10["lauf"].astype(str)
    auf6, auf10 = Z6["aufgabe"].astype(str), Z10["aufgabe"].astype(str)
    # 0,6-Etiketten neu bereinigt (roh ODER bereinigt), damit beide Temperaturen gleich bewertet sind
    g6 = gold_je_lauf(lauf6)
    y6 = Z6["y"].astype(bool).copy()
    neu = 0
    for i in range(len(y6)):
        if not y6[i]:
            b = wm.bereinige_kandidat(str(Z6["kand"][i]))
            if b != str(Z6["kand"][i]) and ev.korrekt(b, g6[lauf6[i]]):
                y6[i] = True
                neu += 1
    y10 = Z10["y"].astype(bool)
    print(f"0,6: {len(y6)} Kandidaten ({y6.sum()} richtig; {neu} durch Bereinigung neu richtig) | 1,0: {len(y10)} Kandidaten ({y10.sum()} richtig)")
    eind = sorted(set(auf6))
    rng = np.random.default_rng(0)
    rng.shuffle(eind)
    falte = {t: i % 5 for i, t in enumerate(eind)}
    for j, t in enumerate(sorted(set(auf10) - set(falte))):
        falte[t] = j % 5
    f6 = np.array([falte[t] for t in auf6])
    f10 = np.array([falte[t] for t in auf10])
    s6, s10 = np.zeros(len(y6)), np.zeros(len(y10))
    for k in range(5):
        tr = f6 != k
        mu, sd = X6[tr].mean(0), X6[tr].std(0) + 1e-6
        w, b = wm.logreg((X6[tr] - mu) / sd, y6[tr].astype(float), a.lam)
        s6[f6 == k] = ((X6[f6 == k] - mu) / sd) @ w + b
        if (f10 == k).any():
            s10[f10 == k] = ((X10[f10 == k] - mu) / sd) @ w + b
    auc6, auc10 = wm.auc(s6, y6), wm.auc(s10, y10)
    p6, n6 = paar_quote(s6, y6, lauf6)
    p10, n10 = paar_quote(s10, y10, lauf10)
    erg = {"auc_06": auc6, "auc_10": auc10, "paar_06": p6, "paare_06": n6, "paar_10": p10, "paare_10": n10, "je_modell_10": {}}
    print(f"AUC zurückgehalten: 0,6 = {auc6:.3f} | 1,0 = {auc10:.3f} (Abfall {auc6 - auc10:+.3f})")
    print(f"Paar-Trefferquote im selben Lauf: 0,6 = {100 * p6:.1f} % ({n6} Paare) | 1,0 = {100 * p10:.1f} % ({n10} Paare)")
    for t in sorted({l.split("/")[0] for l in lauf10}):
        m = np.array([l.startswith(t + "/") for l in lauf10])
        pa, na = paar_quote(s10[m], y10[m], lauf10[m])
        erg["je_modell_10"][t] = {"auc": wm.auc(s10[m], y10[m]), "kandidaten": int(m.sum()), "paar": pa, "paare": na}
        print(f"   {t:14s}: AUC {wm.auc(s10[m], y10[m]):.3f} ({m.sum()} Kandidaten), Paare {100 * pa:.1f} % ({na})")
    if "final" in Z10.files:
        fin = Z10["final"].astype(bool)
        erg["auc_10_endantworten"] = wm.auc(s10[fin], y10[fin])
        print(f"   nur Endantworten bei 1,0: AUC {erg['auc_10_endantworten']} ({fin.sum()} Endantworten, {(~y10[fin]).sum()} falsch)")
    abfall_auc, abfall_paar = auc6 - auc10, 100 * (p6 - p10)
    if abfall_auc < 0.05 and abfall_paar <= 10:
        u = "INVARIANT"
    elif auc10 < 0.85 or abfall_paar > 10:
        u = "NICHT INVARIANT"
    else:
        u = "EINGESCHRÄNKT"
    erg["urteil"] = u
    print(f"URTEIL 1b: {u} (AUC-Abfall {abfall_auc:+.3f}, Paar-Abfall {abfall_paar:+.1f} pp)")
    json.dump(erg, open(a.aus, "w", encoding="utf-8"), indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
