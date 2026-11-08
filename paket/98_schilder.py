"""Schilder des Hauses (08.11.; Nutzer: „Die Schilder hängt der auf, der im Haus wohnt“; „bleibt das auf den langen Atem
gleichfalls stabil?“; NACHTRÄGLICH, beschreibend, nur Text).
Schild = Schluss-Formulierung in den 30 Tokens vor dem ersten </think>: „answer“, „final“, „therefore/thus/so“, „ready“,
„I will/I'll (write|provide|present)“, „conclude“.
Gezählt wird je Lauf mit natürlichem Abschluss:
  - Schild ja/nein;
  - nach Länge des Atems (Tokens vom ersten richtigen Wert bis </think>: < 2.000 / 2.000–8.000 / > 8.000);
  - nach Seed (MIT Seed 0 gegen Seed 1 auf 261–300);
  - Abgabe-Erfolg mit und ohne Schild;
  - Vergleich mit WT-A (Reflex-Abschlüsse und natürliche Abschlüsse) und eigen (Set B).
  python 98_schilder.py
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
SCHILD = re.compile(r"\b(answer|final|therefore|thus|ready|conclude|conclusion)\b|\bI(?: will|'ll) (?:write|provide|present|now)\b|^so\b|\bso,? the\b",
                    re.I | re.M)


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


def main():
    wm = lade_mod("wm", os.path.join(HIER, "42_wahrheitsmelder.py"))
    k2 = lade_mod("k2", os.path.join(HIER, "76_kandidaten_v2.py"))
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(os.path.join(WURZEL, "modelle", "Qwen3.5-0.8B"))
    ZU = tok.convert_tokens_to_ids("</think>")
    memo = {(c, g): bool(v) for c, g, v in json.load(open(os.path.join(ERG, "wertcache.json"), encoding="utf-8"))}
    reflex = set()
    for z in open(os.path.join(ERG, "zucken_WT-A_ergo-zigA.jsonl"), encoding="utf-8"):
        zz = json.loads(z)
        xc = [x for x in zz["stellen"] if zz["zu_tok"] is not None and x[0] == zz["zu_tok"] - 1 and x[7] is not None]
        if xc and xc[0][7] < 0.02 and xc[0][5] >= 0.2:
            reflex.add(zz["id"])

    def merkmale(r):
        g = r["gen_ids"]
        if ZU not in g:
            return None
        k = g.index(ZU)
        vor = tok.decode(g[max(0, k - 30):k])
        st = [tok.decode([t]) for t in g[:k]]
        gr = np.cumsum([len(s) for s in st]) if st else np.array([0])
        denk = "".join(st)
        t1 = None
        for (_, e, c) in sorted(list(wm.kandidaten_mit_ende(denk)) + list(k2.wert_aussagen(denk)), key=lambda x: x[1]):
            if memo.get((c, r["gold"])):
                t1 = int(np.searchsorted(gr, e - 1, side="right"))
                break
        return {"schild": bool(SCHILD.search(vor)), "atem": (k - t1) if t1 is not None else None, "korrekt": bool(r["korrekt"]),
                "zu": k}
    gruppen = {
        "MIT Seed 0 (161–300)": (["s3-mit-161-260", "s3-mit-261-300"], None),
        "MIT Seed 0 (261–300)": (["s3-mit-261-300"], None),
        "MIT Seed 1 (261–300)": (["s3-mit-261-300-s1"], None),
        "MIT Set B (Seed 0)": (["setB30-mit-t06", "minipc-b2-mit-t06"], None),
        "WT-A, Reflex-Abschlüsse": (["s3-wta-161-210", "s3-wta-211-260", "s3-wta-261-300"], "reflex"),
        "WT-A, natürliche Abschlüsse": (["s3-wta-161-210", "s3-wta-211-260", "s3-wta-261-300"], "natuerlich"),
        "eigen Set B (Seed 0)": (["setB30-eigen-t06", "minipc-b2-eigen-t06"], None),
        "ERGORE 161–300": (["s3-ergore-161-260", "s3-ergore-261-300"], None),
    }
    for name, (dirs, filt) in gruppen.items():
        R = laufe(dirs)
        F = []
        for i, r in R.items():
            if filt == "reflex" and i not in reflex:
                continue
            if filt == "natuerlich" and i in reflex:
                continue
            m = merkmale(r)
            if m:
                F.append(m)
        if not F:
            continue
        mit = [f for f in F if f["schild"]]
        ohne = [f for f in F if not f["schild"]]
        zeile = (f"{name:28s}: Abschlüsse {len(F):3d} | mit Schild {100 * len(mit) / len(F):3.0f} % | richtig mit Schild "
                 f"{sum(f['korrekt'] for f in mit)}/{len(mit)}, ohne {sum(f['korrekt'] for f in ohne)}/{len(ohne)}")
        teile = []
        for lo, hi, nm in ((0, 2000, "kurz"), (2000, 8000, "mittel"), (8000, 10 ** 6, "lang")):
            X = [f for f in F if f["atem"] is not None and lo <= f["atem"] < hi]
            if X:
                teile.append(f"{nm} {100 * np.mean([f['schild'] for f in X]):.0f} % (n {len(X)})")
        print(zeile + " | Schild nach Atem (Fund → Abschluss): " + ", ".join(teile))


if __name__ == "__main__":
    main()
