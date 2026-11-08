"""(N23) Schild-Replay (08.11.; Nutzer „Wo haben wir unseren Schilder-Testversuch mit dabei?“; Lesart vorab in ANNAHMEN 13:25).
Frage: Liefert WT-A ab, wenn die Tür an seinem EIGENEN Schild schließt? Nach WT-As Reflex-Abschlüssen gelingt die Abgabe fast nie
(N19: 1 von 32 mit \\boxed{}); die Schild-Reflex-Simulation (N18) hatte angenommen, dass sie immer gelingt.
Je WT-A-Denklauf (161–300, Seed 0; Wert-Aussagen und Wahrheits-Tor aus der Zuck-Messung 82; nur Stellen vor dem ersten </think>):
  S = erste Wert-Aussage höchstens 15 Tokens nach einem eigenen Schild (Muster wie 100);
  N = Kontrolle: die Wert-Aussage ohne Schild in den 15 Tokens davor, die S zeitlich am nächsten liegt;
  F = Feuerstelle des simulierten Schild-Reflexes (N18, τ 1), falls nicht S.
Schnitt nach dem letzten Token des Werts, dann </think> eingesetzt; Antwortteil neu, ≤ 1.024 Tokens, WT-A-GGUF, Protokoll der
Läufe (vLLM-Stil, presence 1,5), Seed 0.
  python 105_schild_replay.py --bauen                                 → daten/schild_replay.jsonl (Laptop, Tokenizer)
  python 105_schild_replay.py --laufen --server URL [--teil k/n]      → ergebnisse/schild_replay.jsonl (fortsetzbar)
  python 105_schild_replay.py --auswerten                             → Urteil N23
"""
import argparse
import json
import os
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(HIER)
ERG = os.path.join(WURZEL, "ergebnisse")
# Quelle: WT-A (Lesart N23) oder MIT (beschreibende Ergänzung, vorab eingetragen 13:3x)
QUELLEN = {"WT-A": (["s3-wta-161-210", "s3-wta-211-260", "s3-wta-261-300"], "zucken_WT-A_ergo-zigA.jsonl", "schild_replay"),
           "MIT": (["s3-mit-161-260", "s3-mit-261-300"], "zucken_MIT_mit-wt.jsonl", "schild_replay_MIT")}
WTA_DIRS, ZUCKEN, DATEN, AUS = None, None, None, None


def setze_quelle(q):
    global WTA_DIRS, ZUCKEN, DATEN, AUS
    dirs, zk, stamm = QUELLEN[q]
    WTA_DIRS, ZUCKEN = dirs, os.path.join(ERG, zk)
    DATEN, AUS = os.path.join(WURZEL, "daten", stamm + ".jsonl"), os.path.join(ERG, stamm + ".jsonl")
SCHILD = re.compile(r"(?:the final answer is|the answer is|so the answer|therefore,? the answer)", re.I)
THINK35 = {"temperature": 0.6, "top_p": 0.95, "top_k": 20, "min_p": 0.0, "presence_penalty": 1.5}
VLLM_STIL = {"repeat_last_n": 40960, "samplers": ["penalties", "temperature", "top_k", "top_p", "min_p"]}
TAU = 1.0


