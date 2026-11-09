"""(N31) Kopplung Wissen → Festlegen (08.11. abends; Roadmap Punkt 6, Nutzer: „Ausbau der wahrheitsgetreuen /
Neuronenzucken-Untersuchungen“). Eingefroren in paket/MEILENSTEIN2_N31_N32.md; ZUSATZ vor dem Datenkontakt nach WRENs Durchsicht
(Nutzer: „Ja, einbauen“) in paket/MEILENSTEIN2_ZUSATZ_WREN.md. Prüfsummen in ANNAHMEN.

Frage: Folgt die *eigene* Festlegungs-Neigung des Modells, also p(</think>) ohne Reflex, seinem Wahrheitssignal?
Nur vorhandene Daten aus der Zuck-Messung 82, keine Modell-Rechnung:
  eigen ≈ WT-A-Texte, WT-A-Modell mit stummgeschalteten 16 WT-Neuronen  (ergebnisse/zucken_WT-A_ergo-zigA.jsonl)
  MIT   ≈ MIT-Texte,  MIT+WT-Modell mit stummgeschalteten 16 Neuronen   (ergebnisse/zucken_MIT_mit-wt.jsonl)
Je Wert-Aussage im Denken mit bekannter Wahrheit:
  K = zT_max (Wissen);
  F = log10(max(p_t_abl, p_arg_abl)), rohe Wahrscheinlichkeit für </think> ohne Reflex (Festlegen; log nur zur Lesbarkeit).
Hauptlesarten (mit Zusatz):
  H6a eigen: AUC_F < 0,60 → „Festlegen blind (bestätigt)“; ≥ 0,70 → „Festlegen gekoppelt (widerlegt)“; sonst „offen“.
      Ob „Wissen da“ gilt, sagt das K-Band (≥ 0,75 stark / 0,65–0,75 schwach / < 0,65 zerstreut), das mit im Ergebnis steht.
  H6b MIT:   AUC_F ≥ 0,70 → „koppelt“; < 0,60 → „blind“; sonst „offen“.
  H6c Unterschied AUC_F(MIT) − AUC_F(eigen): ≥ 0,10 mit 95-%-KI ohne 0 → „MIT koppelt stärker“; KI enthält 0 → „kein Unterschied
      nachweisbar“; sonst „offen (Fall vorab nicht benannt)“.
  Deutungsmatrix (vollständig): eigen blind & MIT koppelt / beide blind / eigen koppelt & MIT blind / beide koppeln / sonst offen.
Zusatzmessung Schild (vorab festgelegt, beschreibend; Wette WREN): AUC_F und AUC_K nur an Aussagen 0–15 Tokens hinter einem
  eigenen Schild („the (final) answer is“, „so the answer“, „therefore the answer“; Erkennung wie 99_schilder_int.py, S3).
  ≥ 0,70 → „koppelt am Schild“; < 0,60 → „blind am Schild“; sonst „offen“.
Cluster-Bootstrap über Läufe (10.000 Ziehungen, Seed 20261109). Beschreibend außerdem: Spearman(K, F) unter den richtigen Aussagen,
  dieselben AUCs mit der gezogenen Wahrscheinlichkeit (ps), nach Tiefe.
Ausgabe: ergebnisse/kopplung_N31.json
  python 111_kopplung.py --selbsttest   # künstliche Daten mit bekannter Antwort
  python 111_kopplung.py --trocken      # nur Zählungen (auch Aussagen hinter Schildern), keine Kennzahlen
  python 111_kopplung.py                # Auswertung
"""
import argparse
import json
import math
import os
import re
import sys

import numpy as np

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(HIER)
ERG = os.path.join(WURZEL, "ergebnisse")
QUELLEN = {"eigen": "zucken_WT-A_ergo-zigA.jsonl", "MIT": "zucken_MIT_mit-wt.jsonl"}
LAEUFE = {"eigen": ["s3-wta-161-210", "s3-wta-211-260", "s3-wta-261-300"], "MIT": ["s3-mit-161-260", "s3-mit-261-300"]}
SCHILD_MITTE = re.compile(r"(?:the final answer is|the answer is|so the answer|therefore,? the answer)\s*:?\s*\$?\\?(?:boxed\{)?",
                          re.I)  # wörtlich wie 99_schilder_int.py
SCHILD_ABSTAND = 15
SEED, N_BOOT = 20261109, 10000
TIEFEN = [(0, 1000), (1000, 2000), (2000, 4000), (4000, 8000), (8000, 10 ** 9)]


