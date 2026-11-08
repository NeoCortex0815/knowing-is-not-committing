"""IFEval (Anweisungstreue) über llama-server, Protokoll wie MIT (exp8_math/code/evaluate.py):
Chat-Vorlage mit Denkmodus, Sampling „think35“, max 32768 Tokens, Bewertung strict prompt-level mit den offiziellen
Google-Prüfregeln auf dem Text nach </think> (ohne </think> -> leer -> nicht erfüllt).

  python 14_ifeval.py --server http://127.0.0.1:8091 --tokenizer MODELLE/Qwen3.5-0.8B \
      --daten daten/ifeval/ifeval_input_data.jsonl --n 120 --vllm-stil --aus ergebnisse/ifeval-mit-vL

--n: die ersten n Prompts in Dateireihenfolge (gleiche Auswahl für alle Läufe; MIT-Abgleich je Prompt möglich).
Schleifen-Abbruch wie 03_eval (Standard an; --kein-abbruch für exaktes MIT-Protokoll). Fortsetzbar.
"""
import argparse
import importlib.util
import json
import os
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
import ifeval_pruefung as P  # noqa: E402


def lade_eval(pfad):
    spec = importlib.util.spec_from_file_location("eval03", pfad)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--server", default="http://127.0.0.1:8091")
    ap.add_argument("--tokenizer", required=True)
    ap.add_argument("--daten", required=True)
    ap.add_argument("--n", type=int, default=541)
    ap.add_argument("--max-tokens", type=int, default=32768)
    ap.add_argument("--parallel", type=int, default=4)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--ohne-denken", action="store_true")
    ap.add_argument("--vllm-stil", action="store_true")
    ap.add_argument("--kein-abbruch", action="store_true")
    ap.add_argument("--schwelle", type=float, default=0.9)
    ap.add_argument("--abbruch-ab", type=int, default=4096)
    ap.add_argument("--timeout", type=int, default=7200)
    ap.add_argument("--eval-modul", default=os.path.join(HIER, "..", "eval", "03_eval.py"))
    ap.add_argument("--aus", required=True)
    a = ap.parse_args()

    ev = lade_eval(a.eval_modul)
    if a.vllm_stil:
        ev.EXTRA.update(ev.VLLM_STIL)
    denken = not a.ohne_denken
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(a.tokenizer)
    zeilen = [json.loads(z) for z in open(a.daten, encoding="utf-8")][:a.n]
    os.makedirs(a.aus, exist_ok=True)
    pfad = os.path.join(a.aus, "ergebnisse.jsonl")
    fertig = {json.loads(z)["id"] for z in open(pfad, encoding="utf-8")} if os.path.exists(pfad) else set()
    lock = threading.Lock()

    def job(r):
        pid = f"ifeval_{r['key']}"
        if pid in fertig:
            return None
        ptext = tok.apply_chat_template([{"role": "user", "content": r["prompt"]}], tokenize=False,
                                        add_generation_prompt=True, enable_thinking=denken)
        ids = tok(ptext, add_special_tokens=False)["input_ids"]
        g = ev.generiere(a.server, ids, a.max_tokens, a.seed, not a.kein_abbruch, a.schwelle, a.abbruch_ab, a.timeout)
        ok, n_ok, n = P.bewerte(r, g["text"], denken=denken)
        rec = {"id": pid, "korrekt": ok, "anw_ok": n_ok, "anw_gesamt": n, "anweisungen": r["instruction_id_list"],
               "ende": g["ende"], "tokens": g["tokens"], "sekunden": g["sekunden"], "think_zu": "</think>" in g["text"],
               "tail_dup8": round(ev.tail_dup8(g["text"]), 3), "prompt_ids": ids, "gen_ids": g["gen_ids"],
               "text": g["text"]}
        with lock, open(pfad, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        return rec

    with ThreadPoolExecutor(a.parallel) as ex:
        futs = [ex.submit(job, r) for r in zeilen]
        for k, fu in enumerate(as_completed(futs), 1):
            r = fu.result()
            if r:
                print(f"[{k}/{len(futs)}] {r['id']}: {r['ende']:12s} {r['tokens']:6d} tok  "
                      f"{r['anw_ok']}/{r['anw_gesamt']} {'OK' if r['korrekt'] else '--'}", flush=True)

    alle = [json.loads(z) for z in open(pfad, encoding="utf-8")]
    n = len(alle)
    zs = {"n": n, "korrekt": round(sum(r["korrekt"] for r in alle) / n, 4),
          "anweisungen_erfuellt": round(sum(r["anw_ok"] for r in alle) / max(sum(r["anw_gesamt"] for r in alle), 1), 4),
          "loop_oder_limit": round(sum(r["ende"] in ("limit", "loop_abbruch") for r in alle) / n, 4),
          "think_geschlossen": round(sum(r["think_zu"] for r in alle) / n, 4),
          "mittel_tokens": round(sum(r["tokens"] for r in alle) / n),
          "protokoll": dict(ev.THINK35, **ev.EXTRA, max_tokens=a.max_tokens, denken=denken,
                            loop_abbruch=not a.kein_abbruch, seed=a.seed, bewertung="strict prompt-level, offiziell")}
    json.dump(zs, open(os.path.join(a.aus, "zusammenfassung.json"), "w"), indent=1)
    print(json.dumps(zs, indent=1))


if __name__ == "__main__":
    main()
