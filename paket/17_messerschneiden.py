"""Messerschneiden-Finder: Stellen, an denen derselbe Text mal in eine Schleife kippt und mal produktiv weiterläuft.

Grundlage für (a) das MIT-Rezept (Richtung aus GEPAARTEN produktiv/repetitiv-Kontexten an derselben Verzweigung) und
(b) spätere Ursachen-Tests (Activation Patching zwischen den beiden Ästen).

Ablauf:
  1. Schleifenbeginn je Diagnose-Transkript wie 04s (erster Lauf wiederholter 8-Gramme >= --min-lauf).
  2. Verzweigungspunkte: Schleifenbeginn + jeder Versatz aus --punkte (negativ = vor dem Beginn der Wiederholung).
  3. Je Punkt --n-fortsetzungen freie Fortsetzungen (--laenge Tokens) mit dem Sampling der echten Messung (llama-server).
  4. Einordnung je Fortsetzung: Anteil Tokens in Wiederholungs-Läufen (Präfix zählt als Vorgeschichte)
       >= --schleife-ab -> "schleife",  <= --produktiv-bis -> "produktiv",  dazwischen -> verworfen
  5. Messerschneide = mindestens --min-je-klasse Fortsetzungen in BEIDEN Klassen.
Ausgabe:
  --aus     jsonl für 04s --kontrast: je Messerschneide gleich viele Schleifen- und Produktiv-Äste (höchstens --je-ast),
            markiert werden die ersten --markier Tokens des Asts (klasse_a = Schleife, klasse_b = produktiv)
  --bericht json mit allen Punkten, Einordnungen und Seeds (für spätere Ursachen-Tests)

  python 17_messerschneiden.py --ergebnisse ergebnisse/diagnose-vL/ergebnisse.jsonl --tokenizer modelle/Qwen3.5-0.8B \
      --gguf gguf/Qwen3.5-0.8B-q8_0.gguf --aus ergebnisse/messer.jsonl --bericht ergebnisse/messer_bericht.json
"""
import argparse
import importlib.util
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor

import numpy as np

HIER = os.path.dirname(os.path.abspath(__file__))


