"""Loop-Eval über llama-server (/completion, Prompt als Token-IDs), Protokoll wie MIT "think35".

  python 03_eval.py --server http://127.0.0.1:8091 --tokenizer MODELLE/Qwen3.5-0.8B \
      --daten daten/math500.jsonl --n 40 --aus ergebnisse/basis

Misst je Aufgabe: Ende (eos / limit / loop_abbruch), Tokens, Tail-Duplikat-Anteil (8-Gramme),
ob </think> geschlossen wurde, Korrektheit (letztes \\boxed{}, math-verify; ohne das Paket bricht das Programm ab).
Speichert Prompt- und Antwort-Token für den Teacher-Forcing-Schritt (04_richtung.py).
Fortsetzbar: bereits bewertete Aufgaben im Ausgabeordner werden übersprungen.

--loop-abbruch (Standard an) bricht eine Generierung ab, sobald sie eindeutig im Kreis läuft
(Tail-Duplikat-Anteil > Schwelle nach mindestens --abbruch-ab Tokens). Spart viel Zeit; für das
exakte MIT-Protokoll --kein-abbruch setzen.

Fassung 0.4 (12.11.2026, Berichtigung des Bewertungsfehlers): Bewertet wird nur noch im Haupt-Thread. Unter Linux setzt math-verify
seine Zeitgrenze mit signal.alarm, das in Arbeits-Threads scheitert; die Fassungen davor fingen den Fehler still ab und verglichen
nur Text. Jetzt: (1) Generierung in Threads, Bewertung und Schreiben im Haupt-Thread; (2) korrekt() verweigert mit Zeitgrenze
außerhalb des Haupt-Threads (RuntimeError); (3) scheitert math-verify an einer Antwort, steht das laut im Log und im Datensatz
("bewertung": "text-rueckfall") und als Zähler in der Zusammenfassung; (4) ohne math-verify kein Lauf.
"""
import argparse
import json
import os
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

PREFIX = "<|im_start|>user\n"
SUFFIX = ("\nPlease reason step by step, and put your final answer within \\boxed{}.<|im_end|>\n"
          "<|im_start|>assistant\n<think>\n")
THINK35 = {"temperature": 0.6, "top_p": 0.95, "top_k": 20, "min_p": 0.0, "presence_penalty": 1.5}
# --vllm-stil (nur Laptop-Fassung): Sampling wie vLLM, das das MIT verwendet hat. llama.cpp-Standard weicht ab:
#   repeat_last_n 64 (Wiederholungsstrafe nur über die letzten 64 Tokens; vLLM: ganze Antwort) und
#   Temperatur ZULETZT (nach top-k/top-p; vLLM: Temperatur vor dem Filtern).
#   repeat_last_n -1 lehnt b11636 ab (Fehler 400) -> 40960 (>= Prompt + 32768 Antwort-Tokens = ganze Antwort).
VLLM_STIL = {"repeat_last_n": 40960, "samplers": ["penalties", "temperature", "top_k", "top_p", "min_p"]}
EXTRA = {}


def tail_dup8(text, woerter=400):
    w = text.split()[-woerter:]
    if len(w) < 16:
        return 0.0
    gesehen, dup = set(), 0
    for i in range(len(w) - 7):
        g = tuple(w[i:i + 8])
        dup += g in gesehen
        gesehen.add(g)
    return dup / (len(w) - 7)


def letztes_boxed(text):
    i = text.rfind("\\boxed")
    while i != -1:
        j = text.find("{", i)
        if j == -1:
            return None
        tiefe, k = 0, j
        while k < len(text):
            if text[k] == "{":
                tiefe += 1
            elif text[k] == "}":
                tiefe -= 1
                if tiefe == 0:
                    return text[j + 1:k]
            k += 1
        i = text.rfind("\\boxed", 0, i)
    return None


def _norm(s):
    s = s.strip().strip("$").replace(" ", "").replace("\\!", "").replace("\\left", "").replace("\\right", "")
    s = re.sub(r"\\text\{([^}]*)\}", r"\1", s)
    s = s.replace("dfrac", "frac").replace("tfrac", "frac").rstrip(".")
    return s


try:
    from math_verify import parse as mv_parse, verify as mv_verify
except Exception:  # pragma: no cover
    mv_parse = None


