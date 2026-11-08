"""Replay der stummen WT-A-Antwortteile (08.11.; Argon Teil 2, Kurzversuch 1; Nutzer „wenn es nur 10 Min. sind, warum nicht“;
Lesart N19 in ANNAHMEN, vor dem ersten Lauf festgelegt).
Stumm = WT-A (MATH-500 161–300, Seed 0) hat das Denken geschlossen, im Antwortteil aber kein \\boxed{} geschrieben (32 Läufe,
davon 14 mit frühem richtigen Wert im Antwortteil laut 81_format_check).
Präfix = Prompt + Denkteil bis einschließlich des ersten </think>. Neu generiert wird nur der Antwortteil, höchstens 1.024 Tokens,
gleiches Protokoll wie die Läufe (T 0,6, top-p 0,95, top-k 20, presence 1,5, vLLM-Stil), Seed 0, WT-A-GGUF:
  Arm A: zweites </think> gesperrt (logit_bias false);
  Arm K: Kontrolle ohne Sperre (Nochmal-Effekt, Einwand WREN). Gleicher Seed: A und K laufen gekoppelt und trennen sich erst,
         wo </think> eine Rolle spielt.
Argons Arm B (Effektor −r⊥ statt ĝ) läuft nicht: Im Wirktiefe-Vortest (N12) öffnet ein Schub entlang −r⊥ die Tür gar nicht.
  python 101_replay.py --bauen                         → daten/replay_wta_stumm.jsonl (Laptop, braucht Tokenizer)
  python 101_replay.py --laufen --server URL ...       → Antwortteile (MiniPC; braucht nur requests)
  python 101_replay.py --auswerten [--erg DATEI]       → Urteil N19 (Laptop; Bewertung wie 03_eval)
"""
import argparse
import json
import os
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(HIER)
WTA_DIRS = ["s3-wta-161-210", "s3-wta-211-260", "s3-wta-261-300"]
DATEN = os.path.join(WURZEL, "daten", "replay_wta_stumm.jsonl")
ERG = os.path.join(WURZEL, "ergebnisse", "replay_wta_stumm.jsonl")
THINK35 = {"temperature": 0.6, "top_p": 0.95, "top_k": 20, "min_p": 0.0, "presence_penalty": 1.5}
VLLM_STIL = {"repeat_last_n": 40960, "samplers": ["penalties", "temperature", "top_k", "top_p", "min_p"]}


def frueh_richtig_aus_log():
    """Die 14 WT-A-Läufe mit frühem richtigen Wert im Antwortteil, wie 81_format_check sie gelistet hat."""
    ids, drin = [], False
    for z in open(os.path.join(WURZEL, "logs", "81_format_check.log"), encoding="utf-8"):
        if z.startswith("WT-A"):
            drin = True
            continue
        if drin:
            m = re.match(r"^\s+(test/\S+)", z)
            if not m:
                break
            ids.append(m.group(1))
    return ids


def bauen():
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(os.path.join(WURZEL, "modelle", "Qwen3.5-0.8B"))
    ZU = tok.convert_tokens_to_ids("</think>")
    frueh = set(frueh_richtig_aus_log())
    assert len(frueh) == 14, f"erwartet 14 Läufe mit frühem richtigen Wert, gefunden {len(frueh)}"
    zeilen = []
    for d in WTA_DIRS:
        for z in open(os.path.join(WURZEL, "ergebnisse", d, "ergebnisse.jsonl"), encoding="utf-8"):
            r = json.loads(z)
            zc = r["text"].find("</think>")
            if zc < 0 or "\\boxed" in r["text"][zc + len("</think>"):]:
                continue
            g = r["gen_ids"]
            assert ZU in g, r["id"]
            k = g.index(ZU)
            zeilen.append({"id": r["id"], "gold": r["gold"], "zu_id": ZU, "prefix": r["prompt_ids"] + g[:k + 1],
                           "n_prefix": len(r["prompt_ids"]) + k + 1, "frueh_richtig": r["id"] in frueh,
                           "weitere_zu": r["text"][zc + len("</think>"):].count("</think>"), "ende": r["ende"],
                           "korrekt_orig": bool(r["korrekt"]), "antwort_tokens_orig": len(g) - k - 1})
    assert len(zeilen) == 32, f"erwartet 32 stumme Läufe, gefunden {len(zeilen)}"
    assert frueh <= {z["id"] for z in zeilen}
    with open(DATEN, "w", encoding="utf-8") as f:
        for z in zeilen:
            f.write(json.dumps(z, ensure_ascii=False) + "\n")
    n = sorted(z["n_prefix"] for z in zeilen)
    print(f"{len(zeilen)} stumme Läufe ({sum(z['frueh_richtig'] for z in zeilen)} mit frühem richtigen Wert), "
          f"Präfix-Länge Median {n[len(n) // 2]}, max {n[-1]}, Summe {sum(n)}; ursprünglich richtig: "
          f"{sum(z['korrekt_orig'] for z in zeilen)}; mit weiterem </think>: {sum(1 for z in zeilen if z['weitere_zu'] > 0)}")
    print(f"gespeichert: {DATEN}")


