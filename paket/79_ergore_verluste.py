"""Warum löst ERGORE auf 161–300 weniger als MIT? (NACHTRÄGLICH, beschreibend; nach dem vorab festgelegten Urteil 07.11. 22:38)
Für jede Aufgabe und jedes Modell: Denken geschlossen? Antwort (\\boxed) im Antwortteil? Ende (eos/limit/Schleife, und ob die
Schleife vor oder nach `</think>` lag)? Stand der richtige Wert schon im Denken (Erkenner v2 aus 76)?
Ausgewertet werden vor allem die 22 Aufgaben „nur MIT richtig“ und die 7 „nur ERGORE richtig“.
  python 79_ergore_verluste.py
"""
import collections
import importlib.util
import json
import os

import numpy as np

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(HIER)
ERG = os.path.join(WURZEL, "ergebnisse")
S3 = {"ERGORE": ["s3-ergore-161-260", "s3-ergore-261-300"], "MIT": ["s3-mit-161-260", "s3-mit-261-300"]}
if "--wta" in __import__("sys").argv:  # gleiche Auswertung für WT-A gegen MIT
    S3 = {"ERGORE": ["s3-wta-161-210", "s3-wta-211-260", "s3-wta-261-300"], "MIT": ["s3-mit-161-260", "s3-mit-261-300"]}


def lade_mod(name, pfad):
    s = importlib.util.spec_from_file_location(name, pfad)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


def main():
    k2 = lade_mod("k2", os.path.join(HIER, "76_kandidaten_v2.py"))
    wm = lade_mod("wm", os.path.join(HIER, "42_wahrheitsmelder.py"))
    ev = wm.lade("ev", os.path.join(WURZEL, "eval", "03_eval.py"))
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(os.path.join(WURZEL, "modelle", "Qwen3.5-0.8B"))
    ZU = tok.convert_tokens_to_ids("</think>")
    memo = {}
    cpfad = os.path.join(ERG, "wertcache.json")
    if os.path.exists(cpfad):  # paralleler Vorab-Abgleich (80_wertcache.py); fehlende Paare werden wie bisher gerechnet
        memo = {(c, g): bool(v) for c, g, v in json.load(open(cpfad, encoding="utf-8"))}

    def ok(c, g):
        k = (c, g)
        if k not in memo:
            memo[k] = bool(ev.korrekt(c, g)) or bool(ev.korrekt(wm.bereinige_kandidat(c), g))
        return memo[k]

    def merkmale(r):
        g = r["gen_ids"]
        text = "".join(tok.decode([t]) for t in g)  # wie 76/80: Token-weise
        zc = text.find("</think>")
        denk = text if zc < 0 else text[:zc]
        antw = "" if zc < 0 else text[zc + len("</think>"):]
        werte = [c for (_, _, c) in wm.kandidaten_mit_ende(denk)] + [w for (_, _, w) in k2.wert_aussagen(denk)]
        richtig_im_denken = any(ok(c, r["gold"]) for c in werte)
        f = {"korrekt": bool(r["korrekt"]), "zu": zc >= 0, "boxed_antwort": "\\boxed" in antw, "ende": r["ende"],
             "tokens": r["tokens"], "denk_tokens": g.index(ZU) if ZU in g else len(g), "richtig_im_denken": richtig_im_denken,
             "antwort_tokens": (len(g) - g.index(ZU) - 1) if ZU in g else 0}
        if not f["zu"]:
            f["art"] = "nie geschlossen (" + r["ende"] + ")"
        elif not f["boxed_antwort"]:
            f["art"] = "geschlossen, keine Antwort (" + r["ende"] + ")"
        elif not f["korrekt"]:
            f["art"] = "geschlossen, falsche Antwort"
        else:
            f["art"] = "richtig"
        return f

    D = {m: {} for m in S3}
    for m, dirs in S3.items():
        for d in dirs:
            for z in open(os.path.join(ERG, d, "ergebnisse.jsonl"), encoding="utf-8"):
                r = json.loads(z)
                D[m][r["id"]] = merkmale(r)
    ids = sorted(set(D["ERGORE"]) & set(D["MIT"]))
    nur_mit = [i for i in ids if D["MIT"][i]["korrekt"] and not D["ERGORE"][i]["korrekt"]]
    nur_erg = [i for i in ids if D["ERGORE"][i]["korrekt"] and not D["MIT"][i]["korrekt"]]
    print(f"Aufgaben {len(ids)} | nur MIT richtig {len(nur_mit)} | nur ERGORE richtig {len(nur_erg)}")
    for name, gruppe, verlierer, gewinner in (("nur MIT richtig", nur_mit, "ERGORE", "MIT"), ("nur ERGORE richtig", nur_erg, "MIT", "ERGORE")):
        arten = collections.Counter(D[verlierer][i]["art"] for i in gruppe)
        wusste = sum(D[verlierer][i]["richtig_im_denken"] for i in gruppe)
        dk_v = [D[verlierer][i]["denk_tokens"] for i in gruppe if D[verlierer][i]["zu"]]
        dk_g = [D[gewinner][i]["denk_tokens"] for i in gruppe if D[gewinner][i]["zu"]]
        print(f"\n== {name} ({len(gruppe)} Aufgaben) – was {verlierer} dort tat:")
        for a, n in arten.most_common():
            print(f"   {n:2d} × {a}")
        print(f"   richtiger Wert stand bei {verlierer} schon im Denken: {wusste}/{len(gruppe)}")
        if dk_v and dk_g:
            print(f"   Denk-Länge bis </think> (Median): {verlierer} {int(np.median(dk_v))}, {gewinner} {int(np.median(dk_g))}")
    print("\n== Alle 140 Aufgaben je Modell:")
    for m in S3:
        arten = collections.Counter(D[m][i]["art"] for i in ids)
        print(f"   {m:6s}: " + "; ".join(f"{a} {n}" for a, n in arten.most_common()))
        falsch_aber_gewusst = sum(1 for i in ids if not D[m][i]["korrekt"] and D[m][i]["richtig_im_denken"])
        print(f"           falsch, obwohl der richtige Wert im Denken stand: {falsch_aber_gewusst}")


if __name__ == "__main__":
    main()
