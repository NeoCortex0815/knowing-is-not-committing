"""Urteil Schritt 3: ERGORE gegen MIT auf den frischen MATH-500-Aufgaben 161–300 und auf 1–300 zusammen; dazu WT-A.
Lesart vorab (ANNAHMEN 07.11. 14:16 und 14:21, Argon-Ergänzungen 14:58), gleich wie 46_urteil160:
  geknackt            – ERGORE > MIT und gepaarter McNemar-Test p < 0,05
  MIT-Niveau erreicht – ERGORE ≥ MIT − ⌊2,5 % der Aufgaben⌋ (140: −3, 300: −7) und MIT NICHT signifikant besser (p ≥ 0,05)
  nicht erreicht      – sonst
Blöcke: Laptop 161–260, MiniPC 261–300 (jede Aufgabe für alle Modelle auf derselben Maschine); Paarvergleiche je Block, dann zusammen.
WT-A: Lesart wie K1–K3 des WT-A-Tests gegen ERGORE und MIT (K1: ≥ Gegner − 3; K2: Zünd-Quote/Präzision wie 70_wta_urteil;
K3: Tokens beidseits gelöst, Vorzeichentest einseitig). Als BESTÄTIGUNG nur, wenn ergebnisse/wta_urteil.json „tor_wta“ = true;
sonst beschreibend. Tokens immer doppelt (alle Aufgaben / gemeinsam gelöst).
  python 73_urteil300.py
"""
import importlib.util
import json
import math
import os
from math import comb

import numpy as np

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(HIER)
ERG = os.path.join(WURZEL, "ergebnisse")
S3 = {
    "MIT": {"Laptop 161–260": ["s3-mit-161-260"], "MiniPC 261–300": ["s3-mit-261-300"]},
    "ERGORE": {"Laptop 161–260": ["s3-ergore-161-260"], "MiniPC 261–300": ["s3-ergore-261-300"]},
    "WT-A": {"Laptop 161–260": ["s3-wta-161-210", "s3-wta-211-260"], "MiniPC 261–300": ["s3-wta-261-300"]},
}
ALT = {"MIT": ["mit-vstil-L", "mit-vstil-L-b", "mit-vstil-L-c"], "ERGORE": ["tag2-test40-kw75", "kw75-b", "kw75-c"],
       "WT-A": ["wta-m500-001-080", "wta-m500-081-160"]}
SOLL = {"Laptop 161–260": 100, "MiniPC 261–300": 40}


def lade(dirs):
    R = {}
    for d in dirs:
        p = os.path.join(ERG, d, "ergebnisse.jsonl")
        if os.path.exists(p):
            R.update({json.loads(z)["id"]: json.loads(z) for z in open(p, encoding="utf-8")})
    return R


def mcnemar(a, b):
    n = a + b
    return min(1.0, 2 * sum(comb(n, x) for x in range(0, min(a, b) + 1)) / 2 ** n) if n else 1.0


def tokens(r):
    return int(r.get("tokens") or len(r["gen_ids"]))


