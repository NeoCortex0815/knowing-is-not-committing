"""Faire Klingel (Nutzer 06.11.: „Wann ist fair?“): eigenen Abschluss-Impuls verstärken statt Entschluss aufzwingen.

aufzeichnen: normal denken lassen (Denkmodus, vLLM-Sampling), je Token den Abschluss-Impuls p(</think>) an dieser Stelle
             aus den Top-20-Wahrscheinlichkeiten des Servers (n_probs) mitschreiben. Fortsetzbar je Aufgabe.
simulieren:  Klingel läutet am ersten Token, an dem (a) ein Antwort-Kandidat im Denken steht (\\boxed{…} / „answer is …“)
             und (b) p(</think>) ≥ Schwelle. Antwort = letzter Kandidat davor. Je Schwelle: wie oft geläutet, wie oft
             richtig/falsch, gesparte Tokens; Vergleich mit dem natürlichen Ende bis zum Budget.
  python 28_faire_klingel.py aufzeichnen --server http://127.0.0.1:8095 --tokenizer modelle/Qwen3.5-0.8B \
      --daten daten/practice/math_train_leicht60.jsonl --n 20 --budget 6144 --aus ergebnisse/faire-klingel-auf
  python 28_faire_klingel.py simulieren --tokenizer modelle/Qwen3.5-0.8B --auf ergebnisse/faire-klingel-auf
"""
import argparse
import importlib.util
import json
import math
import os
import threading
from concurrent.futures import ThreadPoolExecutor

import requests

HIER = os.path.dirname(os.path.abspath(__file__))


def lade(name, datei):
    s = importlib.util.spec_from_file_location(name, os.path.join(HIER, datei))
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


def aufzeichnen(a):
    ev = lade("ev", os.path.join("..", "eval", "03_eval.py"))
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(a.tokenizer)
    zu = tok.convert_tokens_to_ids("</think>")
    zeilen = [json.loads(z) for z in open(a.daten, encoding="utf-8")][:a.n]
    os.makedirs(a.aus, exist_ok=True)
    pfad = os.path.join(a.aus, "aufzeichnung.jsonl")
    fertig = {json.loads(z)["id"] for z in open(pfad, encoding="utf-8")} if os.path.exists(pfad) else set()
    lock = threading.Lock()
    profil = dict(ev.THINK35, **ev.VLLM_STIL)

    def job(row):
        pid = row.get("unique_id") or row.get("id")
        if pid in fertig:
            return
        ids = tok(ev.PREFIX + row["problem"] + ev.SUFFIX, add_special_tokens=False)["input_ids"]
        body = dict(profil, prompt=ids, n_predict=a.budget, seed=a.seed, stream=True, cache_prompt=True, n_probs=20,
                    return_tokens=True)
        gen, pz, text = [], [], []
        with requests.post(a.server.rstrip("/") + "/completion", json=body, stream=True, timeout=3600) as r:
            r.raise_for_status()
            for roh in r.iter_lines(chunk_size=None):
                if not roh or not roh.startswith(b"data:"):
                    continue
                d = json.loads(roh[5:])
                for e in d.get("completion_probabilities") or []:
                    gen.append(e["id"])
                    p = 0.0
                    for t in e.get("top_logprobs") or []:
                        if t["id"] == zu:
                            p = math.exp(t["logprob"])
                    pz.append(round(p, 5))
                text.append(d.get("content", ""))
                if d.get("stop"):
                    break
        rec = {"id": pid, "gold": row["answer"], "gen_ids": gen, "p_zu": pz, "text": "".join(text),
               "zu_bei": gen.index(zu) if zu in gen else None}
        txt = rec["text"]
        rec["pred"] = ev.letztes_boxed(txt.split("</think>")[-1]) if "</think>" in txt else None
        rec["korrekt"] = bool(rec["pred"]) and bool(ev.korrekt(rec["pred"], row["answer"]))
        with lock, open(pfad, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        print(f"{pid}: {len(gen)} Tok, </think> bei {rec['zu_bei']}, max p_zu {max(pz) if pz else 0:.3f}, richtig {rec['korrekt']}", flush=True)

    with ThreadPoolExecutor(a.parallel) as ex:
        list(ex.map(job, zeilen))


def simulieren(a):
    ev = lade("ev", os.path.join("..", "eval", "03_eval.py"))
    kr = lade("kr", "23_klingel_regel.py")
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(a.tokenizer)
    rs = [json.loads(z) for z in open(os.path.join(a.auf, "aufzeichnung.jsonl"), encoding="utf-8")]
    natuerlich = sum(r["korrekt"] for r in rs)
    print(f"{len(rs)} Aufgaben | natürliches Ende bis Budget: richtig {natuerlich}, abgeschlossen {sum(r['zu_bei'] is not None for r in rs)}")
    # Token-genaue Kandidatenpositionen: Text Token für Token aufbauen
    vorb = []
    for r in rs:
        stuecke = [tok.decode([t]) for t in r["gen_ids"]]
        grenzen, acc = [], 0
        for s in stuecke:
            acc += len(s)
            grenzen.append(acc)
        denk = "".join(stuecke).split("</think>")[0]
        kand = [(pos, c) for pos, c in kr.kandidaten(denk)]
        vorb.append((r, grenzen, kand))
    for schwelle in [float(x) for x in a.schwellen.split(",")]:
        gel = richtig = falsch = 0
        gespart, offen_gerettet = [], 0
        for r, grenzen, kand in vorb:
            ende = r["zu_bei"] if r["zu_bei"] is not None else len(r["gen_ids"])
            hit = None
            ki = 0
            letzter = None
            for t in range(ende):
                while ki < len(kand) and kand[ki][0] < grenzen[t]:
                    letzter = kand[ki][1]
                    ki += 1
                if letzter and r["p_zu"][t] >= schwelle:
                    hit = (t, letzter)
                    break
            if hit:
                gel += 1
                ok = bool(ev.korrekt(hit[1], r["gold"]))
                richtig += ok
                falsch += not ok
                gespart.append(ende - hit[0])
                offen_gerettet += ok and not r["korrekt"]
            else:
                richtig += r["korrekt"]
        print(f"Schwelle {schwelle:>5}: geläutet {gel:2d} | gesamt richtig {richtig:2d} (davon neu gerettet {offen_gerettet}) | "
              f"falsch geläutet {falsch:2d} | gespart im Mittel {sum(gespart) / max(len(gespart), 1):,.0f} Tok")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("aufzeichnen")
    s.add_argument("--server", default="http://127.0.0.1:8095"); s.add_argument("--tokenizer", required=True)
    s.add_argument("--daten", required=True); s.add_argument("--n", type=int, default=20)
    s.add_argument("--budget", type=int, default=6144); s.add_argument("--seed", type=int, default=0)
    s.add_argument("--parallel", type=int, default=4); s.add_argument("--aus", required=True)
    m = sub.add_parser("simulieren")
    m.add_argument("--tokenizer", required=True); m.add_argument("--auf", required=True)
    m.add_argument("--schwellen", default="0.005,0.01,0.02,0.05,0.1,0.2")
    a = ap.parse_args()
    aufzeichnen(a) if a.cmd == "aufzeichnen" else simulieren(a)


if __name__ == "__main__":
    main()
