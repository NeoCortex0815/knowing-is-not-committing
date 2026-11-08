"""WT-A-Urteil (Set B, 60 Aufgaben, 0,6, 32k, Seed 0). Lesart vorab in ANNAHMEN (07.11. 13:58, Go 14:01, Prognosen 14:03,
K2-Ergänzung 14:58 – alles vor der ersten Auswertung eines WT-A-Laufs).
Blöcke (Paarvergleiche nur innerhalb eines Blocks, dann zusammengefasst):
  Block 1 Laptop, Aufgaben 1–30:   eigen = setB30-eigen-t06,   WT-A = setB30-wta-t06
  Block 2 MiniPC, Aufgaben 31–60:  eigen = minipc-b2-eigen-t06, WT-A = minipc-b2-wta-t06 (vom MiniPC kopiert)
K0 Mechanik: Sofort-Abschlüsse WT-A ≤ eigen + 1 je Block; frühe Abschlüsse ohne Kandidat (`</think>` in den ersten 500 Denk-Tokens
   ohne Kandidat davor, Sofort-Abschlüsse eingeschlossen) ≤ eigen + 2 gesamt.
   Sofort-Abschluss = `</think>` unter den ersten 3 erzeugten Tokens.
K1 kein Schaden: richtig WT-A ≥ eigen − 3 (60 Aufgaben).
K2 WT wirkt: (a) Zünd-Quote ≥ 60 % und Präzision ≥ 75 % ODER (b) Zünd-Quote ≥ 50 %, Präzision ≥ 85 % und K0, K1, K3 bestanden;
   weniger als 10 Gelegenheiten → „nicht beurteilbar“. Zünd-Quote = Anteil der WT-A-Läufe mit richtigem Kandidaten im Denken,
   deren letzter Kandidat vor `</think>` richtig ist und höchstens 64 Tokens davor endet; Präzision = Anteil der schnellen
   Abschlüsse (≤ 64 Tokens nach irgendeinem Kandidaten) an richtigen Kandidaten (wie 62_v22_urteil).
K3 Ersparnis: beidseits gelöst weniger Tokens, Vorzeichentest einseitig p < 0,05.
K4 Sonde (Schicht 13, eingefroren): AUC auf WT-A-Kandidaten ≥ AUC auf eigen-Kandidaten − 0,03 (je Block, soweit gesammelt).
Tor für Schritt 3 (161–300 als Bestätigung) und die Nacht (WT-A auf 1–160): K0 UND K1 UND K2.
Beschreibend: Prüfstelle 5 (zweites `</think>`, kein boxed im Antwortteil), Tokens doppelt (alle / gemeinsam gelöst), Prognosen.
Ohne vollständige Blöcke gibt es KEIN Urteil (keine Zwischenblicke); --stand zeigt nur die Vollständigkeit.
  python 70_wta_urteil.py [--stand]
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
BLOECKE = {
    "Block 1 (Laptop, 1–30)": {"eigen": "setB30-eigen-t06", "WT-A": "setB30-wta-t06", "n": 30,
                               "sammlung": "setB30_wta_kandidaten.npz"},
    "Block 2 (MiniPC, 31–60)": {"eigen": "minipc-b2-eigen-t06", "WT-A": "minipc-b2-wta-t06", "n": 30,
                                "sammlung": "setB60b2_wta_kandidaten.npz"},
}


def lade_mod(name, pfad):
    s = importlib.util.spec_from_file_location(name, pfad)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


def lade(d):
    p = os.path.join(ERG, d, "ergebnisse.jsonl")
    return {json.loads(z)["id"]: json.loads(z) for z in open(p, encoding="utf-8")} if os.path.exists(p) else {}


def mcnemar(a, b):
    n = a + b
    return min(1.0, 2 * sum(comb(n, x) for x in range(0, min(a, b) + 1)) / 2 ** n) if n else 1.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stand", action="store_true", help="nur Vollständigkeit zeigen, keine Kennzahlen")
    ap.add_argument("--sonde", default=os.path.join(ERG, "wahrheitsmelder_eingefroren.npz"))
    ap.add_argument("--codetest", action="store_true",
                    help="nur Programmtest mit ALTEN Läufen (Gatter/V2.1, ERGORE/V2.2); schreibt wta_urteil_CODETEST.json")
    a = ap.parse_args()
    aus = os.path.join(ERG, "wta_urteil.json")
    if a.codetest:
        BLOECKE["Block 1 (Laptop, 1–30)"].update(eigen="setB-gatter-t06", **{"WT-A": "setB30-v21-t06"}, sammlung="setB30_wt_kandidaten.npz")
        BLOECKE["Block 2 (MiniPC, 31–60)"].update(eigen="setB-ergore-t06", **{"WT-A": "setB30-v22-t06"}, sammlung="gibt_es_nicht.npz")
        aus = os.path.join(ERG, "wta_urteil_CODETEST.json")
    D = {b: {m: lade(c[m]) for m in ("eigen", "WT-A")} for b, c in BLOECKE.items()}
    voll = True
    for b, c in BLOECKE.items():
        z = {m: len(D[b][m]) for m in ("eigen", "WT-A")}
        print(f"{b}: eigen {z['eigen']}/{c['n']}, WT-A {z['WT-A']}/{c['n']}")
        voll = voll and all(v >= c["n"] for v in z.values())
    if a.stand:
        return
    if not voll:
        raise SystemExit("Blöcke unvollständig – kein Urteil (Vorab-Regel: keine Zwischenblicke).")

    wm = lade_mod("wm", os.path.join(HIER, "42_wahrheitsmelder.py"))
    ev = wm.lade("ev", os.path.join(WURZEL, "eval", "03_eval.py"))
    import transformers as tf
    tok = tf.AutoTokenizer.from_pretrained(os.path.join(WURZEL, "modelle", "Qwen3.5-0.8B"))
    ZU = tok.convert_tokens_to_ids("</think>")

    def analyse(r):
        gen = r["gen_ids"]
        st = [tok.decode([t]) for t in gen]
        text = "".join(st)
        zc = text.find("</think>")
        gr = np.cumsum([len(s) for s in st]) if st else np.array([0])
        ks = [(s0, e, c) for (s0, e, c) in wm.kandidaten_mit_ende(text) if zc < 0 or s0 < zc]
        ok = [bool(ev.korrekt(c, r["gold"])) or bool(ev.korrekt(wm.bereinige_kandidat(c), r["gold"])) for (_, _, c) in ks]
        f = {"korrekt": bool(r["korrekt"]), "tokens": int(r.get("tokens", len(gen))), "gelegenheit": any(ok),
             "zuendung": False, "schnell": False, "schnell_richtig": False, "sofort": False, "frueh_ohne": False,
             "zweites_zu": sum(1 for t in gen if t == ZU) >= 2, "zu": zc >= 0,
             "ohne_boxed_nach_zu": zc >= 0 and "\\boxed" not in text[zc:], "denk_tokens": None}
        if zc < 0:
            return f
        t_zu = int(np.searchsorted(gr, zc, side="right"))
        f["denk_tokens"] = t_zu
        f["sofort"] = ZU in gen[:3]
        f["frueh_ohne"] = t_zu < 500 and not ks
        if ks:
            tl = min(int(np.searchsorted(gr, ks[-1][1] - 1, side="right")), len(st) - 1)
            if t_zu - tl <= 64:
                f["schnell"] = True
                f["schnell_richtig"] = f["zuendung"] = ok[-1]
        return f

    # nur gepaarte Aufgaben (gleiche Aufgabe in beiden Modellen desselben Blocks)
    F = {b: {m: {i: analyse(r) for i, r in D[b][m].items() if i in set(D[b]["eigen"]) & set(D[b]["WT-A"])}
             for m in ("eigen", "WT-A")} for b in BLOECKE}
    erg = {"bloecke": {}}

    def summe(m, feld, bl=None):
        return sum(int(x[feld]) for b in (bl or BLOECKE) for x in F[b][m].values())

    for b in BLOECKE:
        zeile = {}
        for m in ("eigen", "WT-A"):
            V = list(F[b][m].values())
            dk = [x["denk_tokens"] for x in V if x["denk_tokens"] is not None]
            zeile[m] = {"richtig": sum(x["korrekt"] for x in V), "sofort": sum(x["sofort"] for x in V),
                        "frueh_ohne_kandidat": sum(x["frueh_ohne"] for x in V), "nie_zu": sum(not x["zu"] for x in V),
                        "gelegenheiten": sum(x["gelegenheit"] for x in V), "zuendungen": sum(x["zuendung"] for x in V),
                        "schnell": sum(x["schnell"] for x in V), "schnell_richtig": sum(x["schnell_richtig"] for x in V),
                        "zweites_zu": sum(x["zweites_zu"] for x in V), "ohne_boxed_nach_zu": sum(x["ohne_boxed_nach_zu"] for x in V),
                        "tokens_mittel": round(float(np.mean([x["tokens"] for x in V]))),
                        "denk_tokens_median": int(np.median(dk)) if dk else None}
            print(f"  {b} {m:5s}: {zeile[m]}")
        erg["bloecke"][b] = zeile

    # K0
    k0_sofort = all(erg["bloecke"][b]["WT-A"]["sofort"] <= erg["bloecke"][b]["eigen"]["sofort"] + 1 for b in BLOECKE)
    fr_w, fr_e = summe("WT-A", "frueh_ohne"), summe("eigen", "frueh_ohne")
    k0 = k0_sofort and fr_w <= fr_e + 2
    # K1 und Paarvergleich je Block
    nur_w = nur_e = 0
    for b in BLOECKE:
        ids = sorted(set(F[b]["eigen"]) & set(F[b]["WT-A"]))
        nur_w += sum(F[b]["WT-A"][i]["korrekt"] and not F[b]["eigen"][i]["korrekt"] for i in ids)
        nur_e += sum(F[b]["eigen"][i]["korrekt"] and not F[b]["WT-A"][i]["korrekt"] for i in ids)
    r_w, r_e = summe("WT-A", "korrekt"), summe("eigen", "korrekt")
    k1 = r_w >= r_e - 3
    # K3 und Tokens doppelt
    weniger = mehr = 0
    tw, te, rel = [], [], []
    for b in BLOECKE:
        for i in set(F[b]["eigen"]) & set(F[b]["WT-A"]):
            w_, e_ = F[b]["WT-A"][i], F[b]["eigen"][i]
            if w_["korrekt"] and e_["korrekt"]:
                weniger += w_["tokens"] < e_["tokens"]
                mehr += w_["tokens"] > e_["tokens"]
                tw.append(w_["tokens"]); te.append(e_["tokens"]); rel.append(w_["tokens"] / max(e_["tokens"], 1) - 1)
    n3 = weniger + mehr
    p3 = sum(comb(n3, i) for i in range(weniger, n3 + 1)) / 2 ** n3 if n3 else 1.0
    k3 = p3 < 0.05 and weniger > mehr
    # K2
    gel, zue = summe("WT-A", "gelegenheit"), summe("WT-A", "zuendung")
    sch, sch_r = summe("WT-A", "schnell"), summe("WT-A", "schnell_richtig")
    zq = zue / gel if gel else 0.0
    praez = sch_r / sch if sch else 0.0
    gel_e, zue_e = summe("eigen", "gelegenheit"), summe("eigen", "zuendung")
    if gel < 10:
        k2, k2_text = False, "NICHT BEURTEILBAR (< 10 Gelegenheiten)"
    else:
        k2a = zq >= 0.60 and praez >= 0.75
        k2b = zq >= 0.50 and praez >= 0.85 and k0 and k1 and k3
        k2 = k2a or k2b
        k2_text = "ERFÜLLT (a)" if k2a else ("ERFÜLLT (b, Grenzfall-Regel)" if k2b else "NICHT erfüllt")
    print(f"URTEIL K0 Mechanik: {'ERFÜLLT' if k0 else 'NICHT erfüllt'} (Sofort je Block WT-A/eigen: "
          + ", ".join(f"{erg['bloecke'][b]['WT-A']['sofort']}/{erg['bloecke'][b]['eigen']['sofort']}" for b in BLOECKE)
          + f"; früh ohne Kandidat gesamt WT-A {fr_w}, eigen {fr_e})")
    print(f"URTEIL K1 kein Schaden: {'ERFÜLLT' if k1 else 'NICHT erfüllt'} (WT-A {r_w} gegen eigen {r_e}; nur WT-A {nur_w}, "
          f"nur eigen {nur_e}, McNemar p = {mcnemar(nur_w, nur_e):.3f})")
    print(f"URTEIL K2 WT wirkt: {k2_text} (Zünd-Quote {100 * zq:.0f} % [{zue}/{gel}], Präzision {100 * praez:.0f} % [{sch_r}/{sch}]; "
          f"Basis eigen {100 * zue_e / gel_e if gel_e else 0:.0f} % [{zue_e}/{gel_e}])")
    print(f"URTEIL K3 Ersparnis: {'ERFÜLLT' if k3 else 'NICHT erfüllt'} (beidseits gelöst {len(tw)}: "
          f"weniger {weniger}, mehr {mehr}, gleich {len(tw) - n3}, p einseitig {p3:.4f})")
    if tw:
        print(f"  Tokens beidseits gelöst ({len(tw)}): WT-A Ø {np.mean(tw):.0f}, eigen Ø {np.mean(te):.0f} "
              f"(Summe {100 * (sum(tw) / sum(te) - 1):+.0f} %, Median je Aufgabe {100 * np.median(rel):+.0f} %)")
    print(f"  Tokens alle Aufgaben: WT-A Ø {np.mean([x['tokens'] for b in BLOECKE for x in F[b]['WT-A'].values()]):.0f}, "
          f"eigen Ø {np.mean([x['tokens'] for b in BLOECKE for x in F[b]['eigen'].values()]):.0f}")
    print(f"  Prüfstelle 5 (Antwortteil): zweites </think> WT-A {summe('WT-A', 'zweites_zu')}, eigen {summe('eigen', 'zweites_zu')}; "
          f"kein boxed nach </think> WT-A {summe('WT-A', 'ohne_boxed_nach_zu')}, eigen {summe('eigen', 'ohne_boxed_nach_zu')}")
    erg.update({"K0": k0, "K1": k1, "K2": k2, "K2_text": k2_text, "K3": k3, "zuend_quote": zq, "gelegenheiten": gel,
                "zuendungen": zue, "praezision": praez, "schnell": sch, "schnell_richtig": sch_r, "basis_zuend_quote": zue_e / gel_e if gel_e else 0.0,
                "basis_gelegenheiten": gel_e, "richtig_wta": r_w, "richtig_eigen": r_e, "nur_wta": nur_w, "nur_eigen": nur_e,
                "p_mcnemar": mcnemar(nur_w, nur_e), "tokens_weniger": weniger, "tokens_mehr": mehr, "p_K3": p3,
                "tokens_gemeinsam_wta": float(np.mean(tw)) if tw else None, "tokens_gemeinsam_eigen": float(np.mean(te)) if te else None,
                "tokens_gemeinsam_median_rel": float(np.median(rel)) if rel else None})
    # K4
    S = np.load(a.sonde)
    k4, k4_teile = True, []
    for b, c in BLOECKE.items():
        p = os.path.join(ERG, c["sammlung"])
        if not os.path.exists(p):
            print(f"   Sonde {b}: Sammlung fehlt ({c['sammlung']}) – K4 für diesen Block ausstehend")
            continue
        Z = np.load(p)
        sc = ((Z["X_13"].astype(np.float64) - S["mu"]) / S["sd"]) @ S["w"] + S["b"]
        tags = np.array([l.split("/")[0] for l in Z["lauf"]])
        a_w = wm.auc(sc[tags == c["WT-A"]], Z["y"][tags == c["WT-A"]].astype(bool))
        a_e = wm.auc(sc[tags == c["eigen"]], Z["y"][tags == c["eigen"]].astype(bool))
        ok = bool(a_w >= a_e - 0.03)
        k4 = k4 and ok
        k4_teile.append(b)
        print(f"   Sonde {b}: AUC WT-A {a_w:.3f} ({(tags == c['WT-A']).sum()} Kandidaten) gegen eigen {a_e:.3f} "
              f"({(tags == c['eigen']).sum()}) – {'intakt' if ok else 'SCHLECHTER als eigen − 0,03'}")
        erg[f"auc_wta_{b}"], erg[f"auc_eigen_{b}"] = a_w, a_e
    print(f"URTEIL K4 Sonde: {'ERFÜLLT' if k4 and k4_teile else ('ausstehend' if not k4_teile else 'NICHT erfüllt')}"
          f"{'' if len(k4_teile) == len(BLOECKE) else ' (nur ' + ', '.join(k4_teile) + ')' if k4_teile else ''}")
    erg["K4"], erg["K4_bloecke"] = (k4 if k4_teile else None), k4_teile
    tor = bool(k0 and k1 and k2)
    erg["tor_wta"] = tor
    print(f"TOR (K0 ∧ K1 ∧ K2): {'OFFEN – WT-A zählt auf 161–300 als Bestätigung; WT-A auf 1–160 heute Nacht' if tor else 'ZU – WT-A auf 161–300 nur beschreibend; kein WT-A-Lauf auf 1–160'}")
    print("Prognosen (14:03) gegen Messung: Gelegenheiten eigen 18–25 → " + f"{gel_e}; Zünd-Quote 60–75 % → {100 * zq:.0f} %; "
          f"Präzision 85–95 % → {100 * praez:.0f} %; Treffer +0…+4 → {r_w - r_e:+d}; Tokens gemeinsam gelöst −20…−40 % → "
          + (f"{100 * (sum(tw) / sum(te) - 1):+.0f} %" if tw else "–"))
    json.dump(erg, open(aus, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(f"gespeichert: {aus}")


if __name__ == "__main__":
    main()