import sys as _sys
# LAPTOP-ÄNDERUNG (einzige gegenüber dem MiniPC-Original): unter Windows scheitert die Zeitbegrenzung von
# math-verify (Unterprozesse, "Zugriff verweigert") und liefert dann stillschweigend False -> abgeschaltet.
# Bewertungslogik unverändert; geprüft mit logs/test_mathverify.py (Laptop ohne Zeitbegrenzung = MiniPC: 0 Abweichungen).
# Nachtrag Fassung 0.4: Diese Prüfung lief im Haupt-Thread. Dass die Zeitgrenze unter Linux in Arbeits-Threads scheitert (und
# der Rückfall dort still nur Text verglich), hat sie nicht erfasst. Deshalb bewertet main() jetzt im Haupt-Thread.
_MV = {"parsing_timeout": None} if _sys.platform == "win32" else {}
_MV_V = {"timeout_seconds": None} if _sys.platform == "win32" else {}


RUECKFAELLE = []  # (pred, gold, Fehler): jeder frühere stille Rückfall ist jetzt sichtbar


def korrekt_mit_status(pred, gold):
    """(richtig, Status). Status "math-verify" oder "text-rueckfall"."""
    if pred is None:
        return False, "math-verify"
    if mv_parse is None:
        raise RuntimeError("math-verify fehlt – ohne das Paket misst die Bewertung etwas anderes")
    if _MV == {} and threading.current_thread() is not threading.main_thread():
        raise RuntimeError("math-verify mit Zeitgrenze nur im Haupt-Thread aufrufen (signal.alarm)")
    try:
        return bool(mv_verify(mv_parse("\\boxed{" + gold + "}", **_MV), mv_parse("\\boxed{" + pred + "}", **_MV),
                              **_MV_V)), "math-verify"
    except Exception as e:  # laut, nicht still
        RUECKFAELLE.append((pred, gold, repr(e)[:200]))
        print(f"WARNUNG Bewertung: math-verify scheitert ({repr(e)[:120]}); Text-Vergleich für pred={pred[:60]!r}",
              file=_sys.stderr, flush=True)
        return _norm(pred) == _norm(gold), "text-rueckfall"


def korrekt(pred, gold):
    return korrekt_mit_status(pred, gold)[0]