def vergleich(name, A, B, na, nb, regel=True):
    ids = sorted(set(A) & set(B))
    n = len(ids)
    a = sum(bool(A[i]["korrekt"]) for i in ids)
    b = sum(bool(B[i]["korrekt"]) for i in ids)
    x = sum(bool(A[i]["korrekt"]) and not B[i]["korrekt"] for i in ids)
    y = sum(bool(B[i]["korrekt"]) and not A[i]["korrekt"] for i in ids)
    p = mcnemar(x, y)
    d = (x - y) / n if n else 0.0
    se = math.sqrt(max(0.0, (x + y) / n - d * d) / n) if n else 0.0
    gem = [i for i in ids if A[i]["korrekt"] and B[i]["korrekt"]]
    w = sum(tokens(A[i]) < tokens(B[i]) for i in gem)
    m = sum(tokens(A[i]) > tokens(B[i]) for i in gem)
    p_tok = sum(comb(w + m, k) for k in range(w, w + m + 1)) / 2 ** (w + m) if w + m else 1.0
    out = {"n": n, na: a, nb: b, f"nur_{na}": x, f"nur_{nb}": y, "p": p,
           "tokens_alle": [float(np.mean([tokens(A[i]) for i in ids])) if ids else None, float(np.mean([tokens(B[i]) for i in ids])) if ids else None],
           "tokens_gemeinsam": [float(np.mean([tokens(A[i]) for i in gem])) if gem else None, float(np.mean([tokens(B[i]) for i in gem])) if gem else None],
           "tokens_weniger": w, "tokens_mehr": m, "p_tokens_einseitig": p_tok}
    print(f"== {name}: {n} Aufgaben | {na} {a} ({100 * a / max(1, n):.1f} %) gegen {nb} {b} ({100 * b / max(1, n):.1f} %) | "
          f"nur {na} {x}, nur {nb} {y}, McNemar p = {p:.4f} | Differenz {100 * d:+.1f} Punkte, 95 % "
          f"[{100 * (d - 1.96 * se):+.1f}; {100 * (d + 1.96 * se):+.1f}]")
    print(f"   Tokens alle Ø {out['tokens_alle'][0] or 0:.0f} gegen {out['tokens_alle'][1] or 0:.0f} | gemeinsam gelöst ({len(gem)}) Ø "
          f"{out['tokens_gemeinsam'][0] or 0:.0f} gegen {out['tokens_gemeinsam'][1] or 0:.0f} (weniger {w}, mehr {m}, p einseitig {p_tok:.4f})")
    if regel:
        tol = math.floor(0.025 * n)
        if a > b and p < 0.05:
            u = f"GEKNACKT – {na} signifikant über {nb}"
        elif a >= b - tol and not (b > a and p < 0.05):
            u = f"{nb}-NIVEAU ERREICHT (Grenze −{tol})"
        else:
            u = "NICHT ERREICHT"
        out["urteil"] = u
        print(f"URTEIL {name}: {u}")
    return out


