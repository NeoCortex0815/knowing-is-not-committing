"""Ausschlussverfahren (08.11. nachts; NACHTRÄGLICH, beschreibend, nur Text; Nutzer ~01:05: „Ursache finden, warum die Präzision
bei den einen Aufgaben erreicht wurde und bei den anderen nicht“, „fehlt der Horizont?“, „größeres Kontextfenster → eher Lösung
und Zucken?“).
Keine Modell-Rechnung, keine Generierung. WT-A und MIT auf MATH-500 161–300 (Seed 0), gleiche Aufgaben.
Je Lauf (Denken = bis zum ersten </think>; Wert-Aussagen wie in 76 = alter Erkenner ∪ v2; Wahrheit aus dem Zwischenspeicher 80):
  - t1 = erstes Auftreten des richtigen Werts;
  - Erwähnungen, verschiedene Werte vor t1, Denk-Länge, Abschluss-Token;
  - letzte Wert-Aussage vor dem Abschluss: richtig? Abstand? Daraus „Abschluss am richtigen Wert“ (≤ 64 Tokens, wie H-WT2);
  - Antwortteil: \\boxed vorhanden? zweites </think>? Ende.
Gruppen bei WT-A (Läufe mit richtigem Wert im Denken):
  G1 = am richtigen Wert geschlossen (≤ 64 Tokens danach, letzte Aussage richtig)
  G2 = Wert da, aber dort nicht geschlossen
Vergleich G1 gegen G2: Position t1, Stufe, Fach, Antwort-Art, Konkurrenz-Werte vor t1, Zweifel-Wörter nach t1, Schluss-Rahmung vor t1.
Zusätzlich:
  - Abgabe-Verluste: am richtigen Wert geschlossen, aber nicht richtig abgegeben;
  - Kontext-Kurve: Anteil der Aufgaben mit richtigem Wert bis 2k/4k/8k/16k/24k/32k Tokens, für WT-A und MIT;
  - Horizont: Hat WT-A geschlossen, bevor MIT den Wert fand?
  python 83_ausschluss.py   → ergebnisse/ausschluss_wta_s3.json
"""
import collections
import importlib.util
import json
import os
import re

import numpy as np

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(HIER)
ERG = os.path.join(WURZEL, "ergebnisse")
S3 = {"WT-A": ["s3-wta-161-210", "s3-wta-211-260", "s3-wta-261-300"], "MIT": ["s3-mit-161-260", "s3-mit-261-300"]}
ZWEIFEL = re.compile(r"\b(Wait|But|Hmm|However|Actually|mistake|wrong|Let me (?:check|verify|double-check|re-?check|re-?evaluate))\b")
SCHLUSS = re.compile(r"\b(So|Therefore|Thus|Hence|answer|final|result|conclude)\b", re.I)


def lade_mod(name, pfad):
    s = importlib.util.spec_from_file_location(name, pfad)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


def antwort_art(gold):
    g = gold.strip().strip("$")
    if re.fullmatch(r"-?\d+", g.replace(",", "")):
        return "ganzzahl"
    if "\\frac" in g or "/" in g or re.fullmatch(r"-?\d*\.\d+", g):
        return "bruch/dezimal"
    if "\\sqrt" in g or "\\pi" in g:
        return "wurzel/pi"
    return "ausdruck/sonst"


