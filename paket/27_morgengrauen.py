"""Morgengrauen (Idee Nutzer 06.11.): Schweigen nach der Klingel → ehrlicher Zwischenstand → Fortsetzung in einer neuen Runde.

Runde 1 (wiederverwendet): Denken einer früheren Klingel-Messung (03b) bis zur Klingel (gen_ids[:denk_tokens]).
Statt „gib die Antwort“: Zwischenstand-Satz → das Modell schreibt Notizen (beste Antwort, falls vorhanden, und Offenes).
Runde 2: neue Anfrage = Aufgabe + NUR die Notizen (wie Qwen-Vorlagen das Denken früherer Runden verwerfen) + „mach weiter“;
Denkbudget wie Runde 1, danach dieselbe harte Klingel wie 03b, Antwort bewertet.
  python 27_morgengrauen.py --server http://127.0.0.1:8095 --tokenizer modelle/Qwen3.5-0.8B \
      --runde1 ergebnisse/klingel-hart2k-eigen/ergebnisse.jsonl --daten daten/practice/math_train_leicht60.jsonl \
      --nur-falsche --seed 1 --aus ergebnisse/morgengrauen
"""
import argparse
import importlib.util
import json
import os
import threading
from concurrent.futures import ThreadPoolExecutor

HIER = os.path.dirname(os.path.abspath(__file__))
ZWISCHEN = ("\n\nConsidering the limited time by the user, I have to stop thinking now and write down honest notes: "
            "my best current answer (if I have one) and what is still open.\n</think>\n\n**Notes so far:**\n")


def lade(name, pfad):
    s = importlib.util.spec_from_file_location(name, pfad)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--server", default="http://127.0.0.1:8095")
    ap.add_argument("--tokenizer", required=True)
    ap.add_argument("--runde1", required=True)
    ap.add_argument("--daten", required=True)
    ap.add_argument("--nur-falsche", action="store_true")
    ap.add_argument("--max", type=int, default=0)
    ap.add_argument("--notizen-max", type=int, default=400)
    ap.add_argument("--denkbudget", type=int, default=2048)
    ap.add_argument("--antwort-max", type=int, default=1024)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--parallel", type=int, default=4)
    ap.add_argument("--aus", required=True)
    a = ap.parse_args()
    ev = lade("eval03", os.path.join(HIER, "..", "eval", "03_eval.py"))
    bb = lade("budget03b", os.path.join(HIER, "03b_budget_eval.py"))
    profil = dict(ev.THINK35, **ev.VLLM_STIL)
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(a.tokenizer)
    enc = lambda s: tok(s, add_special_tokens=False)["input_ids"]
    aufg = {}
    for z in open(a.daten, encoding="utf-8"):
        row = json.loads(z)
        aufg[row.get("unique_id") or row.get("id")] = row
    r1 = [json.loads(z) for z in open(a.runde1, encoding="utf-8")]
    if a.nur_falsche:
        r1 = [r for r in r1 if not r.get("korrekt")]
    if a.max:
        r1 = r1[:a.max]
    os.makedirs(a.aus, exist_ok=True)
    pfad = os.path.join(a.aus, "ergebnisse.jsonl")
    lock = threading.Lock()

    def job(r):
        row = aufg[r["id"]]
        denk = r["gen_ids"][:r["denk_tokens"]]
        notiz, _, _, _ = bb.completion(a.server, r["prompt_ids"] + denk + enc(ZWISCHEN), a.notizen_max, a.seed, profil, 1800)
        notiz = notiz.split("<|im_end|>")[0].strip()
        frage = (row["problem"].rstrip() + "\n\nNotes from your earlier, unfinished attempt at this problem:\n" + notiz
                 + "\n\nContinue from these notes.")
        ids = enc(ev.PREFIX + frage + ev.SUFFIX)
        txt, gen, stop, n1 = bb.completion(a.server, ids, a.denkbudget, a.seed, profil, 1800)
        erzwungen = False
        if stop == "limit":
            if "</think>" not in txt:
                erzwungen = True
                t2, g2, stop, _ = bb.completion(a.server, ids + gen + enc(bb.ABSCHLUSS), a.antwort_max, a.seed, profil, 1800)
                txt, gen = txt + bb.ABSCHLUSS + t2, gen + enc(bb.ABSCHLUSS) + g2
            else:
                t2, g2, stop, _ = bb.completion(a.server, ids + gen, a.antwort_max, a.seed, profil, 1800)
                txt, gen = txt + t2, gen + g2
        pred = ev.letztes_boxed(txt.split("</think>")[-1])
        kand = ev.letztes_boxed(notiz)
        rec = {"id": r["id"], "gold": row["answer"], "notiz": notiz, "notiz_kandidat": kand,
               "notiz_kandidat_richtig": bool(kand) and bool(ev.korrekt(kand, row["answer"])),
               "pred": pred, "korrekt": bool(ev.korrekt(pred, row["answer"])), "ende": "eos" if stop != "limit" else "limit",
               "erzwungen": erzwungen, "denk_tokens_runde2": n1, "tokens_runde2": len(gen)}
        with lock, open(pfad, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        print(f"{r['id']}: Notiz-Kandidat {kand!r} | Runde 2: {pred!r} {'OK' if rec['korrekt'] else '--'} ({rec['ende']})", flush=True)
        return rec

    with ThreadPoolExecutor(a.parallel) as ex:
        erg = list(ex.map(job, r1))
    n = len(erg)
    print(f"\nMORGENGRAUEN: {n} Aufgaben | Notiz enthält Kandidat {sum(bool(e['notiz_kandidat']) for e in erg)}"
          f" (davon richtig {sum(e['notiz_kandidat_richtig'] for e in erg)}) | Runde 2 richtig {sum(e['korrekt'] for e in erg)}"
          f" | falsch abgegeben {sum(e['ende'] == 'eos' and not e['korrekt'] for e in erg)}")


if __name__ == "__main__":
    main()
