"""Flur / Horizont (08.11.; NACHTRÄGLICH, beschreibend; Nutzer: „Horizont – hier brauchen wir mehr Tiefe, das ist der Flur des
Fuchsbaus“). Frage: Warum öffnet das Wahrheits-Tor an richtigen Werten tief im Denken seltener? Liegt es an der TIEFE (Abstand zum
Anfang), am SCHLEIFEN-ZUSTAND (der Text wiederholt sich) oder an der SCHWIERIGKEIT (späte Stellen stammen aus schweren Aufgaben)?
Daten: Zuck-Messung 82 auf WT-A-Texten und MIT-Texten (gleiche Sonde, gleicher L15-Eingang). Je richtiger Wert-Aussage:
  offen = zT_max > 0; Tiefe t (Tokens); Stufe 1–5; Text-Quelle (WT-A/MIT); Schleifen-Grad w = Anteil der 8-Gramme in den 512 Tokens
  vor t, die im Text schon früher vorkamen.
Ausgabe:
  - Tabellen „Tor offen“ nach Tiefe × Schleifen-Grad (niedrig/mittel/hoch, Drittel über alle);
  - nach Tiefe × Stufe;
  - logistische Regression offen ~ log(t) + w + Stufe + Quelle. Koeffizienten werden standardisiert; mit Lauf-Bootstrap
    (200×) als Unsicherheit, weil Aussagen eines Laufs nicht unabhängig sind.
Dasselbe für falsche Wert-Aussagen als Vergleich.
  python 88_flur.py → ergebnisse/flur.json
"""
import collections
import importlib.util
import json
import os

import numpy as np

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(HIER)
ERG = os.path.join(WURZEL, "ergebnisse")
QUELLEN = {"WT-A": ("zucken_WT-A_ergo-zigA.jsonl", ["s3-wta-161-210", "s3-wta-211-260", "s3-wta-261-300"]),
           "MIT": ("zucken_MIT_mit-wt.jsonl", ["s3-mit-161-260", "s3-mit-261-300"])}
TIEFE = ((0, 2000), (2000, 8000), (8000, 16000), (16000, 40000))


def lade_mod(name, pfad):
    s = importlib.util.spec_from_file_location(name, pfad)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


def schleifen_grad(ids, fenster=512, n=8):
    """w[t] = Anteil der 8-Gramme (endend in [t-fenster+1, t]), die vorher im Text schon vorkamen."""
    gesehen = set()
    wdh = np.zeros(len(ids), dtype=np.float32)
    for i in range(n - 1, len(ids)):
        k = tuple(ids[i - n + 1:i + 1])
        if k in gesehen:
            wdh[i] = 1.0
        else:
            gesehen.add(k)
    c = np.concatenate([[0.0], np.cumsum(wdh)])
    w = np.zeros(len(ids), dtype=np.float32)
    for t in range(len(ids)):
        a = max(0, t - fenster + 1)
        w[t] = (c[t + 1] - c[a]) / (t + 1 - a)
    return w