def schild_stellen(name):
    """Token-Positionen der eigenen Schilder je Lauf (wie 99, S3: Text aus gen_ids bis n_mess, Regex, Ende → Token)."""
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(os.path.join(WURZEL, "modelle", "Qwen3.5-0.8B"))
    bedarf = {}  # Lauf-ID -> n_mess (gestreamt, damit nie alle Läufe zugleich im Speicher liegen)
    for zeile in open(os.path.join(ERG, QUELLEN[name]), encoding="utf-8"):
        zz = json.loads(zeile)
        bedarf[zz["id"]] = zz["n_mess"]
    cache = {}

    def stueck(t):
        if t not in cache:
            cache[t] = tok.decode([t])
        return cache[t]

    stellen = {}
    for d in LAEUFE[name]:
        for z in open(os.path.join(ERG, d, "ergebnisse.jsonl"), encoding="utf-8"):
            r = json.loads(z)
            if r["id"] not in bedarf or r["id"] in stellen:
                continue
            st = [stueck(t) for t in r["gen_ids"][:bedarf[r["id"]]]]
            gr = np.cumsum([len(s) for s in st]) if st else np.array([0])
            stellen[r["id"]] = [int(np.searchsorted(gr, m.end() - 1, side="right")) for m in SCHILD_MITTE.finditer("".join(st))]
    return stellen, len(set(bedarf) - set(stellen))


def lade(name, stellen=None):
    """Liste von Läufen; je Lauf Arrays ok, K, F, Fs (gezogen), t, schild. Aussagen ohne bekannte Wahrheit oder ohne Ablation
    fallen weg."""
    laeufe, fehlend = [], 0
    for zeile in open(os.path.join(ERG, QUELLEN[name]), encoding="utf-8"):
        lauf = json.loads(zeile)
        sch = (stellen or {}).get(lauf["id"], [])
        ok, K, F, Fs, t, s = [], [], [], [], [], []
        for a in lauf.get("aussagen", []):
            if a.get("ok") not in (True, False):
                continue
            pa, pb = a.get("p_t_abl"), a.get("p_arg_abl")
            if pa is None and pb is None:
                fehlend += 1
                continue
            p = max(x for x in (pa, pb) if x is not None)
            ps = max((x for x in (a.get("ps_t_abl"), a.get("ps_arg_abl")) if x is not None), default=0.0)
            ok.append(bool(a["ok"]))
            K.append(float(a["zT_max"]))
            F.append(math.log10(max(p, 1e-30)))
            Fs.append(float(ps))
            t.append(int(a["t"]))
            s.append(any(0 <= a["t"] - ts <= SCHILD_ABSTAND for ts in sch))
        laeufe.append({"id": lauf["id"], "ok": np.array(ok, bool), "K": np.array(K), "F": np.array(F), "Fs": np.array(Fs),
                       "t": np.array(t), "schild": np.array(s, bool)})
    return laeufe, fehlend


def rang(x):
    """Ränge 1..n, Bindungen gemittelt (vektorisiert)."""
    x = np.asarray(x, float)
    ordnung = np.argsort(x, kind="mergesort")
    xs = x[ordnung]
    neu = np.r_[True, xs[1:] != xs[:-1]]
    gruppe = np.cumsum(neu) - 1
    start = np.flatnonzero(neu)
    ende = np.r_[start[1:], len(xs)] - 1
    r = np.empty(len(x))
    r[ordnung] = ((start + ende) / 2 + 1)[gruppe]
    return r


