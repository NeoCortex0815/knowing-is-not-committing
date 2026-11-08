"""Format statt Denken? (08.11. nachts, NACHTRÄGLICH, beschreibend; Frage des Nutzers „Was übersehen wir?“)
Bei Läufen, die das Denken schließen, aber KEIN \\boxed im Antwortteil abgeben: Steht der richtige Wert trotzdem im Antwortteil
(Wert-Aussage nach dem Erkenner v2 oder „answer is …“)? Dann wäre der Verlust teils ein Formatfehler.
Prüfung über denselben Zwischenspeicher wie 76/80 (math-verify mit hartem Zeitlimit je Paar über 80_wertcache).
  python 81_format_check.py
"""
import collections
import importlib.util
import json
import os
import subprocess
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(HIER)
ERG = os.path.join(WURZEL, "ergebnisse")
S3 = {"ERGORE": ["s3-ergore-161-260", "s3-ergore-261-300"], "MIT": ["s3-mit-161-260", "s3-mit-261-300"],
      "WT-A": ["s3-wta-161-210", "s3-wta-211-260", "s3-wta-261-300"]}


def lade_mod(name, pfad):
    s = importlib.util.spec_from_file_location(name, pfad)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


def main():
    wm = lade_mod("wm", os.path.join(HIER, "42_wahrheitsmelder.py"))
    k2 = lade_mod("k2", os.path.join(HIER, "76_kandidaten_v2.py"))
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(os.path.join(WURZEL, "modelle", "Qwen3.5-0.8B"))
    faelle = {m: [] for m in S3}
    paare = set()
    for m, dirs in S3.items():
        for d in dirs:
            for z in open(os.path.join(ERG, d, "ergebnisse.jsonl"), encoding="utf-8"):
                r = json.loads(z)
                text = "".join(tok.decode([t]) for t in r["gen_ids"])
                zc = text.find("</think>")
                if zc < 0:
                    continue
                antw = text[zc + len("</think>"):]
                if "\\boxed" in antw:
                    continue
                aus_ = sorted([(e, c) for (_, e, c) in wm.kandidaten_mit_ende(antw)] + [(e, w) for (_, e, w) in k2.wert_aussagen(antw)])
                werte = [c for (_, c) in aus_]
                # Detail (08.11. ~01:32): Zeichen-Position im Antwortteil (Anteil) je Wert und Zahl weiterer </think>
                faelle[m].append((r["id"], r["gold"], werte, r["ende"], [(round(e / max(1, len(antw)), 3), c) for (e, c) in aus_],
                                  antw.count("</think>")))
                for w in werte:
                    paare.add((w, r["gold"]))
    # fehlende Paare über den Zwischenspeicher (80) mit Zeitlimit prüfen lassen
    cache = os.path.join(ERG, "wertcache.json")
    bekannt = {(c, g): v for c, g, v in json.load(open(cache, encoding="utf-8"))} if os.path.exists(cache) else {}
    offen = [p for p in paare if p not in bekannt]
    # 08.11. ~01:35: der erste Lauf (Einzelprozess je Paar) brach am Zeitlimit ab. Jetzt füllt 80_wertcache.py --antwortteil den
    # Zwischenspeicher parallel; hier wird nichts mehr nachgerechnet, fehlende Paare zählen als „unbekannt“.
    print(f"Paare {len(paare)}, im Zwischenspeicher {len(paare) - len(offen)}, unbekannt {len(offen)}", flush=True)
    if offen and "--nachrechnen" in sys.argv:
        tmp = os.path.join(ERG, "_format_check_paare.jsonl")
        with open(tmp, "w", encoding="utf-8") as f:
            for c, g in offen:
                f.write(json.dumps({"id": "x", "gold": g, "gen_ids": [], "text": "", "_wert": c}, ensure_ascii=False) + "\n")
        print(f"{len(offen)} neue Paare – prüfe direkt mit Zeitlimit", flush=True)
        ev = wm.lade("ev", os.path.join(WURZEL, "eval", "03_eval.py"))
        import multiprocessing as mp  # noqa: F401  (Zeitlimit-Variante: einfache Prüfung je Paar in Unterprozess)
        for c, g in offen:
            try:
                out = subprocess.run([sys.executable, "-c",
                                      "import importlib.util,sys,json;s=importlib.util.spec_from_file_location('ev',sys.argv[1]);"
                                      "e=importlib.util.module_from_spec(s);s.loader.exec_module(e);print(bool(e.korrekt(sys.argv[2],sys.argv[3])))",
                                      os.path.join(WURZEL, "eval", "03_eval.py"), c, g], capture_output=True, text=True, timeout=20)
                bekannt[(c, g)] = out.stdout.strip().endswith("True")
            except subprocess.TimeoutExpired:
                bekannt[(c, g)] = False
        os.remove(tmp)
        del ev
    for m in S3:
        F = faelle[m]
        mit_wert = [f for f in F if any(bekannt.get((w, f[1]), False) for w in f[2])]
        enden = collections.Counter(f[3] for f in F)
        print(f"{m:6s}: zu ohne \\boxed {len(F):3d} ({dict(enden)}) | davon richtiger Wert im Antworttext (ohne boxed): {len(mit_wert)}")
        for (i, g, werte, ende, lage, n_zu) in mit_wert:
            erst = min(p for (p, c) in lage if bekannt.get((c, g), False))
            letzte = lage[-1]
            print(f"     {i:36s} Ende {ende:12s} | erster richtiger Wert bei {100 * erst:3.0f} % des Antwortteils | letzte Wert-Aussage "
                  f"{'richtig' if bekannt.get((letzte[1], g), False) else 'falsch'} | weitere </think>: {n_zu}")


if __name__ == "__main__":
    main()