def bauen():
    import numpy as np
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(os.path.join(WURZEL, "modelle", "Qwen3.5-0.8B"))
    ZU = tok.convert_tokens_to_ids("</think>")
    runs = {}
    for d in WTA_DIRS:
        for z in open(os.path.join(ERG, d, "ergebnisse.jsonl"), encoding="utf-8"):
            r = json.loads(z)
            runs[r["id"]] = r
    items, n_s, n_n, n_f = [], 0, 0, 0
    for z in open(ZUCKEN, encoding="utf-8"):
        zr = json.loads(z)
        r = runs[zr["id"]]
        g = r["gen_ids"]
        zu = g.index(ZU) if ZU in g else len(g)
        st = [tok.decode([t]) for t in g[:zu]]
        gr = np.cumsum([len(s) for s in st]) if st else np.array([0])
        text = "".join(st)
        sch = [int(np.searchsorted(gr, m.end() - 1, side="right")) for m in SCHILD.finditer(text)]
        A = sorted([s for s in zr["aussagen"] if s["ok"] is not None and s["t"] < zu], key=lambda s: s["t"])

        def hinter(s):
            return any(0 <= s["t"] - t <= 15 for t in sch)
        H = [s for s in A if hinter(s)]
        if not H:
            continue
        S = H[0]
        wahl = [("S", S)]
        ohne = [s for s in A if not hinter(s)]
        if ohne:
            wahl.append(("N", min(ohne, key=lambda s: (abs(s["t"] - S["t"]), s["t"]))))
        F = next((s for s in H if s["zT_max"] >= TAU), None)
        if F is not None and F["t"] != S["t"]:
            wahl.append(("F", F))
        for art, s in wahl:
            items.append({"id": zr["id"], "gold": r["gold"], "art": art, "t": s["t"], "wert": s["wert"], "ok": s["ok"],
                          "zT": s["zT_max"], "f_ist_s": bool(F is not None and F["t"] == S["t"]), "zu_id": ZU,
                          "prefix": r["prompt_ids"] + g[:s["t"] + 1] + [ZU], "n_prefix": len(r["prompt_ids"]) + s["t"] + 2})
        n_s += 1
        n_n += any(a == "N" for a, _ in wahl)
        n_f += any(a == "F" for a, _ in wahl)
    with open(DATEN, "w", encoding="utf-8") as f:
        for it in items:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")
    n = sorted(it["n_prefix"] for it in items)
    print(f"Läufe mit Schild-Wert S: {n_s} von 140 | mit Kontrolle N: {n_n} | zusätzliche Feuerstelle F: {n_f} | "
          f"Stellen gesamt {len(items)}; Präfix Median {n[len(n) // 2]}, max {n[-1]}, Summe {sum(n)}")
    print(f"S mit richtigem Wert: {sum(1 for it in items if it['art'] == 'S' and it['ok'])}, "
          f"N mit richtigem Wert: {sum(1 for it in items if it['art'] == 'N' and it['ok'])}")
    print(f"gespeichert: {DATEN}")