def main():
    lr = lade_mod("dw", os.path.join(HIER, "72_denk_weiche.py"))
    stufe = {}
    for z in open(os.path.join(WURZEL, "daten", "math500.jsonl"), encoding="utf-8"):
        d = json.loads(z)
        stufe[d["unique_id"]] = int(d["level"])
    zeilen = []  # (quelle, lauf-id, ok, offen, t, w, stufe)
    for q, (datei, dirs) in QUELLEN.items():
        gen = {}
        for d in dirs:
            for z in open(os.path.join(ERG, d, "ergebnisse.jsonl"), encoding="utf-8"):
                r = json.loads(z)
                gen[r["id"]] = r["gen_ids"]
        for z in open(os.path.join(ERG, datei), encoding="utf-8"):
            r = json.loads(z)
            w = schleifen_grad(gen[r["id"]][:r["n_mess"]])
            for s in r["aussagen"]:
                if s["ok"] is None:
                    continue
                zeilen.append((q, r["id"], bool(s["ok"]), s["zT_max"] > 0, s["t"], float(w[min(s["t"], len(w) - 1)]), stufe.get(r["id"], 3)))
        print(f"{q}: {sum(1 for x in zeilen if x[0] == q)} Aussagen", flush=True)
    W = np.array([x[5] for x in zeilen])
    g1, g2 = np.quantile(W, [1 / 3, 2 / 3])
    print(f"Schleifen-Grad: Drittel-Grenzen {g1:.2f} / {g2:.2f}")
    B = {"drittel": [float(g1), float(g2)]}
    import sys
    if "--geschachtelt" in sys.argv:  # 08.11. ~12:35 (Argon, Teil 2): M1 nur Tiefe, M2 + Stufe, M3 + Schleife, M4 + Quelle
        X = [x for x in zeilen if x[2]]
        y = np.array([1.0 if x[3] else 0.0 for x in X])
        spalten = {"Tiefe": np.log1p(np.array([x[4] for x in X], float)), "Stufe": np.array([x[6] for x in X], float),
                   "Schleife": np.array([x[5] for x in X], float), "Quelle MIT": np.array([1.0 if x[0] == "MIT" else 0.0 for x in X])}
        for name, cols in (("M1 Tiefe", ["Tiefe"]), ("M2 + Stufe", ["Tiefe", "Stufe"]), ("M3 + Schleife", ["Tiefe", "Stufe", "Schleife"]),
                           ("M4 + Quelle", ["Tiefe", "Stufe", "Schleife", "Quelle MIT"])):
            F = np.stack([spalten[c] for c in cols], 1)
            F = (F - F.mean(0)) / (F.std(0) + 1e-9)
            w, _ = lr.logreg(F, y)
            print(f"   geschachtelt {name:14s}: " + ", ".join(f"{c} {w[k + 1]:+.2f}" for k, c in enumerate(cols)))
        return

    def stufe_w(w):
        return "niedrig" if w <= g1 else ("mittel" if w <= g2 else "hoch")
    for ok_wert, name in ((True, "richtig"), (False, "falsch")):
        X = [x for x in zeilen if x[2] == ok_wert]
        print(f"\n== {name}e Wert-Aussagen: Tor offen (%) nach Tiefe × Schleifen-Grad [n] – beide Text-Quellen zusammen")
        tab = {}
        for lo, hi in TIEFE:
            teile = []
            for sw in ("niedrig", "mittel", "hoch"):
                Y = [x for x in X if lo <= x[4] < hi and stufe_w(x[5]) == sw]
                v = 100 * np.mean([x[3] for x in Y]) if Y else float("nan")
                tab[f"{lo}-{hi} {sw}"] = [float(v), len(Y)]
                teile.append(f"{sw} {v:4.0f} [{len(Y):5d}]")
            print(f"   {lo:5d}–{hi:5d}: " + " | ".join(teile))
        B[f"tiefe_x_schleife_{name}"] = tab
        print(f"== {name}: Tor offen (%) nach Tiefe × Stufe [n]")
        tab = {}
        for lo, hi in TIEFE:
            teile = []
            for st in (1, 2, 3, 4, 5):
                Y = [x for x in X if lo <= x[4] < hi and x[6] == st]
                v = 100 * np.mean([x[3] for x in Y]) if Y else float("nan")
                tab[f"{lo}-{hi} S{st}"] = [float(v), len(Y)]
                teile.append(f"S{st} {v:4.0f} [{len(Y):4d}]")
            print(f"   {lo:5d}–{hi:5d}: " + " | ".join(teile))
        B[f"tiefe_x_stufe_{name}"] = tab
        # logistische Regression mit Lauf-Bootstrap
        def matrix(Y):
            t = np.log1p(np.array([x[4] for x in Y], dtype=float))
            w = np.array([x[5] for x in Y], dtype=float)
            st = np.array([x[6] for x in Y], dtype=float)
            qm = np.array([1.0 if x[0] == "MIT" else 0.0 for x in Y])
            F = np.stack([t, w, st, qm], 1)
            mu, sd = F.mean(0), F.std(0) + 1e-9
            F = (F - mu) / sd
            return F, np.array([1.0 if x[3] else 0.0 for x in Y])
        Xm, y = matrix(X)
        w0, _ = lr.logreg(Xm, y)
        laeufe = sorted({(x[0], x[1]) for x in X})
        idx = collections.defaultdict(list)
        for i, x in enumerate(X):
            idx[(x[0], x[1])].append(i)
        rng = np.random.default_rng(0)
        boot = []
        for _ in range(200):
            zieh = rng.integers(0, len(laeufe), len(laeufe))
            ii = [i for k in zieh for i in idx[laeufe[k]]]
            Xb, yb = matrix([X[i] for i in ii])
            boot.append(lr.logreg(Xb, yb)[0])
        boot = np.array(boot)
        lo_, hi_ = np.quantile(boot, [0.025, 0.975], axis=0)
        namen = ["Achsenabschnitt", "log Tiefe", "Schleifen-Grad", "Stufe", "Quelle MIT"]
        print(f"== {name}: logistische Regression offen ~ log Tiefe + Schleifen-Grad + Stufe + Quelle (standardisiert; 95 % Lauf-Bootstrap)")
        B[f"regression_{name}"] = {}
        for k, nm in enumerate(namen):
            print(f"   {nm:16s}: {w0[k]:+.2f} [{lo_[k]:+.2f}; {hi_[k]:+.2f}]")
            B[f"regression_{name}"][nm] = [float(w0[k]), float(lo_[k]), float(hi_[k])]
    json.dump(B, open(os.path.join(ERG, "flur.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(f"gespeichert: {os.path.join(ERG, 'flur.json')}")


if __name__ == "__main__":
    main()