def lade_modul(name, pfad):
    spec = importlib.util.spec_from_file_location(name, pfad)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ergebnisse", required=True)
    ap.add_argument("--tokenizer", required=True)
    ap.add_argument("--gguf", required=True)
    ap.add_argument("--llama-server", default=os.path.join(HIER, "..", "llama", "bin", "llama-server.exe"))
    ap.add_argument("--eval-modul", default=os.path.join(HIER, "..", "eval", "03_eval.py"))
    ap.add_argument("--port", type=int, default=8095)
    ap.add_argument("--slots", type=int, default=4)
    ap.add_argument("--max-len", type=int, default=8192)
    ap.add_argument("--min-lauf", type=int, default=32)
    ap.add_argument("--punkte", default="-64,-16,0", help="Versätze zum Schleifenbeginn")
    ap.add_argument("--n-fortsetzungen", type=int, default=8)
    ap.add_argument("--laenge", type=int, default=384)
    ap.add_argument("--schleife-ab", type=float, default=0.5)
    ap.add_argument("--produktiv-bis", type=float, default=0.1)
    ap.add_argument("--min-je-klasse", type=int, default=2)
    ap.add_argument("--je-ast", type=int, default=2, help="höchstens so viele Äste je Klasse und Messerschneide in --aus")
    ap.add_argument("--markier", type=int, default=64)
    ap.add_argument("--max-texte", type=int, default=0)
    ap.add_argument("--aus", required=True)
    ap.add_argument("--bericht", required=True)
    a = ap.parse_args()

    ev = lade_modul("eval03", a.eval_modul)
    ev.EXTRA.update(ev.VLLM_STIL)
    p2 = lade_modul("pruefstand2", os.path.join(HIER, "15_pruefstand_frei.py"))
    texte = [json.loads(z) for z in open(a.ergebnisse, encoding="utf-8") if z.strip()]
    if a.max_texte:
        texte = texte[:a.max_texte]
    versaetze = [int(x) for x in a.punkte.split(",")]

    punkte = []
    for i, r in enumerate(texte):
        gen = r["gen_ids"][:a.max_len]
        _, _, onset = p2.laeufe(gen, a.min_lauf)
        if onset >= len(gen):
            continue
        for v in versaetze:
            cut = onset + v
            if 8 <= cut <= len(gen):
                punkte.append({"id": r["id"], "i": i, "onset": onset, "versatz": v, "cut": cut,
                               "prompt_ids": r["prompt_ids"], "praefix_gen": gen[:cut]})
    jobs = list(range(len(punkte)))  # je Punkt EIN Faden, Seeds nacheinander -> gleicher Slot, Präfix nur einmal einlesen
    ctx = max(len(p["prompt_ids"]) + p["cut"] for p in punkte) + a.laenge + 64
    print(f"{len(punkte)} Verzweigungspunkte aus {len({p['id'] for p in punkte})} Transkripten, "
          f"{len(jobs) * a.n_fortsetzungen} Fortsetzungen à {a.laenge} Tokens, Kontext je Slot {ctx}", flush=True)

    fertig = [0]

    def lauf(k):
        p = punkte[k]
        aeste = []
        for s in range(a.n_fortsetzungen):
            g = ev.generiere(f"http://127.0.0.1:{a.port}", p["prompt_ids"] + p["praefix_gen"], a.laenge, 2000 + s,
                             False, 0.9, 10 ** 9, 3600)
            cont = g["gen_ids"]
            _, lauf_, _ = p2.laeufe(p["praefix_gen"] + cont, a.min_lauf)
            anteil = float(lauf_[p["cut"]:].mean()) if cont else 1.0
            klasse = "schleife" if anteil >= a.schleife_ab else ("produktiv" if anteil <= a.produktiv_bis else "unklar")
            aeste.append({"seed": 2000 + s, "anteil": round(anteil, 3), "klasse": klasse, "n": len(cont), "ids": cont})
        fertig[0] += 1
        if fertig[0] % 10 == 0:
            print(f"  {fertig[0]}/{len(punkte)} Punkte fertig ({time.time() - t0:.0f} s)", flush=True)
        return k, aeste

    t0 = time.time()
    proc = p2.server_start(a.llama_server, os.path.abspath(a.gguf), a.port, a.slots, ctx)
    try:
        with ThreadPoolExecutor(a.slots) as ex:
            erg = list(ex.map(lauf, jobs))
    finally:
        p2.server_stopp(proc)
    for k, aeste in erg:
        punkte[k]["aeste"] = aeste

    n_messer, zeilen = 0, []
    for p in punkte:
        sch = [f for f in p["aeste"] if f["klasse"] == "schleife"]
        pro = [f for f in p["aeste"] if f["klasse"] == "produktiv"]
        p["schleife"], p["produktiv"] = len(sch), len(pro)
        p["messerschneide"] = len(sch) >= a.min_je_klasse and len(pro) >= a.min_je_klasse
        if not p["messerschneide"]:
            continue
        n_messer += 1
        m = min(len(sch), len(pro), a.je_ast)
        for klasse, aeste in (("schleife", sch[:m]), ("produktiv", pro[:m])):
            for f in aeste:
                idx = list(range(p["cut"], p["cut"] + min(a.markier, len(f["ids"]))))
                zeilen.append({"id": f"{p['id']}@{p['cut']}#{f['seed']}", "prompt_ids": p["prompt_ids"],
                               "gen_ids": p["praefix_gen"] + f["ids"],
                               "klasse_a": idx if klasse == "schleife" else [],
                               "klasse_b": idx if klasse == "produktiv" else []})
    with open(a.aus, "w", encoding="utf-8") as fh:
        for z in zeilen:
            fh.write(json.dumps(z) + "\n")

    nach_v = {}
    for p in punkte:
        d = nach_v.setdefault(p["versatz"], {"punkte": 0, "messerschneiden": 0, "schleife": 0, "produktiv": 0})
        d["punkte"] += 1; d["messerschneiden"] += p["messerschneide"]
        d["schleife"] += p["schleife"]; d["produktiv"] += p["produktiv"]
    bericht = {"protokoll": {k: getattr(a, k) for k in ("gguf", "punkte", "n_fortsetzungen", "laenge", "schleife_ab",
                                                         "produktiv_bis", "min_je_klasse", "je_ast", "markier")},
               "nach_versatz": nach_v, "messerschneiden": n_messer, "zeilen_fuer_04s": len(zeilen),
               "sekunden": round(time.time() - t0),
               "punkte": [{k: v for k, v in p.items() if k not in ("prompt_ids", "praefix_gen")} for p in punkte]}
    json.dump(bericht, open(a.bericht, "w", encoding="utf-8"), ensure_ascii=False)
    for v, d in sorted(nach_v.items()):
        print(f"Versatz {v:+4d}: {d['messerschneiden']:3d} Messerschneiden von {d['punkte']} Punkten "
              f"(Äste: {d['schleife']} Schleife / {d['produktiv']} produktiv)")
    print(f"MESSERSCHNEIDEN: {n_messer}, Zeilen für 04s --kontrast: {len(zeilen)}, {bericht['sekunden']} s", flush=True)


if __name__ == "__main__":
    main()
