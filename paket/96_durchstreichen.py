"""Durchstreichen, schnelle Antworten, Schilder (08.11.; Antworten des Nutzers auf die Fragen-Anker, 11:15; NACHTRÄGLICH,
beschreibend, nur Text und vorhandene Messungen).
(A) Durchstreichen – Nutzer: „Warum wird durchgestrichen, WENN das Durchgestrichene wahr ist?“
    Eine Wert-Aussage gilt als durchgestrichen, wenn innerhalb von 60 Tokens danach ein Rücknahme-Wort folgt (wait, no, actually,
    mistake, incorrect, wrong, let me re…, hmm). Gezählt wird:
    - wie oft richtige und wie oft falsche Werte durchgestrichen werden;
    - in Denktexten (WT-A, MIT) mit dem Wahrheits-Tor zT_max aus der Zuck-Messung: durchgestrichene gegen behaltene richtige Werte.
(B) Schnell sicher gegen schnell geraten – Nutzer: „Gibt’s dort bereits durchgestrichene Dinge?“
    INT-Antworten unter 1.000 Tokens, richtig gegen falsch:
    - Durchstreichungen, Zweifel-Wörter, Zahl verschiedener Werte;
    - L13-Sondenwert am Ende (int_sonde).
(C) Schilder – Nutzer: „Die Schilder hängt der auf, der im Haus wohnt.“ Häufigste Wörter in den 12 Tokens vor dem ersten
    </think>, MITs natürliche Abschlüsse gegen WT-As Reflex-Abschlüsse.
  python 96_durchstreichen.py
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
RUECK = re.compile(r"\b(wait|no,|actually|mistake|incorrect|wrong|let me re|hmm|not correct|that's not)\b", re.I)
ZWEIFEL = re.compile(r"\b(maybe|perhaps|i think|not sure|guess|probably|might)\b", re.I)


def lade_mod(name, pfad):
    s = importlib.util.spec_from_file_location(name, pfad)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


def laufe(dirs):
    R = {}
    for d in dirs:
        for z in open(os.path.join(ERG, d, "ergebnisse.jsonl"), encoding="utf-8"):
            r = json.loads(z)
            R[r["id"]] = r
    return R


def main():
    wm = lade_mod("wm", os.path.join(HIER, "42_wahrheitsmelder.py"))
    k2 = lade_mod("k2", os.path.join(HIER, "76_kandidaten_v2.py"))
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(os.path.join(WURZEL, "modelle", "Qwen3.5-0.8B"))
    memo = {(c, g): bool(v) for c, g, v in json.load(open(os.path.join(ERG, "wertcache.json"), encoding="utf-8"))}

    def aussagen(r, nur_denken):
        st = [tok.decode([t]) for t in r["gen_ids"]]
        gr = np.cumsum([len(s) for s in st]) if st else np.array([0])
        text = "".join(st)
        zc = text.find("</think>")
        teil = text if (zc < 0 or not nur_denken) else text[:zc]
        A = []
        for (_, e, c) in list(wm.kandidaten_mit_ende(teil)) + list(k2.wert_aussagen(teil)):
            t = min(int(np.searchsorted(gr, e - 1, side="right")), len(st) - 1)
            nach = text[e:int(gr[min(t + 60, len(gr) - 1)])]
            A.append({"t": t, "c": c, "ok": memo.get((c, r["gold"])), "weg": bool(RUECK.search(nach))})
        return A, text
    print("== (A) Durchstreichen: Anteil durchgestrichener Wert-Aussagen")
    for name, dirs, nur_denken in (("WT-A Denken", ["s3-wta-161-210", "s3-wta-211-260", "s3-wta-261-300"], True),
                                   ("MIT Denken", ["s3-mit-161-260", "s3-mit-261-300"], True),
                                   ("INT (Vorderzimmer)", ["s3-int-eigen-161-210", "s3-int-eigen-211-260", "s3-int-eigen-261-300"], False)):
        R = laufe(dirs)
        k = collections.Counter()
        zt = {"weg": [], "bleibt": []}
        Z = {}
        datei = {"WT-A Denken": "zucken_WT-A_ergo-zigA.jsonl", "MIT Denken": "zucken_MIT_mit-wt.jsonl"}.get(name)
        if datei:
            for z in open(os.path.join(ERG, datei), encoding="utf-8"):
                zz = json.loads(z)
                Z[zz["id"]] = {(s["t"], s["wert"]): s["zT_max"] for s in zz["aussagen"]}
        for i, r in R.items():
            A, _ = aussagen(r, nur_denken)
            for s in A:
                if s["ok"] is None:
                    continue
                k[(s["ok"], s["weg"])] += 1
                if s["ok"] and i in Z:
                    v = Z[i].get((s["t"], s["c"][:40]))
                    if v is not None:
                        zt["weg" if s["weg"] else "bleibt"].append(v)
        rw = k[(True, True)] / max(1, k[(True, True)] + k[(True, False)])
        fw = k[(False, True)] / max(1, k[(False, True)] + k[(False, False)])
        zeile = (f"   {name:20s}: richtige Werte durchgestrichen {k[(True, True)]} von {k[(True, True)] + k[(True, False)]} ({100 * rw:.0f} %) | "
                 f"falsche {k[(False, True)]} von {k[(False, True)] + k[(False, False)]} ({100 * fw:.0f} %)")
        if zt["weg"] and zt["bleibt"]:
            zeile += (f" | Wahrheits-Tor an richtigen Werten: durchgestrichen Median {np.median(zt['weg']):+.2f}, behalten "
                      f"{np.median(zt['bleibt']):+.2f}")
        print(zeile)
    print("\n== (B) Schnelle INT-Antworten (< 1.000 Tokens): richtig gegen falsch")
    I = laufe(["s3-int-eigen-161-210", "s3-int-eigen-211-260", "s3-int-eigen-261-300", "setB60-ohne-eigen-t06",
               "m500-001-080-ohne-eigen-t06", "m500-081-160-ohne-eigen-t06"])
    sonde = {}
    for z in open(os.path.join(ERG, "int_sonde.jsonl"), encoding="utf-8"):
        e = json.loads(z)
        if e.get("wert") is not None:
            sonde[e["id"]] = e["wert"]
    gr_ = {True: collections.defaultdict(list), False: collections.defaultdict(list)}
    for i, r in I.items():
        if r["tokens"] >= 1000:
            continue
        A, text = aussagen(r, False)
        g = gr_[bool(r["korrekt"])]
        g["durchgestrichen"].append(sum(s["weg"] for s in A))
        g["zweifel"].append(len(ZWEIFEL.findall(text)))
        g["verschiedene_werte"].append(len({s["c"].strip() for s in A}))
        g["tokens"].append(r["tokens"])
        if i in sonde:
            g["sonde"].append(sonde[i])
    for merkmal in ("durchgestrichen", "zweifel", "verschiedene_werte", "tokens", "sonde"):
        a, b = gr_[True][merkmal], gr_[False][merkmal]
        auc = None
        if a and b:  # paarweise, Gleichstand zählt halb (viele Nullen bei Zählmerkmalen)
            A_ = np.array(a, dtype=float)[:, None]
            B_ = np.array(b, dtype=float)[None, :]
            auc = float(((A_ > B_).sum() + 0.5 * (A_ == B_).sum()) / (A_.size * B_.size))
        print(f"   {merkmal:18s}: richtig Mittel {np.mean(a):6.2f} (n {len(a)}) | falsch Mittel {np.mean(b):6.2f} (n {len(b)}) | "
              f"AUC (richtig hoch) {auc:.2f}")
    print("\n== (C) Schilder: häufigste Wörter in den 12 Tokens vor dem ersten </think>")
    ZU = tok.convert_tokens_to_ids("</think>")
    for name, dirs, datei, nur in (("MIT, natürlich", ["s3-mit-161-260", "s3-mit-261-300"], None, None),
                                   ("WT-A, Reflex", ["s3-wta-161-210", "s3-wta-211-260", "s3-wta-261-300"], "zucken_WT-A_ergo-zigA.jsonl", "Reflex")):
        R = laufe(dirs)
        reflex = None
        if datei:
            reflex = set()
            for z in open(os.path.join(ERG, datei), encoding="utf-8"):
                zz = json.loads(z)
                xc = [x for x in zz["stellen"] if zz["zu_tok"] is not None and x[0] == zz["zu_tok"] - 1 and x[7] is not None]
                if xc and xc[0][7] < 0.02 and xc[0][5] >= 0.2:
                    reflex.add(zz["id"])
        woerter = collections.Counter()
        n = 0
        for i, r in R.items():
            if ZU not in r["gen_ids"] or (reflex is not None and i not in reflex):
                continue
            k_ = r["gen_ids"].index(ZU)
            vor = tok.decode(r["gen_ids"][max(0, k_ - 12):k_]).lower()
            n += 1
            woerter.update(set(re.findall(r"[a-z]+", vor)))
        print(f"   {name} (n {n}): " + ", ".join(f"{w} {100 * c / n:.0f} %" for w, c in woerter.most_common(10)))


if __name__ == "__main__":
    main()