def generiere(server, ids, max_tokens, seed, abbruch, schwelle, abbruch_ab, timeout):
    body = dict(THINK35, **EXTRA, prompt=ids, n_predict=max_tokens, seed=seed, stream=True, cache_prompt=True,
                return_tokens=True)
    text, toks, ende, n = [], [], None, 0
    naechste_pruefung = abbruch_ab
    t0 = time.time()
    with requests.post(server.rstrip("/") + "/completion", json=body, stream=True, timeout=timeout) as r:
        r.raise_for_status()
        for roh in r.iter_lines(chunk_size=None):  # None: Daten sofort weiterreichen, nicht puffern
            zeile = roh.decode("utf-8", "replace") if isinstance(roh, bytes) else roh
            if not zeile or not zeile.startswith("data:"):
                continue
            d = json.loads(zeile[5:])
            text.append(d.get("content", ""))
            toks.extend(d.get("tokens", []) or [])
            n = d.get("tokens_predicted", n) or n
            if d.get("stop"):
                ende = "limit" if d.get("stop_type", "") == "limit" else "eos"
                n = d.get("tokens_predicted", n)
                break
            n_lauf = len(toks) if toks else len(text)
            if abbruch and n_lauf >= naechste_pruefung:
                naechste_pruefung = n_lauf + 256
                if tail_dup8("".join(text)) > schwelle:
                    ende = "loop_abbruch"
                    break
    voll = "".join(text)
    return {"text": voll, "gen_ids": toks, "ende": ende or "unbekannt",
            "tokens": n or len(toks), "sekunden": round(time.time() - t0, 1)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--server", default="http://127.0.0.1:8091")
    ap.add_argument("--tokenizer", required=True, help="HF-Modellordner (für Tokenizer)")
    ap.add_argument("--daten", required=True, help="jsonl mit problem/answer (MATH-500)")
    ap.add_argument("--n", type=int, default=40)
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--max-tokens", type=int, default=32768)
    ap.add_argument("--parallel", type=int, default=4)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--mischen", action="store_true", help="Aufgaben vor der Auswahl mischen (Seed)")
    ap.add_argument("--kein-abbruch", action="store_true")
    ap.add_argument("--schwelle", type=float, default=0.9)
    ap.add_argument("--abbruch-ab", type=int, default=4096)
    ap.add_argument("--timeout", type=int, default=7200)
    ap.add_argument("--aus", required=True)
    ap.add_argument("--vllm-stil", action="store_true", help="Sampling wie vLLM (MIT-Auswertung)")
    ap.add_argument("--temperatur", type=float, default=None,
                    help="Empfindlichkeitstest (Nutzer 06.11.): Temperatur statt 0,6 (z. B. 1,0 = Empfehlung Qwen3.6 Denkmodus)")
    a = ap.parse_args()
    if mv_parse is None:
        _sys.exit("math-verify fehlt – bitte installieren (ohne das Paket misst die Bewertung etwas anderes)")
    if a.vllm_stil:
        EXTRA.update(VLLM_STIL)
    if a.temperatur is not None:
        THINK35["temperature"] = a.temperatur

    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(a.tokenizer)
    zeilen = [json.loads(z) for z in open(a.daten, encoding="utf-8")]
    if a.mischen:
        import random
        random.Random(a.seed).shuffle(zeilen)
    zeilen = zeilen[a.start:a.start + a.n]
    os.makedirs(a.aus, exist_ok=True)
    pfad = os.path.join(a.aus, "ergebnisse.jsonl")
    fertig = set()
    if os.path.exists(pfad):
        fertig = {json.loads(z)["id"] for z in open(pfad, encoding="utf-8")}
    lock = threading.Lock()

    def job(i, row):
        pid = row.get("unique_id") or row.get("id") or str(a.start + i)
        if pid in fertig:
            return None
        ptext = PREFIX + row["problem"] + SUFFIX
        ids = tok(ptext, add_special_tokens=False)["input_ids"]
        g = generiere(a.server, ids, a.max_tokens, a.seed, not a.kein_abbruch, a.schwelle,
                      a.abbruch_ab, a.timeout)
        if not g["gen_ids"]:
            g["gen_ids"] = tok(g["text"], add_special_tokens=False)["input_ids"]
            g["gen_ids_quelle"] = "neu_tokenisiert"
        pred = letztes_boxed(g["text"])
        rec = {"id": pid, "gold": row["answer"], "pred": pred, "korrekt": None,  # wird im Haupt-Thread gesetzt
               "ende": g["ende"], "tokens": g["tokens"], "sekunden": g["sekunden"],
               "tail_dup8": round(tail_dup8(g["text"]), 3), "think_zu": "</think>" in g["text"],
               "prompt_ids": ids, "gen_ids": g["gen_ids"], "text": g["text"]}
        return rec

    with ThreadPoolExecutor(a.parallel) as ex:
        futs = [ex.submit(job, i, r) for i, r in enumerate(zeilen)]
        for k, fu in enumerate(as_completed(futs), 1):
            r = fu.result()
            if r:
                r["korrekt"], status = korrekt_mit_status(r["pred"], r["gold"])  # Haupt-Thread
                if status != "math-verify":
                    r["bewertung"] = status
                with lock:
                    with open(pfad, "a", encoding="utf-8") as f:
                        f.write(json.dumps(r, ensure_ascii=False) + "\n")
                print(f"[{k}/{len(futs)}] {r['id']}: {r['ende']:12s} {r['tokens']:6d} tok  "
                      f"dup8 {r['tail_dup8']:.2f}  {'OK' if r['korrekt'] else '--'}  ({r['sekunden']} s)",
                      flush=True)

    alle = [json.loads(z) for z in open(pfad, encoding="utf-8")]
    n = len(alle)
    zs = {"n": n,
          "korrekt": round(sum(r["korrekt"] for r in alle) / n, 4),
          "loop_oder_limit": round(sum(r["ende"] in ("limit", "loop_abbruch") for r in alle) / n, 4),
          "eos": round(sum(r["ende"] == "eos" for r in alle) / n, 4),
          "think_geschlossen": round(sum(r["think_zu"] for r in alle) / n, 4),
          "mittel_tokens": round(sum(r["tokens"] for r in alle) / n),
          "mittel_tail_dup8": round(sum(r["tail_dup8"] for r in alle) / n, 3),
          "protokoll": dict(THINK35, **EXTRA, max_tokens=a.max_tokens, loop_abbruch=not a.kein_abbruch,
                            schwelle=a.schwelle, abbruch_ab=a.abbruch_ab, seed=a.seed),
          "math_verify": mv_parse is not None, "bewertung": "Haupt-Thread (Fassung 0.4)",
          "bewertung_rueckfaelle": sum(1 for r in alle if r.get("bewertung") == "text-rueckfall")}
    json.dump(zs, open(os.path.join(a.aus, "zusammenfassung.json"), "w"), indent=1)
    print(json.dumps(zs, indent=1))


if __name__ == "__main__":
    main()