def merkmale(r, tok, ZU, wm, k2, memo):
    g = r["gen_ids"]
    st = [tok.decode([t]) for t in g]
    gr = np.cumsum([len(s) for s in st]) if st else np.array([0])
    text = "".join(st)
    zc = text.find("</think>")
    zu_tok = g.index(ZU) if ZU in g else None
    denk = text if zc < 0 else text[:zc]
    antw = "" if zc < 0 else text[zc + len("</think>"):]
    A = []
    for (s0, e, c) in list(wm.kandidaten_mit_ende(denk)) + list(k2.wert_aussagen(denk)):
        t = min(int(np.searchsorted(gr, e - 1, side="right")), len(st) - 1)
        A.append((t, c, memo.get((c, r["gold"])), s0, e))
    A.sort(key=lambda x: (x[0], x[3]))
    ok_A = [x for x in A if x[2]]
    f = {"id": r["id"], "korrekt": bool(r["korrekt"]), "ende": r["ende"], "n_gen": len(g), "zu_tok": zu_tok,
         "denk_tokens": zu_tok if zu_tok is not None else len(g), "boxed_antwort": "\\boxed" in antw,
         "zweites_zu": antw.count("</think>"), "n_aussagen": len(A), "unbekannt": sum(1 for x in A if x[2] is None),
         "t1": ok_A[0][0] if ok_A else None, "erwaehnungen_richtig": len(ok_A)}
    if zc < 0:
        f["art"] = "nie geschlossen (" + r["ende"] + ")"
    elif not f["boxed_antwort"]:
        f["art"] = "geschlossen, keine Antwort (" + r["ende"] + ")"
    elif not f["korrekt"]:
        f["art"] = "geschlossen, falsche Antwort"
    else:
        f["art"] = "richtig"
    if ok_A:
        t1, _, _, s1, e1 = ok_A[0]
        f["konkurrenz_vor_t1"] = len({x[1].strip() for x in A if x[0] < t1 and x[2] is False})
        f["zweifel_nach_t1"] = len(ZWEIFEL.findall(denk[e1:e1 + 600]))
        f["schluss_vor_t1"] = bool(SCHLUSS.search(denk[max(0, s1 - 120):s1]))
    # 08.11. ~01:40 (Nutzer-Idee „Nachsicht“): wie oft stand der richtige Wert VOR dem Abschluss schon da? Und der Antwortteil?
    f["richtig_vor_zu"] = sum(1 for x in ok_A if zu_tok is not None and x[0] < zu_tok)
    f["antwort_tokens"] = (len(g) - zu_tok - 1) if zu_tok is not None else 0
    letzte = A[-1] if A else None
    if zu_tok is not None and letzte is not None:
        f["letzte_richtig"] = letzte[2]
        f["abstand_letzte_zu"] = zu_tok - letzte[0]
        f["zu_am_richtigen"] = bool(letzte[2] is True and 0 <= zu_tok - letzte[0] <= 64)
        f["zu_am_falschen"] = bool(letzte[2] is False and 0 <= zu_tok - letzte[0] <= 64)
    else:
        f["letzte_richtig"], f["abstand_letzte_zu"], f["zu_am_richtigen"], f["zu_am_falschen"] = None, None, False, False
    return f