def laufen(a):
    import requests
    zeilen = [json.loads(z) for z in open(a.daten, encoding="utf-8")]
    fertig = set()
    if os.path.exists(a.aus):
        fertig = {(json.loads(z)["id"], json.loads(z)["arm"]) for z in open(a.aus, encoding="utf-8")}
    lock = threading.Lock()

    def eins(z):
        aus = []
        for arm in ("A", "K"):  # gleicher Slot nacheinander: der Präfix bleibt im Cache
            if (z["id"], arm) in fertig:
                continue
            body = dict(THINK35, **VLLM_STIL, prompt=z["prefix"], n_predict=a.max_tokens, seed=a.seed, stream=False,
                        cache_prompt=True, return_tokens=True)
            if arm == "A":
                body["logit_bias"] = [[z["zu_id"], False]]
            t0 = time.time()
            r = requests.post(a.server.rstrip("/") + "/completion", json=body, timeout=a.timeout)
            r.raise_for_status()
            d = r.json()
            rec = {"id": z["id"], "arm": arm, "text": d.get("content", ""), "gen_ids": d.get("tokens", []),
                   "ende": "limit" if d.get("stop_type") == "limit" else d.get("stop_type", "?"),
                   "tokens": d.get("tokens_predicted"), "sekunden": round(time.time() - t0, 1), "seed": a.seed}
            with lock:
                with open(a.aus, "a", encoding="utf-8") as f:
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            aus.append(rec)
        return aus

    with ThreadPoolExecutor(a.parallel) as ex:
        futs = [ex.submit(eins, z) for z in zeilen]
        for k, fu in enumerate(as_completed(futs), 1):
            for r in fu.result():
                print(f"[{k}/{len(futs)}] {r['id']} Arm {r['arm']}: {r['ende']:6s} {r['tokens']} tok, "
                      f"boxed {'ja' if chr(92) + 'boxed' in r['text'] else 'nein'}, </think> {r['text'].count('</think>')} "
                      f"({r['sekunden']} s)", flush=True)


