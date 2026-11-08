"""Alltagsprofil mit ERZWUNGENER Antwort: Denken auf N Tokens begrenzt, dann muss das Modell antworten.

Wie ein Server mit --reasoning-budget N: Hat das Modell nach N Tokens das Denken (</think>) nicht beendet, wird
der von Qwen empfohlene Abschluss eingefügt ("Considering the limited time ... </think>") und die Antwort
(höchstens --antwort-max Tokens) erzeugt. Bewertet wird das letzte \\boxed{} der Antwort (math-verify, wie 03_eval).
Gleiche Aufgaben, gleiches Sampling (MIT "think35") wie 03_eval.py; nur das Denkbudget ist anders.

  python 03b_budget_eval.py --server http://127.0.0.1:8091 --tokenizer MODELLE/Qwen3.5-0.8B \
      --daten daten/math500.jsonl --n 40 --denkbudget 8192 --aus ergebnisse/basis-b8k-L
Fortsetzbar wie 03_eval.py.
"""
import argparse
import importlib.util
import json
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

HIER = os.path.dirname(os.path.abspath(__file__))
ABSCHLUSS = ("\n\nConsidering the limited time by the user, I have to give the solution based on the thinking "
             "directly now.\n</think>\n\n")


def lade_eval(pfad):
    spec = importlib.util.spec_from_file_location("eval03", pfad)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def completion(server, ids, n, seed, profil, timeout):
    body = dict(profil, prompt=ids, n_predict=n, seed=seed, stream=False, cache_prompt=True, return_tokens=True)
    r = requests.post(server.rstrip("/") + "/completion", json=body, timeout=timeout)
    r.raise_for_status()
    d = r.json()
    return d.get("content", ""), list(d.get("tokens") or []), d.get("stop_type", ""), d.get("tokens_predicted", 0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--server", default="http://127.0.0.1:8091")
    ap.add_argument("--tokenizer", required=True)
    ap.add_argument("--daten", required=True)
    ap.add_argument("--n", type=int, default=40)
    ap.add_argument("--denkbudget", type=int, default=8192)
    ap.add_argument("--antwort-max", type=int, default=1024)
    ap.add_argument("--parallel", type=int, default=4)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--timeout", type=int, default=3600)
    ap.add_argument("--eval-modul", default=os.path.join(HIER, "..", "eval", "03_eval.py"))
    ap.add_argument("--vllm-stil", action="store_true", help="Sampling wie vLLM (siehe eval/03_eval.py VLLM_STIL)")
    ap.add_argument("--aus", required=True)
    a = ap.parse_args()

    ev = lade_eval(a.eval_modul)
    if a.vllm_stil:  # Profil für alle Anfragen dieses Laufs um die vLLM-Einstellungen ergänzen
        ev.THINK35 = dict(ev.THINK35, **ev.VLLM_STIL)
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(a.tokenizer)
    ab_ids = tok(ABSCHLUSS, add_special_tokens=False)["input_ids"]
    zeilen = [json.loads(z) for z in open(a.daten, encoding="utf-8")][:a.n]
    os.makedirs(a.aus, exist_ok=True)
    pfad = os.path.join(a.aus, "ergebnisse.jsonl")
    fertig = {json.loads(z)["id"] for z in open(pfad, encoding="utf-8")} if os.path.exists(pfad) else set()
    lock = threading.Lock()

    def job(i, row):
        pid = row.get("unique_id") or row.get("id") or str(i)
        if pid in fertig:
            return None
        ids = tok(ev.PREFIX + row["problem"] + ev.SUFFIX, add_special_tokens=False)["input_ids"]
        t0 = time.time()
        txt, gen, stop, n1 = completion(a.server, ids, a.denkbudget, a.seed, ev.THINK35, a.timeout)
        erzwungen = False
        if stop == "limit":  # Budget erschöpft
            if "</think>" not in txt:
                erzwungen = True
                txt2, gen2, stop, n2 = completion(a.server, ids + gen + ab_ids, a.antwort_max, a.seed, ev.THINK35,
                                                  a.timeout)
                txt, gen = txt + ABSCHLUSS + txt2, gen + ab_ids + gen2
            else:  # Denken fertig, Antwort angefangen -> zu Ende schreiben lassen
                txt2, gen2, stop, n2 = completion(a.server, ids + gen, a.antwort_max, a.seed, ev.THINK35, a.timeout)
                txt, gen = txt + txt2, gen + gen2
        antwort = txt.split("</think>")[-1]
        pred = ev.letztes_boxed(antwort)
        rec = {"id": pid, "gold": row["answer"], "pred": pred, "korrekt": ev.korrekt(pred, row["answer"]),
               "ende": "eos" if stop != "limit" else "limit", "erzwungen": erzwungen,
               "denk_tokens": n1, "tokens": len(gen), "sekunden": round(time.time() - t0, 1),
               "tail_dup8": round(ev.tail_dup8(txt), 3), "think_zu": "</think>" in txt,
               "prompt_ids": ids, "gen_ids": gen, "text": txt}
        with lock, open(pfad, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        return rec

    with ThreadPoolExecutor(a.parallel) as ex:
        futs = [ex.submit(job, i, r) for i, r in enumerate(zeilen)]
        for k, fu in enumerate(as_completed(futs), 1):
            r = fu.result()
            if r:
                print(f"[{k}/{len(futs)}] {r['id']}: {'erzwungen' if r['erzwungen'] else 'selbst  '} "
                      f"{r['tokens']:6d} tok {'OK' if r['korrekt'] else '--'} ({r['sekunden']} s)", flush=True)

    alle = [json.loads(z) for z in open(pfad, encoding="utf-8")]
    n = len(alle)
    zs = {"n": n, "denkbudget": a.denkbudget, "antwort_max": a.antwort_max,
          "korrekt": round(sum(r["korrekt"] for r in alle) / n, 4),
          "erzwungen": round(sum(r["erzwungen"] for r in alle) / n, 4),
          "selbst_fertig": round(sum(not r["erzwungen"] and r["think_zu"] for r in alle) / n, 4),
          "korrekt_wenn_erzwungen": round(sum(r["korrekt"] for r in alle if r["erzwungen"]) /
                                          max(sum(r["erzwungen"] for r in alle), 1), 4),
          "mittel_tokens": round(sum(r["tokens"] for r in alle) / n),
          "protokoll": dict(ev.THINK35, seed=a.seed, abschluss=ABSCHLUSS.strip())}
    json.dump(zs, open(os.path.join(a.aus, "zusammenfassung.json"), "w"), indent=1)
    print(json.dumps(zs, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