def auc(werte, y):
    """Mann-Whitney-AUC P(Wert_richtig > Wert_falsch), Bindungen gemittelt."""
    y = np.asarray(y, bool)
    n1, n0 = y.sum(), (~y).sum()
    if n1 == 0 or n0 == 0:
        return float("nan")
    r = rang(werte)
    return float((r[y].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def spearman(a, b):
    if len(a) < 3:
        return float("nan")
    return float(np.corrcoef(rang(a), rang(b))[0, 1])


def zusammen(laeufe, feld, auswahl=None):
    teile = [l[feld] if auswahl is None else l[feld][auswahl(l)] for l in laeufe]
    return np.concatenate(teile) if teile else np.array([])


def boot_auc(laeufe, feld, rng, n_boot=N_BOOT, auswahl=None):
    n = len(laeufe)
    werte = np.empty(n_boot)
    for b in range(n_boot):
        zug = [laeufe[i] for i in rng.integers(0, n, n)]
        werte[b] = auc(zusammen(zug, feld, auswahl), zusammen(zug, "ok", auswahl))
    return werte


def band_K(a):
    return "stark" if a >= 0.75 else ("schwach" if a >= 0.65 else "zerstreut")


def klasse(a):
    return "koppelt" if a >= 0.70 else ("blind" if a < 0.60 else "offen")


DEUTUNG = {
    ("blind", "koppelt"): "eigen blind, MIT koppelt: MITs Vorteil ist eine Kopplung von Wissen und Festlegen; Bau dieser Kopplung im "
                          "eigenen Hinterzimmer",
    ("blind", "blind"): "beide blind: MIT legt sich aus anderen Gründen fest (Schilder, Prüf-Floskeln); Fokus Schilder",
    ("koppelt", "blind"): "Asymmetrie umgekehrt: unser Modell koppelt, MIT nicht; MITs Vorteil liegt dann nicht in der Kopplung",
    ("koppelt", "koppelt"): "beide koppeln: „Wissen ist nicht Festlegen“ für das Festlegen-Signal selbst geschwächt; die Lücke liegt "
                            "woanders (z. B. Stärke statt Richtung)",
}


def auswerten(daten, rng, n_boot=N_BOOT):
    erg = {"lesart": "MEILENSTEIN2_N31_N32.md + MEILENSTEIN2_ZUSATZ_WREN.md (N31)", "quellen": {}}
    boots = {}
    schild = lambda l: l["schild"]
    richtig = lambda l: l["ok"]
    for name, laeufe in daten.items():
        ok = zusammen(laeufe, "ok")
        bF = boot_auc(laeufe, "F", rng, n_boot)
        boots[name] = bF
        aK = auc(zusammen(laeufe, "K"), ok)
        okS = zusammen(laeufe, "ok", schild)
        bS = boot_auc(laeufe, "F", rng, n_boot, schild)
        aFS = auc(zusammen(laeufe, "F", schild), okS)
        e = {
            "aussagen": int(len(ok)), "richtig": int(ok.sum()), "laeufe": len(laeufe),
            "AUC_F": round(auc(zusammen(laeufe, "F"), ok), 4),
            "AUC_F_KI95": [round(float(np.nanpercentile(bF, 2.5)), 4), round(float(np.nanpercentile(bF, 97.5)), 4)],
            "bootstrap_ohne_beide_klassen": int(np.isnan(bF).sum()),  # Zusatz 2 (WREN A4): übersprungen, gezählt
            "AUC_K": round(aK, 4), "K_band": band_K(aK),
            "AUC_Fs_gezogen": round(auc(zusammen(laeufe, "Fs"), ok), 4),
            "spearman_K_F_richtige": round(spearman(zusammen(laeufe, "K", richtig), zusammen(laeufe, "F", richtig)), 4),
            "schild": {"aussagen": int(len(okS)), "richtig": int(okS.sum()),
                       "AUC_F": round(aFS, 4) if not math.isnan(aFS) else None,
                       "AUC_F_KI95": [round(float(np.nanpercentile(bS, 2.5)), 4), round(float(np.nanpercentile(bS, 97.5)), 4)],
                       "bootstrap_ohne_beide_klassen": int(np.isnan(bS).sum()),
                       "AUC_K": round(auc(zusammen(laeufe, "K", schild), okS), 4) if len(okS) else None,
                       "urteil": ("zu wenig Daten" if math.isnan(aFS) else
                                  {"koppelt": "koppelt am Schild", "blind": "blind am Schild", "offen": "offen"}[klasse(aFS)])},
            "nach_tiefe": {},
        }
        for lo, hi in TIEFEN:
            wahl = lambda l, lo=lo, hi=hi: (l["t"] >= lo) & (l["t"] < hi)
            okt = zusammen(laeufe, "ok", wahl)
            e["nach_tiefe"][f"{lo}-{hi}"] = {"n": int(len(okt)), "richtig": int(okt.sum()),
                                             "AUC_F": round(auc(zusammen(laeufe, "F", wahl), okt), 4),
                                             "AUC_K": round(auc(zusammen(laeufe, "K", wahl), okt), 4)}
        erg["quellen"][name] = e
    q = erg["quellen"]
    fe, fm = q["eigen"]["AUC_F"], q["MIT"]["AUC_F"]
    h6a = {"blind": "Festlegen blind (bestätigt)", "koppelt": "Festlegen gekoppelt (widerlegt)", "offen": "offen"}[klasse(fe)]
    h6b = {"koppelt": "MIT koppelt", "blind": "MIT ebenfalls blind", "offen": "offen"}[klasse(fm)]
    diff = boots["MIT"] - boots["eigen"]
    lo, hi = float(np.nanpercentile(diff, 2.5)), float(np.nanpercentile(diff, 97.5))
    d = fm - fe
    if d >= 0.10 and lo > 0:
        h6c = "MIT koppelt stärker"
    elif d <= -0.10 and hi < 0:  # Zusatz 2 (WREN A13): spiegelbildlich benannt
        h6c = "eigen koppelt stärker"
    elif lo <= 0 <= hi:
        h6c = "kein Unterschied nachweisbar"
    else:
        h6c = "offen (Fall vorab nicht benannt)"
    deutung = DEUTUNG.get((klasse(fe), klasse(fm)), "offen: mindestens eine Seite liegt zwischen 0,60 und 0,70")
    erg["urteil"] = {"H6a_eigen": h6a, "K_band_eigen": q["eigen"]["K_band"], "H6b_MIT": h6b, "K_band_MIT": q["MIT"]["K_band"],
                     "H6c_unterschied": h6c, "AUC_F_MIT_minus_eigen": round(d, 4), "KI95": [round(lo, 4), round(hi, 4)],
                     "deutung": deutung,
                     "schild_eigen": q["eigen"]["schild"]["urteil"], "schild_MIT": q["MIT"]["schild"]["urteil"]}
    return erg


def selbsttest():
    """Künstliche Läufe mit bekannter Antwort; berührt keine echten Daten.
    Fall 1: eigen blind, MIT gekoppelt → H6a bestätigt, H6b koppelt, H6c MIT stärker, Deutung „eigen blind, MIT koppelt“.
    Fall 2: beide blind → H6b blind, H6c kein Unterschied, Deutung „beide blind“.
    Fall 3: MIT koppelt nur am Schild → Schild-Urteil MIT „koppelt am Schild“, eigen „blind am Schild“."""
    rng = np.random.default_rng(11)

    def quelle(kopplung, nur_schild=False, n_lauf=140, n_aussage=60):
        laeufe = []
        for _ in range(n_lauf):
            schild = rng.random(n_aussage) < 0.10
            ok = rng.random(n_aussage) < np.where(schild, 0.45, 0.05)
            K = np.where(ok, 1.5, -2.0) + rng.standard_normal(n_aussage)
            k = kopplung * (schild if nur_schild else 1.0)
            F = k * K + rng.standard_normal(n_aussage) - 10
            laeufe.append({"id": "x", "ok": ok, "K": K, "F": F, "Fs": np.zeros(n_aussage), "t": rng.integers(0, 9000, n_aussage),
                           "schild": schild})
        return laeufe

    faelle = [("Fall 1", {"eigen": quelle(0.0), "MIT": quelle(1.0)},
               {"H6a_eigen": "Festlegen blind (bestätigt)", "H6b_MIT": "MIT koppelt", "H6c_unterschied": "MIT koppelt stärker"}),
              ("Fall 2", {"eigen": quelle(0.0), "MIT": quelle(0.0)},
               {"H6b_MIT": "MIT ebenfalls blind", "H6c_unterschied": "kein Unterschied nachweisbar"}),
              ("Fall 3", {"eigen": quelle(0.0), "MIT": quelle(1.5, nur_schild=True)},
               {"schild_MIT": "koppelt am Schild", "schild_eigen": "blind am Schild"}),
              ("Fall 4 (Zusatz 2)", {"eigen": quelle(1.0), "MIT": quelle(0.0)},
               {"H6a_eigen": "Festlegen gekoppelt (widerlegt)", "H6c_unterschied": "eigen koppelt stärker"}),
              ("Fall 5 (Zusatz 2)", {"eigen": quelle(1.0), "MIT": quelle(1.0)},
               {"H6b_MIT": "MIT koppelt", "H6c_unterschied": "kein Unterschied nachweisbar"})]
    gut = True
    for name, daten, soll in faelle:
        u = auswerten(daten, np.random.default_rng(SEED), n_boot=300)["urteil"]
        treffer = all(u[k] == v for k, v in soll.items())
        print(f"{name}: {'ok' if treffer else 'FALSCH'} | " + " | ".join(f"{k}: {u[k]}" for k in soll) + f" | Deutung: {u['deutung'][:40]}…")
        gut &= treffer
    print("Selbsttest", "BESTANDEN" if gut else "NICHT BESTANDEN")
    return gut


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--trocken", action="store_true", help="nur zählen, keine Kennzahlen")
    ap.add_argument("--selbsttest", action="store_true", help="Methode an künstlichen Daten mit bekannter Antwort prüfen")
    a = ap.parse_args()
    if a.selbsttest:
        sys.exit(0 if selbsttest() else 1)
    daten = {}
    for name in QUELLEN:
        stellen, ohne = schild_stellen(name)
        laeufe, fehlend = lade(name, stellen)
        daten[name] = laeufe
        ok = zusammen(laeufe, "ok")
        okS = zusammen(laeufe, "ok", lambda l: l["schild"])
        print(f"{name}: {len(laeufe)} Läufe, {len(ok)} Aussagen ({int(ok.sum())} richtig); hinter eigenem Schild {len(okS)} "
              f"({int(okS.sum())} richtig); Schilder gesamt {sum(len(v) for v in stellen.values())}; Läufe ohne Text {ohne}; "
              f"ohne Ablation verworfen {fehlend}")
    if a.trocken:
        print("Trocken: keine Kennzahlen berechnet.")
        return
    erg = auswerten(daten, np.random.default_rng(SEED))
    json.dump(erg, open(os.path.join(ERG, "kopplung_N31.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(erg["urteil"], ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