def auswerten(a):
    import importlib.util
    s = importlib.util.spec_from_file_location("ev", os.path.join(WURZEL, "eval", "03_eval.py"))
    ev = importlib.util.module_from_spec(s)
    s.loader.exec_module(ev)
    Z = {json.loads(z)["id"]: json.loads(z) for z in open(DATEN, encoding="utf-8")}
    R = {}
    for z in open(a.erg, encoding="utf-8"):
        r = json.loads(z)
        R[(r["id"], r["arm"])] = r
    zeilen = []
    for i, z in Z.items():
        e = {"id": i, "frueh": z["frueh_richtig"], "orig_ok": z["korrekt_orig"], "weitere_zu": z["weitere_zu"]}
        for arm in ("A", "K"):
            r = R.get((i, arm))
            if r is None:
                e[arm] = None
                continue
            pred = ev.letztes_boxed(r["text"])
            e[arm] = {"boxed": pred is not None, "ok": bool(pred is not None and ev.korrekt(pred, z["gold"])),
                      "eos": r["ende"] == "eos", "zu": r["text"].count("</think>"), "tokens": r["tokens"]}
        zeilen.append(e)
    fehlt = [(e["id"], arm) for e in zeilen for arm in ("A", "K") if e[arm] is None]
    print(f"Antwortteile: {2 * len(zeilen) - len(fehlt)} von {2 * len(zeilen)}" + (f" – FEHLEN: {fehlt}" if fehlt else ""))

    def zaehle(Y, arm, feld):
        return sum(1 for e in Y if e[arm] and e[arm][feld])
    B = {}
    for name, Y in (("14 mit frühem richtigen Wert", [e for e in zeilen if e["frueh"]]),
                    ("18 ohne frühen richtigen Wert", [e for e in zeilen if not e["frueh"]]), ("alle 32", zeilen)):
        print(f"\n== {name} (n {len(Y)})")
        for arm, lang in (("A", "Arm A (Sperre)"), ("K", "Kontrolle K  ")):
            ok = zaehle(Y, arm, "ok")
            sauber = sum(1 for e in Y if e[arm] and e[arm]["ok"] and e[arm]["eos"])
            print(f"   {lang}: \\boxed {zaehle(Y, arm, 'boxed'):2d} | richtig {ok:2d} (davon sauber mit eos {sauber:2d}) | "
                  f"weiteres </think> {sum(1 for e in Y if e[arm] and e[arm]['zu'] > 0):2d} | Ende eos {zaehle(Y, arm, 'eos'):2d}")
            B[f"{name} {arm}"] = {"boxed": zaehle(Y, arm, "boxed"), "richtig": ok, "sauber": sauber}
        nurA = sum(1 for e in Y if e["A"] and e["K"] and e["A"]["ok"] and not e["K"]["ok"])
        nurK = sum(1 for e in Y if e["A"] and e["K"] and e["K"]["ok"] and not e["A"]["ok"])
        print(f"   gepaart: nur A richtig {nurA}, nur K richtig {nurK}")
        B[f"{name} gepaart"] = [nurA, nurK]
    Y14 = [e for e in zeilen if e["frueh"]]
    a14 = zaehle(Y14, "A", "ok")
    urteil_argon = "bestätigt" if a14 >= 10 else ("widerlegt" if a14 < 7 else "offen")
    d = zaehle(zeilen, "A", "ok") - zaehle(zeilen, "K", "ok")
    urteil_sperre = "Sperre trägt" if d >= 3 else ("kein Sperr-Effekt" if d <= 1 else "offen")
    neu = sum(1 for e in zeilen if e["A"] and e["A"]["ok"] and not e["orig_ok"])
    print(f"\nURTEIL N19 (a) Argon, Arm A auf den 14: {a14} gerettet → {urteil_argon} (≥ 10 bestätigt, < 7 widerlegt)")
    print(f"URTEIL N19 (b) Sperre gegen Kontrolle auf den 32: A − K = {d:+d} → {urteil_sperre} (≥ +3 trägt, ≤ +1 kein Effekt)")
    print(f"Beschreibend: WT-A mit Arm A hochgerechnet {61 + neu}/140 (tatsächlich 61; +{neu} gerettete stumme Läufe)")
    B.update({"urteil_argon": urteil_argon, "urteil_sperre": urteil_sperre, "a14": a14, "A_minus_K": d, "wta_hochgerechnet": 61 + neu,
              "zeilen": zeilen})
    json.dump(B, open(a.erg.replace(".jsonl", "_auswertung.json"), "w", encoding="utf-8"),
              indent=1, ensure_ascii=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bauen", action="store_true")
    ap.add_argument("--laufen", action="store_true")
    ap.add_argument("--auswerten", action="store_true")
    ap.add_argument("--server", default="http://127.0.0.1:8091")
    ap.add_argument("--daten", default=DATEN)
    ap.add_argument("--aus", default=ERG)
    ap.add_argument("--erg", default=ERG)
    ap.add_argument("--parallel", type=int, default=12)
    ap.add_argument("--max-tokens", type=int, default=1024)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--timeout", type=int, default=1800)
    a = ap.parse_args()
    if a.bauen:
        bauen()
    elif a.laufen:
        laufen(a)
    elif a.auswerten:
        auswerten(a)
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