def laufen(a):
    import requests
    k, n = (int(x) for x in a.teil.split("/"))
    items = [it for i, it in enumerate(json.loads(z) for z in open(a.daten, encoding="utf-8")) if i % n == k]
    fertig = set()
    if os.path.exists(a.aus):
        for z in open(a.aus, encoding="utf-8"):
            e = json.loads(z)
            fertig.add((e["id"], e["art"]))
    lock = threading.Lock()

    def eins(it):
        if (it["id"], it["art"]) in fertig:
            return None
        body = dict(THINK35, **VLLM_STIL, prompt=it["prefix"], n_predict=a.max_tokens, seed=0, stream=False,
                    cache_prompt=True, return_tokens=True)
        t0 = time.time()
        r = requests.post(a.server.rstrip("/") + "/completion", json=body, timeout=a.timeout)
        r.raise_for_status()
        d = r.json()
        rec = {"id": it["id"], "art": it["art"], "text": d.get("content", ""), "gen_ids": d.get("tokens", []),
               "ende": "limit" if d.get("stop_type") == "limit" else d.get("stop_type", "?"),
               "tokens": d.get("tokens_predicted"), "sekunden": round(time.time() - t0, 1)}
        with lock:
            with open(a.aus, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        return rec

    with ThreadPoolExecutor(a.parallel) as ex:
        futs = [ex.submit(eins, it) for it in items]
        for i, fu in enumerate(as_completed(futs), 1):
            r = fu.result()
            if r:
                print(f"[{i}/{len(futs)}] {r['id']} {r['art']}: {r['ende']:6s} {r['tokens']} tok ({r['sekunden']} s)", flush=True)


def auswerten(a):
    import importlib.util
    sys.stdout.reconfigure(encoding="utf-8")
    s = importlib.util.spec_from_file_location("ev", os.path.join(WURZEL, "eval", "03_eval.py"))
    ev = importlib.util.module_from_spec(s)
    s.loader.exec_module(ev)
    I = {(it["id"], it["art"]): it for it in (json.loads(z) for z in open(DATEN, encoding="utf-8"))}
    R = {}
    for z in open(a.aus, encoding="utf-8"):
        e = json.loads(z)
        R[(e["id"], e["art"])] = e
    fehlt = [k for k in I if k not in R]
    print(f"Antwortteile: {len(I) - len(fehlt)} von {len(I)}" + (f" – FEHLEN {len(fehlt)}" if fehlt else ""))
    E = {}
    for k, it in I.items():
        if k not in R:
            continue
        txt = R[k]["text"]
        pred = ev.letztes_boxed(txt)
        E[k] = {"abgabe": pred is not None, "richtig": bool(pred is not None and ev.korrekt(pred, it["gold"])),
                "eos": R[k]["ende"] == "eos", "zu": "</think>" in txt, "ok_wert": it["ok"], "zT": it["zT"]}
    B = {}
    for art, name in (("S", "S – am eigenen Schild"), ("N", "N – Kontrolle ohne Schild"), ("F", "F – Reflex-Feuerstelle (zusätzlich)")):
        X = [e for (i, a_), e in E.items() if a_ == art]
        if not X:
            continue
        ab = sum(e["abgabe"] for e in X)
        print(f"== {name}: n {len(X)} | Abgabe {ab} ({100 * ab / len(X):.0f} %), davon sauber (eos) "
              f"{sum(e['abgabe'] and e['eos'] for e in X)} | richtig {sum(e['richtig'] for e in X)} | weiteres </think> "
              f"{sum(e['zu'] for e in X)}")
        for okw, nm in ((True, "richtiger Wert"), (False, "falscher Wert")):
            Y = [e for e in X if e["ok_wert"] is okw]
            if Y:
                print(f"     {nm:15s}: n {len(Y):3d} | Abgabe {sum(e['abgabe'] for e in Y):3d} | richtig {sum(e['richtig'] for e in Y):3d}")
        B[art] = {"n": len(X), "abgabe": ab, "richtig": sum(e["richtig"] for e in X)}
    paare = [i for (i, a_) in E if a_ == "S" and (i, "N") in E]
    sS = sum(E[(i, "S")]["abgabe"] for i in paare)
    sN = sum(E[(i, "N")]["abgabe"] for i in paare)
    nurS = sum(1 for i in paare if E[(i, "S")]["abgabe"] and not E[(i, "N")]["abgabe"])
    nurN = sum(1 for i in paare if E[(i, "N")]["abgabe"] and not E[(i, "S")]["abgabe"])
    rS, rN = 100 * sS / max(1, len(paare)), 100 * sN / max(1, len(paare))
    urteil = ("Schild-Abschluss liefert ab" if (rS >= 50 and rS - rN >= 20) else
              ("widerlegt" if (rS <= 20 or rS - rN <= 5) else "offen"))
    print(f"\nGepaart ({len(paare)} Läufe mit S und N): Abgabe S {sS} ({rS:.0f} %) gegen N {sN} ({rN:.0f} %); nur S {nurS}, nur N {nurN}")
    print(f"URTEIL N23 (vorab): {urteil}  (≥ 50 % und ≥ +20 Punkte: liefert ab; ≤ 20 % oder ≤ +5 Punkte: widerlegt)")
    # N18 neu gerechnet: Reflex feuert an F (oder an S, wenn F = S); Ergebnis = echte Abgabe dort, sonst tatsächlicher Lauf
    Z = {json.loads(z)["id"]: json.loads(z) for z in open(ZUCKEN, encoding="utf-8")}
    feuer = {}
    for (i, a_), it in I.items():
        if a_ == "F" or (a_ == "S" and it["f_ist_s"]):
            feuer[i] = (i, a_)
    r_ = f_ = 0
    for i, z in Z.items():
        if i in feuer and feuer[i] in E:
            e = E[feuer[i]]
            r_ += e["richtig"]
            f_ += e["abgabe"] and not e["richtig"]
        else:
            r_ += bool(z["korrekt"])
            f_ += z["art"] == "geschlossen, falsche Antwort"
    ist_r = sum(bool(z["korrekt"]) for z in Z.values())
    ist_f = sum(z["art"] == "geschlossen, falsche Antwort" for z in Z.values())
    print(f"Beschreibend – N18 mit echter Abgabe (τ {TAU:g}, feuert in {len(feuer)} Läufen): richtig {r_} (tatsächlich {ist_r}), "
          f"falsch {f_} (tatsächlich {ist_f}), S₂ {(r_ - 2 * f_) / len(Z):+.3f} (tatsächlich {(ist_r - 2 * ist_f) / len(Z):+.3f})")
    B.update({"paare": len(paare), "abgabe_S": sS, "abgabe_N": sN, "urteil": urteil, "n18_echt": [r_, f_]})
    json.dump(B, open(a.aus.replace(".jsonl", "_auswertung.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bauen", action="store_true")
    ap.add_argument("--laufen", action="store_true")
    ap.add_argument("--auswerten", action="store_true")
    ap.add_argument("--server", default="http://127.0.0.1:8096")
    ap.add_argument("--quelle", default="WT-A", choices=list(QUELLEN))
    ap.add_argument("--daten")
    ap.add_argument("--aus")
    ap.add_argument("--teil", default="0/1")
    ap.add_argument("--parallel", type=int, default=6)
    ap.add_argument("--max-tokens", type=int, default=1024)
    ap.add_argument("--timeout", type=int, default=1800)
    a = ap.parse_args()
    setze_quelle(a.quelle)
    a.daten = a.daten or DATEN
    a.aus = a.aus or AUS
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