def main():
    import sys
    aus = os.path.join(ERG, "urteil300.json")
    if "--codetest" in sys.argv:  # nur Programmtest mit ALTEN Läufen (1–160), schreibt urteil300_CODETEST.json
        S3["MIT"] = {"Laptop 161–260": ["mit-vstil-L-c", "mit-vstil-L-b"], "MiniPC 261–300": ["mit-vstil-L"]}
        S3["ERGORE"] = {"Laptop 161–260": ["kw75-c", "kw75-b"], "MiniPC 261–300": ["tag2-test40-kw75"]}
        S3["WT-A"] = {"Laptop 161–260": ["kw75-c"], "MiniPC 261–300": []}
        aus = os.path.join(ERG, "urteil300_CODETEST.json")
    D = {m: {b: lade(ds) for b, ds in bl.items()} for m, bl in S3.items()}
    voll = True
    for m, bl in D.items():
        for b, R in bl.items():
            print(f"{m:6s} {b}: {len(R)}/{SOLL[b]}" + (f" richtig {sum(bool(r['korrekt']) for r in R.values())}" if len(R) >= SOLL[b] else ""))
            voll = voll and (len(R) >= SOLL[b] or m == "WT-A")
    if not voll:
        raise SystemExit("MIT/ERGORE unvollständig – kein Urteil (keine Zwischenblicke).")
    erg = {}
    for b in SOLL:
        erg[f"ERGORE gegen MIT · {b}"] = vergleich(f"{b} (beschreibend je Block)", D["ERGORE"][b], D["MIT"][b], "ERGORE", "MIT", regel=False)
    s3 = {m: {k: v for R in bl.values() for k, v in R.items()} for m, bl in D.items()}
    erg["ERGORE gegen MIT · 161–300"] = vergleich("161–300 (frisch, Hauptaussage)", s3["ERGORE"], s3["MIT"], "ERGORE", "MIT")
    alt = {m: lade(ds) for m, ds in ALT.items()}
    alle = {m: {**alt[m], **s3[m]} for m in ("ERGORE", "MIT")}
    erg["ERGORE gegen MIT · 1–300"] = vergleich("1–300 zusammen (1–260 Laptop, 261–300 MiniPC)", alle["ERGORE"], alle["MIT"], "ERGORE", "MIT")
    print("Prognose (14:16): gleichauf (|Differenz| ≤ 5 Aufgaben auf 140), ERGORE 10–15 % weniger Tokens.")
    # WT-A
    tor = None
    p_tor = os.path.join(ERG, "wta_urteil.json")
    if os.path.exists(p_tor):
        tor = bool(json.load(open(p_tor, encoding="utf-8")).get("tor_wta"))
    status = "BESTÄTIGUNG" if tor else "BESCHREIBEND"
    n_wta = len(s3["WT-A"])
    print(f"\n== WT-A auf 161–300: {n_wta}/140 Läufe | Lesart: {status} (Tor aus wta_urteil.json: {tor})")
    if n_wta:
        for gegner in ("ERGORE", "MIT"):
            v = vergleich(f"WT-A gegen {gegner} · 161–300 [{status}]", s3["WT-A"], s3[gegner], "WT-A", gegner, regel=False)
            v["K1"] = v["WT-A"] >= v[gegner] - 3
            v["K3"] = v["p_tokens_einseitig"] < 0.05 and v["tokens_weniger"] > v["tokens_mehr"]
            print(f"   K1 (≥ {gegner} − 3): {'ERFÜLLT' if v['K1'] else 'NICHT erfüllt'} | K3 Tokens: {'ERFÜLLT' if v['K3'] else 'NICHT erfüllt'}")
            erg[f"WT-A gegen {gegner} · 161–300"] = v
        # K2 wie 70_wta_urteil (Zünd-Quote, Präzision) auf den WT-A-Läufen
        wm_s = importlib.util.spec_from_file_location("wm", os.path.join(HIER, "42_wahrheitsmelder.py"))
        wm = importlib.util.module_from_spec(wm_s)
        wm_s.loader.exec_module(wm)
        ev = wm.lade("ev", os.path.join(WURZEL, "eval", "03_eval.py"))
        import transformers as tf
        tok = tf.AutoTokenizer.from_pretrained(os.path.join(WURZEL, "modelle", "Qwen3.5-0.8B"))
        gel = zue = sch = sch_r = 0
        for r in s3["WT-A"].values():
            st = [tok.decode([t]) for t in r["gen_ids"]]
            text = "".join(st)
            zc = text.find("</think>")
            gr = np.cumsum([len(s) for s in st]) if st else np.array([0])
            ks = [(s0, e, c) for (s0, e, c) in wm.kandidaten_mit_ende(text) if zc < 0 or s0 < zc]
            ok = [bool(ev.korrekt(c, r["gold"])) or bool(ev.korrekt(wm.bereinige_kandidat(c), r["gold"])) for (_, _, c) in ks]
            gel += any(ok)
            if zc < 0 or not ks:
                continue
            t_zu = int(np.searchsorted(gr, zc, side="right"))
            tl = min(int(np.searchsorted(gr, ks[-1][1] - 1, side="right")), len(st) - 1)
            if t_zu - tl <= 64:
                sch += 1
                sch_r += ok[-1]
                zue += ok[-1]
        print(f"   K2 WT-A: Zünd-Quote {100 * zue / gel if gel else 0:.0f} % [{zue}/{gel}], Präzision {100 * sch_r / sch if sch else 0:.0f} % [{sch_r}/{sch}]")
        erg["WT-A K2"] = {"gelegenheiten": gel, "zuendungen": zue, "schnell": sch, "schnell_richtig": sch_r}
        if alt["WT-A"] and set(alt["MIT"]) <= set(alt["WT-A"]):
            w_alle = {**alt["WT-A"], **s3["WT-A"]}
            for gegner in ("ERGORE", "MIT"):
                erg[f"WT-A gegen {gegner} · 1–300"] = vergleich(f"WT-A gegen {gegner} · 1–300 [1–160 beschreibend]", w_alle, alle[gegner],
                                                               "WT-A", gegner, regel=False)
    erg["wta_lesart"] = status
    json.dump(erg, open(aus, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(f"gespeichert: {aus}")


if __name__ == "__main__":
    main()
