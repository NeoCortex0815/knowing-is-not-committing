"""Antwort-Zwang-Probe (07.11. ~09:40; nur vorhandene Läufe, keine neuen Aufgaben-Läufe):
Läufe OHNE saubere Antwort (Denken zu, aber kein boxed+eos im Antwortteil = „leeres Zucken“, oder Denken nie zu) werden
abgeschnitten und mit „The final answer is $\\boxed{“ zu einer Antwort gezwungen (wie das Budget-Forcing in s1).
Varianten:
  ende       – nach dem vollständigen Lauf (bei nie geschlossenem Denken vorher `</think>` einsetzen): das praktische Protokoll
               „Antwort erzwingen, wenn am Budget-Ende keine Antwort da ist“;
  schliessen – direkt nach dem eigenen `</think>` des Modells (nur Zuck-Läufe): Hatte es beim Schließen eine Antwort parat?
Gleiche Sampling-Einstellungen wie der Lauf (THINK35 + vLLM-Stil, Temperatur des Laufs, Seed 0), 48 neue Tokens.
Richtige Läufe und Läufe mit sauberer (falscher) Antwort bleiben unverändert. Fortsetzbar; je Anfrage bis zu 3 Versuche.
  python 60_antwort_zwang.py --lauf ergebnisse/setB-ergore-t06 --server http://127.0.0.1:8096 --temperatur 0.6
"""
import argparse
import concurrent.futures as cf
import importlib.util
import json
import os
import time

import requests

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(HIER)
ZWANG = "\n\nThe final answer is $\\boxed{"


def lade(name, pfad):
    s = importlib.util.spec_from_file_location(name, pfad)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lauf", required=True)
    ap.add_argument("--server", required=True)
    ap.add_argument("--temperatur", type=float, required=True)
    ap.add_argument("--tokenizer", default=os.path.join(WURZEL, "modelle", "Qwen3.5-0.8B"))
    ap.add_argument("--n-neu", type=int, default=48)
    ap.add_argument("--parallel", type=int, default=6)
    ap.add_argument("--aus", default=None)
    a = ap.parse_args()
    ev = lade("ev", os.path.join(WURZEL, "eval", "03_eval.py"))
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(a.tokenizer)
    ZU = tok.convert_tokens_to_ids("</think>")
    zwang_ids = tok.encode(ZWANG, add_special_tokens=False)
    zu_zwang_ids = tok.encode("\n</think>" + ZWANG, add_special_tokens=False)
    assert ZU in zu_zwang_ids, "`</think>` wird nicht als ein Token kodiert"
    lauf = a.lauf if os.path.isabs(a.lauf) else os.path.join(WURZEL, a.lauf)
    aus = a.aus or os.path.join(WURZEL, "ergebnisse", "antwort_zwang", os.path.basename(lauf.rstrip("/\\")) + ".jsonl")
    os.makedirs(os.path.dirname(aus), exist_ok=True)
    R = [json.loads(z) for z in open(os.path.join(lauf, "ergebnisse.jsonl"), encoding="utf-8")]
    box = "\\boxed{"
    fertig = set()
    if os.path.exists(aus):
        fertig = {(json.loads(z)["id"], json.loads(z)["variante"]) for z in open(aus, encoding="utf-8")}
    body0 = dict(ev.THINK35, **ev.VLLM_STIL)
    body0["temperature"] = a.temperatur
    jobs = []
    for r in R:
        zu = "</think>" in r["text"]
        sauber = zu and box in r["text"].split("</think>", 1)[1] and r["ende"] == "eos"
        if r["korrekt"] or sauber:
            continue
        g = r["gen_ids"]
        if zu:
            jobs.append((r, "ende", r["prompt_ids"] + g + zwang_ids))
            if ZU in g:
                jobs.append((r, "schliessen", r["prompt_ids"] + g[:g.index(ZU) + 1] + zwang_ids))
        else:
            jobs.append((r, "ende", r["prompt_ids"] + g + zu_zwang_ids))
    jobs = [j for j in jobs if (j[0]["id"], j[1]) not in fertig]
    print(f"{os.path.basename(lauf)}: {len(R)} Läufe, {len(jobs)} Zwang-Anfragen offen (Temperatur {a.temperatur})", flush=True)

    def frage(job):
        r, var, ids = job
        for v in range(3):
            try:
                body = dict(body0, prompt=ids, n_predict=a.n_neu, seed=0, stream=False, cache_prompt=False)
                d = requests.post(a.server.rstrip("/") + "/completion", json=body, timeout=900).json()
                inhalt = d.get("content", "")
                pred = ev.letztes_boxed(box + inhalt)
                return {"id": r["id"], "variante": var, "gold": r["gold"], "pred": pred, "korrekt": bool(pred) and bool(ev.korrekt(pred, r["gold"])),
                        "ende_vorher": r["ende"], "denken_zu": "</think>" in r["text"], "praefix_tokens": len(ids), "inhalt": inhalt[:300]}
            except Exception as e:  # noqa: BLE001 – Socket-/Serverfehler: warten, wiederholen
                print(f"  Versuch {v + 1} {r['id']} {var}: {type(e).__name__}", flush=True)
                time.sleep(10)
        return None

    fehlend = 0
    with open(aus, "a", encoding="utf-8") as f, cf.ThreadPoolExecutor(a.parallel) as ex:
        for erg in ex.map(frage, jobs):
            if erg:
                f.write(json.dumps(erg, ensure_ascii=False) + "\n")
                f.flush()
            else:
                fehlend += 1
    E = [json.loads(z) for z in open(aus, encoding="utf-8")]
    richtig = sum(bool(r["korrekt"]) for r in R)
    zus = {"lauf": os.path.basename(lauf), "laeufe": len(R), "richtig_vorher": richtig}
    for var in ("ende", "schliessen"):
        ev_ = [e for e in E if e["variante"] == var]
        zus[var] = {"angefragt": len(ev_), "gerettet": sum(e["korrekt"] for e in ev_), "ohne_antwort": sum(not e["pred"] for e in ev_)}
    zus["richtig_mit_zwang_ende"] = richtig + zus["ende"]["gerettet"]
    json.dump(zus, open(aus.replace(".jsonl", "_zusammenfassung.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(json.dumps(zus, ensure_ascii=False), flush=True)
    if fehlend:
        print(f"{fehlend} Anfragen ohne Antwort – Lauf wiederholen (Fortsetzen)", flush=True)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
