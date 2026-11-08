"""Paralleler Vorab-Abgleich für den Erkenner v2 (07./08.11.; rein technisch).
Anlass: 76_kandidaten_v2.py prüft jede Wert-Aussage im Denken mit math-verify. Unter Windows läuft das ohne Zeitlimit,
~0,1–0,5 s je Aufruf; bei zehntausenden Paaren dauert das 1–2 h auf einem Kern. Einzelne verschachtelte Ausdrücke
blockieren math-verify sogar dauerhaft (gefunden 08.11. 00:00: ein Prozess hing > 10 min an einem Paar).
Dieses Skript zieht GENAU dieselben (Wert, gold)-Paare wie 76:
  - Token-weise Dekodierung;
  - Denk-Teil vor dem ersten `</think>`;
  - alter Erkenner ∪ Wert-Aussagen.
Es berechnet dieselbe Prüfung pruefe(c, g) = korrekt(c, g) oder korrekt(bereinigt(c), g) parallel.
**Hartes Zeitlimit je Paar (--zeitlimit, Standard 20 s):** Läuft eine Prüfung länger, wird der Prozess beendet, und das Paar
gilt als NICHT richtig. Diese Paare werden gezählt und in ergebnisse/wertcache_zeitlimit.json gelistet.
Ergebnis: ergebnisse/wertcache.json (wird alle 2.000 Paare zwischengespeichert). 76 und 79 lesen den Zwischenspeicher.
  python 80_wertcache.py <Ordner unter ergebnisse/> …
"""
import importlib.util
import json
import multiprocessing as mp
import os
import queue
import sys
import time

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(HIER)
ERG = os.path.join(WURZEL, "ergebnisse")
CACHE = os.path.join(ERG, "wertcache.json")
ZEITLIMIT_LISTE = os.path.join(ERG, "wertcache_zeitlimit.json")


def lade_mod(name, pfad):
    s = importlib.util.spec_from_file_location(name, pfad)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


def arbeiter(wid, inq, outq):
    wm = lade_mod("wm", os.path.join(HIER, "42_wahrheitsmelder.py"))
    ev = wm.lade("ev", os.path.join(WURZEL, "eval", "03_eval.py"))
    outq.put((wid, None, None))                       # bereit
    while True:
        item = inq.get()
        if item is None:
            return
        i, c, g = item
        v = bool(ev.korrekt(c, g)) or bool(ev.korrekt(wm.bereinige_kandidat(c), g))
        outq.put((wid, i, v))


def speichern(erg):
    json.dump([[c, g, v] for (c, g), v in erg.items()], open(CACHE, "w", encoding="utf-8"), ensure_ascii=False)


def main():
    # 08.11. ~01:35, rein technisch: --antwortteil sammelt die Paare aus dem Antwortteil (nach `</think>`) der Läufe OHNE \boxed
    # (für 81_format_check.py); gleiche Prüfung, gleicher Zwischenspeicher.
    antwortteil = "--antwortteil" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    zeitlimit = 20.0
    if "--zeitlimit" in sys.argv:
        zeitlimit = float(sys.argv[sys.argv.index("--zeitlimit") + 1])
        args = [a for a in args if a != str(sys.argv[sys.argv.index("--zeitlimit") + 1])]
    wm = lade_mod("wm", os.path.join(HIER, "42_wahrheitsmelder.py"))
    k2 = lade_mod("k2", os.path.join(HIER, "76_kandidaten_v2.py"))
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(os.path.join(WURZEL, "modelle", "Qwen3.5-0.8B"))
    erg = {}
    if os.path.exists(CACHE):
        erg = {(c, g): bool(v) for c, g, v in json.load(open(CACHE, encoding="utf-8"))}
    zeitl = json.load(open(ZEITLIMIT_LISTE, encoding="utf-8")) if os.path.exists(ZEITLIMIT_LISTE) else []
    paare = set()
    for d in args:
        p = os.path.join(ERG, d, "ergebnisse.jsonl")
        if not os.path.exists(p):
            print(f"FEHLT: {d}", flush=True)
            continue
        for z in open(p, encoding="utf-8"):
            r = json.loads(z)
            st = [tok.decode([t]) for t in r["gen_ids"]]          # wie 76: Token-weise
            text = "".join(st)
            zc = text.find("</think>")
            denk = text if zc < 0 else text[:zc]
            if antwortteil:
                if zc < 0 or "\\boxed" in text[zc + len("</think>"):]:
                    continue
                denk = text[zc + len("</think>"):]
            for (_, _, c) in wm.kandidaten_mit_ende(denk):
                paare.add((c, r["gold"]))
            for (_, _, w) in k2.wert_aussagen(denk):
                paare.add((w, r["gold"]))
    offen = sorted(pp for pp in paare if pp not in erg)
    print(f"{len(paare)} Paare, davon {len(offen)} neu zu prüfen (Zeitlimit {zeitlimit:.0f} s je Paar)", flush=True)
    n_w = int(os.environ.get("WSP_WORKER", 6))
    ctx = mp.get_context("spawn")
    outq = ctx.Queue()
    W = {}

    def starte(wid):
        inq = ctx.Queue()
        p = ctx.Process(target=arbeiter, args=(wid, inq, outq), daemon=True)
        p.start()
        W[wid] = {"p": p, "inq": inq, "item": None, "start": None, "bereit": False}

    for wid in range(n_w):
        starte(wid)
    t0, fertig, naechste = time.time(), 0, 0
    while naechste < len(offen) or any(w["item"] is not None for w in W.values()):
        for wid, w in W.items():
            if w["bereit"] and w["item"] is None and naechste < len(offen):
                c, g = offen[naechste]
                w["item"], w["start"] = (naechste, c, g), time.time()
                w["inq"].put(w["item"])
                naechste += 1
        try:
            wid, i, v = outq.get(timeout=0.5)
            if wid in W and i is None:
                W[wid]["bereit"] = True
            elif wid in W and W[wid]["item"] is not None and W[wid]["item"][0] == i:
                _, c, g = W[wid]["item"]
                erg[(c, g)] = v
                W[wid]["item"] = None
                fertig += 1
                if fertig % 2000 == 0:
                    speichern(erg)
                    print(f"  {fertig}/{len(offen)} ({time.time() - t0:.0f} s, Zeitlimit-Fälle {len(zeitl)})", flush=True)
        except queue.Empty:
            pass
        for wid, w in list(W.items()):
            if w["item"] is not None and time.time() - w["start"] > zeitlimit:
                _, c, g = w["item"]
                erg[(c, g)] = False
                zeitl.append([c, g])
                fertig += 1
                print(f"  Zeitlimit: {c[:60]!r} (gold {g[:30]!r}) → als nicht richtig gezählt", flush=True)
                w["p"].terminate()
                starte(wid)
    for w in W.values():
        w["inq"].put(None)
    speichern(erg)
    json.dump(zeitl, open(ZEITLIMIT_LISTE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"gespeichert: {CACHE} ({len(erg)} Paare, {time.time() - t0:.0f} s, Zeitlimit-Fälle gesamt {len(zeitl)})", flush=True)


if __name__ == "__main__":
    main()