def main():
    wm = lade_mod("wm", os.path.join(HIER, "42_wahrheitsmelder.py"))
    k2 = lade_mod("k2", os.path.join(HIER, "76_kandidaten_v2.py"))
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(os.path.join(WURZEL, "modelle", "Qwen3.5-0.8B"))
    ZU = tok.convert_tokens_to_ids("</think>")
    memo = {(c, g): bool(v) for c, g, v in json.load(open(os.path.join(ERG, "wertcache.json"), encoding="utf-8"))}
    info = {}
    for z in open(os.path.join(WURZEL, "daten", "math500.jsonl"), encoding="utf-8"):
        d = json.loads(z)
        info[d.get("unique_id", d.get("id"))] = (d.get("level"), d.get("subject"))
    D = {m: {} for m in S3}
    for m, dirs in S3.items():
        for d in dirs:
            for z in open(os.path.join(ERG, d, "ergebnisse.jsonl"), encoding="utf-8"):
                r = json.loads(z)
                f = merkmale(r, tok, ZU, wm, k2, memo)
                f["level"], f["fach"] = info.get(r["id"], (None, r["id"].split("/")[1] if "/" in r["id"] else None))
                f["antwort_art"] = antwort_art(r["gold"])
                D[m][r["id"]] = f
        print(f"{m}: {len(D[m])} Läufe gelesen", flush=True)
    ids = sorted(set(D["WT-A"]) & set(D["MIT"]))
    W, M = D["WT-A"], D["MIT"]
    B = {"n": len(ids), "unbekannte_paare": {m: sum(D[m][i]["unbekannt"] for i in ids) for m in S3}}
    paar = collections.Counter((W[i]["korrekt"], M[i]["korrekt"]) for i in ids)
    B["paare"] = {"beide": paar[(True, True)], "nur_WT-A": paar[(True, False)], "nur_MIT": paar[(False, True)], "keiner": paar[(False, False)]}
    print(f"\nPaare (WT-A, MIT): beide richtig {paar[(True, True)]} | nur WT-A {paar[(True, False)]} | nur MIT {paar[(False, True)]} | "
          f"keiner {paar[(False, False)]} | unbekannte Wert-Paare {B['unbekannte_paare']}")

    # 1) Kontext-Kurve: richtiger Wert gefunden bis X Tokens
    print("\n== Kontext-Kurve: Aufgaben mit richtigem Wert im Denken bis X Tokens (von 140)")
    B["kontext_kurve"] = {}
    for m in S3:
        t1 = [D[m][i]["t1"] for i in ids]
        zeile = {X: sum(1 for t in t1 if t is not None and t < X) for X in (2000, 4000, 8000, 16000, 24000, 32768)}
        B["kontext_kurve"][m] = zeile
        print(f"   {m:5s}: " + " | ".join(f"≤{X // 1000}k {n}" for X, n in zeile.items()))
    for m in S3:  # Anteil richtig abgegeben je Fund-Zeitpunkt
        stufen = ((0, 4000), (4000, 8000), (8000, 16000), (16000, 32768))
        teile = []
        for lo, hi in stufen:
            X = [D[m][i] for i in ids if D[m][i]["t1"] is not None and lo <= D[m][i]["t1"] < hi]
            teile.append(f"{lo // 1000}–{hi // 1000}k: {sum(x['korrekt'] for x in X)}/{len(X)}")
        print(f"   {m:5s} richtig abgegeben je Fund-Zeitpunkt: " + " | ".join(teile))

    # 2) Trichter WT-A und MIT
    for m in S3:
        X = [D[m][i] for i in ids]
        mit_wert = [x for x in X if x["t1"] is not None]
        g1 = [x for x in mit_wert if x["zu_am_richtigen"]]
        g2 = [x for x in mit_wert if not x["zu_am_richtigen"]]
        t = collections.OrderedDict([("richtiger Wert im Denken", len(mit_wert)), ("am richtigen Wert geschlossen (G1)", len(g1)),
                                     ("davon richtig abgegeben", sum(x["korrekt"] for x in g1)),
                                     ("Wert da, dort nicht geschlossen (G2)", len(g2)), ("davon trotzdem richtig", sum(x["korrekt"] for x in g2)),
                                     ("ohne richtigen Wert", len(X) - len(mit_wert)),
                                     ("davon trotzdem richtig", sum(x["korrekt"] for x in X if x["t1"] is None))])
        B[f"trichter_{m}"] = dict(t)
        print(f"\n== Trichter {m}: " + " | ".join(f"{k} {v}" for k, v in t.items()))
        print(f"   G2 – was stattdessen: " + "; ".join(f"{a} {n}" for a, n in collections.Counter(x["art"] for x in g2).most_common()))
        g2_zu = [x for x in g2 if x["zu_tok"] is not None]
        print(f"   G2 mit Abschluss ({len(g2_zu)}): danach am falschen Wert geschlossen {sum(x['zu_am_falschen'] for x in g2_zu)}, "
              f"sonst wo geschlossen {sum(not x['zu_am_falschen'] for x in g2_zu)}; Abschluss vor t1? "
              f"{sum(1 for x in g2_zu if x['zu_tok'] < x['t1'])}")
        verl = [x for x in g1 if not x["korrekt"]]
        print(f"   Abgabe-Verluste (G1, nicht richtig abgegeben) {len(verl)}: " + "; ".join(
            f"{a} {n}" for a, n in collections.Counter(x["art"] + (" +2.</think>" if x["zweites_zu"] else "") for x in verl).most_common()))
        B[f"abgabe_verluste_{m}"] = collections.Counter(x["art"] for x in verl)

    # 3) Ausschlussverfahren: G1 gegen G2 bei WT-A
    X = [W[i] for i in ids if W[i]["t1"] is not None]
    g1 = [x for x in X if x["zu_am_richtigen"]]
    g2 = [x for x in X if not x["zu_am_richtigen"]]
    print(f"\n== Ausschluss WT-A: G1 (am richtigen Wert geschlossen) {len(g1)} gegen G2 (Wert da, dort nicht geschlossen) {len(g2)}")
    B["ausschluss"] = {}
    for name, fn in (("t1 (Median Tokens)", lambda x: x["t1"]), ("Erwähnungen richtig (Median)", lambda x: x["erwaehnungen_richtig"]),
                     ("Konkurrenz-Werte vor t1 (Median)", lambda x: x["konkurrenz_vor_t1"]),
                     ("Zweifel-Wörter nach t1 (Median)", lambda x: x["zweifel_nach_t1"]),
                     ("Stufe (Median)", lambda x: x["level"] if isinstance(x["level"], (int, float)) else np.nan)):
        a1 = np.array([fn(x) for x in g1], dtype=float)
        a2 = np.array([fn(x) for x in g2], dtype=float)
        B["ausschluss"][name] = [float(np.nanmedian(a1)), float(np.nanmedian(a2))]
        print(f"   {name:34s}: G1 {np.nanmedian(a1):8.1f} | G2 {np.nanmedian(a2):8.1f}")
    for name, fn in (("Schluss-Rahmung vor t1", lambda x: x["schluss_vor_t1"]),):
        print(f"   {name:34s}: G1 {100 * np.mean([fn(x) for x in g1]):.0f} % | G2 {100 * np.mean([fn(x) for x in g2]):.0f} %")
    for feld in ("level", "fach", "antwort_art"):
        c1 = collections.Counter(x[feld] for x in g1)
        c2 = collections.Counter(x[feld] for x in g2)
        keys = sorted(set(c1) | set(c2), key=lambda k: str(k))
        print(f"   {feld}: " + " | ".join(f"{k}: G1 {c1[k]} / G2 {c2[k]} ({100 * c1[k] / max(1, c1[k] + c2[k]):.0f} % G1)" for k in keys))
        B["ausschluss"][feld] = {str(k): [c1[k], c2[k]] for k in keys}
    print("   t1-Stufen: " + " | ".join(
        f"{lo // 1000}–{hi // 1000}k: G1 {sum(1 for x in g1 if lo <= x['t1'] < hi)} / G2 {sum(1 for x in g2 if lo <= x['t1'] < hi)}"
        for lo, hi in ((0, 2000), (2000, 4000), (4000, 8000), (8000, 16000), (16000, 32768))))

    # 4) Horizont: die 26 „nur MIT richtig“
    nur_mit = [i for i in ids if M[i]["korrekt"] and not W[i]["korrekt"]]
    print(f"\n== Horizont bei den {len(nur_mit)} Aufgaben „nur MIT richtig“:")
    h = collections.Counter()
    for i in nur_mit:
        w, mm = W[i], M[i]
        if w["t1"] is None and w["zu_tok"] is not None and mm["t1"] is not None and w["zu_tok"] < mm["t1"]:
            h["WT-A schloss, bevor MIT den Wert fand (Wert bei WT-A nie da)"] += 1
        elif w["t1"] is None:
            h["Wert bei WT-A nie da (ohne früheren Abschluss)"] += 1
        elif w["zu_am_richtigen"]:
            h["WT-A schloss am richtigen Wert, Abgabe misslang"] += 1
        elif w["zu_tok"] is None:
            h["Wert da, WT-A schloss nie"] += 1
        else:
            h["Wert da, WT-A schloss woanders"] += 1
        print(f"   {i:32s} WT-A {w['art']:38s} t1 {str(w['t1']):>6s} zu {str(w['zu_tok']):>6s} | MIT t1 {str(mm['t1']):>6s} "
              f"zu {str(mm['zu_tok']):>6s} | Stufe {w['level']} {w['antwort_art']}")
    for k, v in h.most_common():
        print(f"   → {v:2d} × {k}")
    B["horizont_nur_mit"] = dict(h)
    # 5) „Nachsicht“ (NACHTRÄGLICH, erkundend): Abschluss am richtigen Wert (G1) – hilft es, wenn der Wert vorher schon öfter da war?
    print("\n== Nachsicht: Abschluss am richtigen Wert (G1), nach Zahl der richtigen Erwähnungen VOR dem Abschluss")
    B["nachsicht"] = {}
    for m in S3:
        X = [D[m][i] for i in ids if D[m][i]["zu_am_richtigen"]]
        for name, lo, hi in (("1×", 1, 1), ("2×", 2, 2), ("3–5×", 3, 5), ("6×+", 6, 10 ** 6)):
            Y = [x for x in X if lo <= x["richtig_vor_zu"] <= hi]
            if Y:
                e = {"n": len(Y), "richtig": sum(x["korrekt"] for x in Y), "zweites_zu": sum(1 for x in Y if x["zweites_zu"]),
                     "antwort_tokens_median": float(np.median([x["antwort_tokens"] for x in Y]))}
                B["nachsicht"][f"{m} {name}"] = e
                print(f"   {m:5s} {name:5s}: n {e['n']:3d} | richtig abgegeben {e['richtig']:3d} ({100 * e['richtig'] / e['n']:.0f} %) | "
                      f"weiteres </think> im Antwortteil {e['zweites_zu']:3d} ({100 * e['zweites_zu'] / e['n']:.0f} %) | Antwortteil Median "
                      f"{e['antwort_tokens_median']:.0f} Tokens")
    # MIT: Bestätigungs-Strecke (Fund → Abschluss)
    s = [M[i]["zu_tok"] - M[i]["t1"] for i in ids if M[i]["t1"] is not None and M[i]["zu_tok"] is not None and M[i]["zu_tok"] >= M[i]["t1"]]
    s_w = [W[i]["zu_tok"] - W[i]["t1"] for i in ids if W[i]["t1"] is not None and W[i]["zu_tok"] is not None and W[i]["zu_tok"] >= W[i]["t1"]]
    B["bestaetigungs_strecke_median"] = {"MIT": float(np.median(s)) if s else None, "WT-A": float(np.median(s_w)) if s_w else None}
    print(f"\n== Fund → Abschluss (Tokens, Median): MIT {B['bestaetigungs_strecke_median']['MIT']} | WT-A {B['bestaetigungs_strecke_median']['WT-A']}")
    json.dump(B, open(os.path.join(ERG, "ausschluss_wta_s3.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False, default=str)
    json.dump({m: D[m] for m in S3}, open(os.path.join(ERG, "ausschluss_wta_s3_laeufe.json"), "w", encoding="utf-8"), ensure_ascii=False)
    print(f"gespeichert: {os.path.join(ERG, 'ausschluss_wta_s3.json')}")


if __name__ == "__main__":
    main()
