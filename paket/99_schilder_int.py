"""Schilder und Vorderzimmer, offline (08.11.; N17 in ANNAHMEN; NACHTRÄGLICH, erkundend, nur Text und vorhandene Messungen).
(S1) Abschluss mit Schild = inneres „fertig“? Antwortteil danach: zweites </think>, Länge, \\boxed, richtig.
(S2) Schilder mitten im Denken: „the (final) answer is“ → binnen 200 Tokens geschlossen?
(S3) Schild plus Wahrheit: Wahrheits-Tor am Wert direkt hinter dem Schild (WT-A- und MIT-Texte, 82).
(I1) Karte Vorder- gegen Hinterzimmer nach Fach / Stufe / Antwort-Art (1–300).
(I2) Festlegungs-Risiko: Lange falsche INT-Läufe – bleibt der erste genannte Wert?
  python 99_schilder_int.py
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
SCHILD_ENDE = re.compile(r"\b(answer|final|therefore|thus|ready|conclude|conclusion)\b|\bI(?: will|'ll) (?:write|provide|present|now)\b|^so\b|\bso,? the\b",
                         re.I | re.M)
SCHILD_MITTE = re.compile(r"(?:the final answer is|the answer is|so the answer|therefore,? the answer)\s*:?\s*\$?\\?(?:boxed\{)?", re.I)


def lade_mod(name, pfad):
    s = importlib.util.spec_from_file_location(name, pfad)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


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
        info[d["unique_id"]] = d
    GR = {"MIT 161–300": ["s3-mit-161-260", "s3-mit-261-300"], "MIT s1 261–300": ["s3-mit-261-300-s1"],
          "eigen Set B": ["setB30-eigen-t06", "minipc-b2-eigen-t06"], "ERGORE 161–300": ["s3-ergore-161-260", "s3-ergore-261-300"],
          "WT-A 161–300": ["s3-wta-161-210", "s3-wta-211-260", "s3-wta-261-300"]}
    print("== (S1) Abschluss mit Schild = inneres „fertig“? (Antwortteil nach dem ersten </think>)")
    for name, dirs in GR.items():
        R = laufe(dirs)
        T = {True: [], False: []}
        for r in R.values():
            g = r["gen_ids"]
            if ZU not in g:
                continue
            k = g.index(ZU)
            schild = bool(SCHILD_ENDE.search(tok.decode(g[max(0, k - 30):k])))
            antw = tok.decode(g[k + 1:])
            T[schild].append({"zweites": "</think>" in antw, "laenge": len(g) - k - 1, "boxed": "\\boxed" in antw,
                              "korrekt": bool(r["korrekt"])})
        z = []
        for s in (True, False):
            X = T[s]
            if X:
                z.append(f"{'mit' if s else 'ohne'} Schild n {len(X):3d}: zweites </think> {100 * np.mean([x['zweites'] for x in X]):3.0f} %, "
                         f"Antwortteil Median {np.median([x['laenge'] for x in X]):6.0f}, \\boxed {100 * np.mean([x['boxed'] for x in X]):3.0f} %, "
                         f"richtig {100 * np.mean([x['korrekt'] for x in X]):3.0f} %")
        print(f"   {name:16s}: " + " | ".join(z))
    print("\n== (S2) Schilder mitten im Denken („the (final) answer is …“): binnen 200 Tokens geschlossen?")
    for name, dirs in GR.items():
        R = laufe(dirs)
        n_schild, n_zu = 0, 0
        for r in R.values():
            g = r["gen_ids"]
            k = g.index(ZU) if ZU in g else len(g)
            st = [tok.decode([t]) for t in g[:k]]
            gr = np.cumsum([len(s) for s in st]) if st else np.array([0])
            denk = "".join(st)
            for m in SCHILD_MITTE.finditer(denk):
                t = int(np.searchsorted(gr, m.end() - 1, side="right"))
                n_schild += 1
                n_zu += (k < len(g)) and (k - t <= 200)
        print(f"   {name:16s}: Schilder im Denken {n_schild:5d} | danach binnen 200 Tokens geschlossen {n_zu:4d} "
              f"({100 * n_zu / max(1, n_schild):.0f} %) | Schilder je Lauf {n_schild / max(1, len(R)):.1f}")
    print("\n== (S3) Schild plus Wahrheit (Wert direkt hinter dem Schild; Wahrheits-Tor aus 82)")
    for name, datei, dirs in (("WT-A", "zucken_WT-A_ergo-zigA.jsonl", GR["WT-A 161–300"]), ("MIT", "zucken_MIT_mit-wt.jsonl", GR["MIT 161–300"])):
        R = laufe(dirs)
        hinter, sonst = [], []
        for z in open(os.path.join(ERG, datei), encoding="utf-8"):
            zz = json.loads(z)
            r = R[zz["id"]]
            g = r["gen_ids"][:zz["n_mess"]]
            st = [tok.decode([t]) for t in g]
            gr = np.cumsum([len(s) for s in st]) if st else np.array([0])
            denk = "".join(st)
            schild_t = [int(np.searchsorted(gr, m.end() - 1, side="right")) for m in SCHILD_MITTE.finditer(denk)]
            for s in zz["aussagen"]:
                if s["ok"] is None:
                    continue
                (hinter if any(0 <= s["t"] - t <= 15 for t in schild_t) else sonst).append(s)
        for nm, X in (("hinter Schild", hinter), ("ohne Schild", sonst)):
            if X:
                print(f"   {name:4s} {nm:13s}: n {len(X):5d} | Wert richtig {100 * np.mean([s['ok'] for s in X]):3.0f} % | Tor offen "
                      f"{100 * np.mean([s['zT_max'] > 0 for s in X]):3.0f} % | zT Median {np.median([s['zT_max'] for s in X]):+.2f}")
        for nm, X in (("hinter Schild", hinter), ("ohne Schild", sonst)):
            r_ = [s["zT_max"] for s in X if s["ok"]]
            f_ = [s["zT_max"] for s in X if not s["ok"]]
            if r_ and f_:
                A_ = np.array(r_)[:, None]
                B_ = np.array(f_)[None, :]
                auc = float(((A_ > B_).sum() + 0.5 * (A_ == B_).sum()) / (A_.size * B_.size))
                print(f"   {name:4s} {nm:13s}: Trennschärfe des Wahrheits-Tors richtig/falsch AUC {auc:.2f}")
    print("\n== (I1) Karte Vorder- gegen Hinterzimmer (INT = eigen ohne Denken; Denken = MIT bzw. ERGORE), 1–300")
    INT = laufe(["m500-001-080-ohne-eigen-t06", "m500-081-160-ohne-eigen-t06", "s3-int-eigen-161-210", "s3-int-eigen-211-260", "s3-int-eigen-261-300"])
    for denkname, ddirs in (("MIT", ["mit-vstil-L", "mit-vstil-L-b", "mit-vstil-L-c", "s3-mit-161-260", "s3-mit-261-300"]),
                            ("ERGORE", ["kw75-b", "kw75-c", "tag2-test40-kw75", "s3-ergore-161-260", "s3-ergore-261-300"])):
        D = laufe(ddirs)
        ids = sorted(set(INT) & set(D))
        print(f"   gegen {denkname} ({len(ids)} Aufgaben): INT {sum(INT[i]['korrekt'] for i in ids)} | Denken {sum(D[i]['korrekt'] for i in ids)}")
        for feld in ("subject", "level"):
            teile = []
            for wert in sorted({info[i][feld] for i in ids}, key=str):
                X = [i for i in ids if info[i][feld] == wert]
                nur_i = sum(1 for i in X if INT[i]["korrekt"] and not D[i]["korrekt"])
                nur_d = sum(1 for i in X if D[i]["korrekt"] and not INT[i]["korrekt"])
                teile.append(f"{wert}: {nur_i}:{nur_d}")
            print(f"      {feld} (nur INT : nur Denken): " + " | ".join(teile))
    print("\n== (I2) Festlegungs-Risiko im Vorderzimmer: lange INT-Läufe (> 8.000 Tokens)")
    for richtig in (False, True):
        k = collections.Counter()
        for r in INT.values():
            if r["tokens"] <= 8000 or bool(r["korrekt"]) != richtig:
                continue
            text = tok.decode(r["gen_ids"])
            A = sorted([(e, c) for (_, e, c) in list(wm.kandidaten_mit_ende(text)) + list(k2.wert_aussagen(text))])
            if not A:
                k["keine Werte"] += 1
                continue
            erster = norm(A[0][1])
            werte = [norm(c) for _, c in A]
            k["n"] += 1
            k["erster Wert = Endantwort"] += (erster == norm(r.get("pred")))
            k["verschiedene Werte (Summe)"] += len(set(werte))
            k["erster Wert kommt ≥ 5× vor"] += (werte.count(erster) >= 5)
        n = max(1, k["n"])
        print(f"   {'richtig' if richtig else 'falsch':7s}: n {k['n']} | erster Wert = Endantwort {100 * k['erster Wert = Endantwort'] / n:.0f} % | "
              f"erster Wert ≥ 5× wiederholt {100 * k['erster Wert kommt ≥ 5× vor'] / n:.0f} % | verschiedene Werte Ø {k['verschiedene Werte (Summe)'] / n:.1f}")


if __name__ == "__main__":
    main()
