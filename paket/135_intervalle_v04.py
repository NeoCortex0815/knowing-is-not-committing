"""Bootstrap-Intervalle für den Bericht v0.4 (12.11.2026). Die Intervalle in v0.3 kamen aus WRENs Durchsicht (ANNAHMEN 08.11.
19:03, gepaarter Bootstrap, 10.000 Ziehungen); sie beruhen auf der alten Bewertung. Dieses Skript rechnet sie mit derselben Art
(gepaarter Bootstrap über Aufgaben, Perzentil-Intervall) einmal auf den Original-Ergebnissen (muss die veröffentlichten Werte
ungefähr treffen, ±0,5 Punkte: Selbsttest gegen bekannte Antwort) und einmal auf dem berichtigten Spiegel nachrechnung_mv/.
[descriptive]
  python paket/135_intervalle_v04.py --selbsttest | --rechnen
"""
import argparse
import importlib.util
import json
import os
import sys

import numpy as np

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(HIER)
SP = os.path.join(WURZEL, "nachrechnung_mv")
D = {"MIT": ["s3-mit-161-260", "s3-mit-261-300"], "ERGORE": ["s3-ergore-161-260", "s3-ergore-261-300"],
     "WT-A": ["s3-wta-161-210", "s3-wta-211-260", "s3-wta-261-300"],
     "INT": ["s3-int-eigen-161-210", "s3-int-eigen-211-260", "s3-int-eigen-261-300"]}
VEROEFFENTLICHT = {"ERGORE": (-10.7, -18.0, -3.4), "WT-A": (-13.6, -21.4, -5.7), "INT": (-6.4, -15.0, 2.1), "Schiedsrichter": (4, -1, 10)}
B = 10000


def lade_mod(name, pfad):
    s = importlib.util.spec_from_file_location(name, pfad)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


def laufe(wurzel, dirs):
    R = {}
    for d in dirs:
        for z in open(os.path.join(wurzel, "ergebnisse", d, "ergebnisse.jsonl"), encoding="utf-8"):
            if z.strip():
                r = json.loads(z)
                R[r["id"]] = bool(r["korrekt"])
    return R


def boot(diff, skala, seed=0):
    rng = np.random.default_rng(seed)
    n = len(diff)
    idx = rng.integers(0, n, size=(B, n))
    s = diff[idx].mean(1) * skala if skala else diff[idx].sum(1)
    pkt = diff.mean() * skala if skala else diff.sum()
    return float(pkt), float(np.percentile(s, 2.5)), float(np.percentile(s, 97.5))


def schiedsrichter_diffs(wurzel):
    """Je uneinige Aufgabe: richtig(Wahl der Sonde) − richtig(Seed 0), genau wie n29 in 107."""
    h = lade_mod("h107", os.path.join(wurzel, "paket", "107_halbtest.py"))
    ev = lade_mod("ev", os.path.join(wurzel, "eval", "03_eval.py"))
    m = lade_mod("m103", os.path.join(wurzel, "paket", "103_vorderzimmer_sonde.py"))
    st = m.stufen()
    F = np.load(os.path.join(wurzel, "ergebnisse", "vorderzimmer_sonde_eingefroren.npz"))
    k = m.SCHICHTEN.index(int(F["schicht"]))

    def werte(saetze):
        X = m.verbinden([m.lade_satz(d, st) for d in saetze])
        return dict(zip(X["ids"], ((X["X"][:, k] - F["mu"]) / F["sd"]) @ F["w"] + F["b"]))
    s0, s1 = werte(h.S0), werte(h.S1)
    A, C = h.laufe(h.S0), h.laufe(h.S1)
    ids = sorted(set(A) & set(C))

    def gleich(i):
        pa, pc = A[i]["pred"], C[i]["pred"]
        return pa is not None and pc is not None and (ev.korrekt(pa, pc) or ev.korrekt(pc, pa))
    U = [i for i in ids if not gleich(i) and A[i]["pred"] is not None and C[i]["pred"] is not None and i in s0 and i in s1]
    return np.array([float((A[i] if s0[i] >= s1[i] else C[i])["korrekt"]) - float(A[i]["korrekt"]) for i in U])


def alle(wurzel):
    M = laufe(wurzel, D["MIT"])
    E = {}
    for name in ("ERGORE", "WT-A", "INT"):
        X = laufe(wurzel, D[name])
        ids = sorted(set(X) & set(M))
        assert len(ids) == 140, (name, len(ids))
        E[name] = boot(np.array([float(X[i]) - float(M[i]) for i in ids]), 100.0) + (sum(X[i] for i in ids), sum(M[i] for i in ids))
    d = schiedsrichter_diffs(wurzel)
    E["Schiedsrichter"] = boot(d, None) + (len(d), int((d != 0).sum()))
    return E


def zeigen(E, titel):
    print(titel)
    for k, v in E.items():
        print(f"  {k:15s} {v[0]:+6.1f} [{v[1]:+6.1f}; {v[2]:+6.1f}]   ({v[3]} gegen {v[4]})" if k != "Schiedsrichter" else
              f"  {k:15s} {v[0]:+6.0f} [{v[1]:+6.0f}; {v[2]:+6.0f}]   (uneinig {v[3]}, verschieden entschieden {v[4]})")


def selbsttest():
    E = alle(WURZEL)
    zeigen(E, "Original-Ergebnisse (alte Bewertung):")
    ok = all(abs(E[k][j] - VEROEFFENTLICHT[k][j]) <= 0.5 + (0.5 if k == "Schiedsrichter" else 0) for k in VEROEFFENTLICHT for j in range(3))
    print("SELBSTTEST", "bestanden (veröffentlichte Intervalle getroffen)" if ok else "NICHT bestanden")
    return ok


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--selbsttest", action="store_true")
    g.add_argument("--rechnen", action="store_true")
    a = ap.parse_args()
    if a.selbsttest:
        sys.exit(0 if selbsttest() else 1)
    E = alle(SP)
    zeigen(E, "Spiegel (berichtigte Bewertung):")
    json.dump(E, open(os.path.join(SP, "logs", "135_intervalle_v04.json"), "w", encoding="utf-8"), indent=1)
