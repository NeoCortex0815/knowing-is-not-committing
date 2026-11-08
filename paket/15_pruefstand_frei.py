"""Prüfstand v2: freie Fortsetzung ab Schleifen-Eintritt (statt Teacher-Forcing wie 09_pruefstand.py).

Idee: Prüfstand v1 maß, wie stark ein Edit die Wahrscheinlichkeit VORGEGEBENER Schleifen-Tokens senkt. Das sagte die echte
Leistung nicht voraus (05.11.: v1 setzte alpha 10 vor alpha 6 und den MIT-Edit ans Ende – echt war es umgekehrt).
v2 misst, ob ein Modell beim FREIEN Weiterdenken aus einer begonnenen Schleife herausfindet – mit genau dem Sampling der
echten Messung (llama-server, THINK35 + vLLM-Stil aus eval/03_eval.py).

Ablauf je Modell (GGUF):
  1. eigener llama-server auf --port (Standard 8095, läuft neben einer laufenden Messung auf 8091), --slots Slots
  2. für jedes Diagnose-Transkript mit Schleife: Präfix = Prompt + Antwort bis Schleifenbeginn + --eintritt Tokens
     (Schleifenbeginn wie 04s: erster Lauf wiederholter 8-Gramme >= --min-lauf Tokens)
  3. --fortsetzung Tokens frei generieren (kein Schleifen-Abbruch), je --seeds Seeds
  4. Kennzahlen je Fortsetzung:
       raus        letzte 256 Fortsetzungs-Tokens überwiegend NICHT in einem Wiederholungs-Lauf, oder </think> erreicht, oder EOS
       schleife    Anteil der Fortsetzungs-Tokens in Wiederholungs-Läufen (Präfix zählt als Vorgeschichte)
       think_zu    </think> in der Fortsetzung
  5. Wertung = Anteil "raus" (Gleichstand: weniger "schleife")
Eichung: --real name=wert (echte Trefferquote) -> Spearman-Rangkorrelation und Reihenfolge; Modelle ohne --real bekommen eine
Vorhersage per linearer Anpassung (nur Anhaltspunkt).

  python 15_pruefstand_frei.py --ergebnisse ergebnisse/diagnose-vL/ergebnisse.jsonl --tokenizer modelle/Qwen3.5-0.8B \
      --modell basis=gguf/Qwen3.5-0.8B-q8_0.gguf --modell mit=gguf/Qwen3.5-0.8B-mit-q8_0.gguf ... \
      --real basis=0.10 --real mit=0.55 ... --aus ergebnisse/pruefstand2.json
"""
import argparse
import importlib.util
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import requests

HIER = os.path.dirname(os.path.abspath(__file__))


def lade_modul(name, pfad):
    spec = importlib.util.spec_from_file_location(name, pfad)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def laeufe(gen, min_lauf):
    """wie 04s labels(): rep[t] = 8-Gramm bis t schon gesehen; lauf = Läufe von rep >= min_lauf; onset = erster Lauf."""
    n = len(gen)
    rep = np.zeros(n, dtype=bool)
    gesehen = set()
    for t in range(7, n):
        g = tuple(gen[t - 7:t + 1])
        rep[t] = g in gesehen
        gesehen.add(g)
    lauf = np.zeros(n, dtype=bool)
    t, onset = 0, n
    while t < n:
        if rep[t]:
            s = t
            while t < n and rep[t]:
                t += 1
            if t - s >= min_lauf:
                lauf[s:t] = True
                onset = min(onset, s)
        else:
            t += 1
    return rep, lauf, onset


def rang(x):
    o = np.argsort(np.argsort(x, kind="stable"), kind="stable").astype(float)
    for v in set(x):  # Gleichstände: mittlerer Rang
        idx = [i for i, y in enumerate(x) if y == v]
        o[idx] = np.mean(o[idx])
    return o


def spearman(a, b):
    ra, rb = rang(list(a)), rang(list(b))
    if ra.std() == 0 or rb.std() == 0:
        return float("nan")
    return float(np.corrcoef(ra, rb)[0, 1])


def server_start(exe, gguf, port, slots, ctx):
    log = open(os.path.join(HIER, "..", "logs", f"pruefstand2-server-{port}.log"), "w")
    p = subprocess.Popen([exe, "-m", gguf, "--host", "127.0.0.1", "--port", str(port), "-c", str(slots * ctx),
                          "-np", str(slots), "-ngl", "99"], stdout=log, stderr=subprocess.STDOUT)
    for _ in range(180):
        try:
            if requests.get(f"http://127.0.0.1:{port}/health", timeout=2).ok:
                return p
        except requests.RequestException:
            pass
        if p.poll() is not None:
            raise SystemExit(f"llama-server beendet (exit {p.returncode}), siehe {log.name}")
        time.sleep(1)
    p.terminate()
    raise SystemExit("llama-server nicht bereit")


def server_stopp(p):
    p.terminate()  # nur DIESER Prozess – nie alle llama-server (daneben läuft evtl. eine echte Messung)
    try:
        p.wait(timeout=20)
    except subprocess.TimeoutExpired:
        p.kill()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ergebnisse", required=True, help="Diagnose-Transkripte (03_eval ergebnisse.jsonl)")
    ap.add_argument("--tokenizer", required=True)
    ap.add_argument("--modell", action="append", required=True, help="name=pfad.gguf (mehrfach)")
    ap.add_argument("--real", action="append", default=[], help="name=echte Trefferquote (Eichung)")
    ap.add_argument("--llama-server", default=os.path.join(HIER, "..", "llama", "bin", "llama-server.exe"))
    ap.add_argument("--eval-modul", default=os.path.join(HIER, "..", "eval", "03_eval.py"))
    ap.add_argument("--port", type=int, default=8095)
    ap.add_argument("--slots", type=int, default=4)
    ap.add_argument("--max-len", type=int, default=8192, help="max. Antwort-Tokens im Präfix")
    ap.add_argument("--eintritt", type=int, default=32, help="Tokens nach Schleifenbeginn im Präfix")
    ap.add_argument("--min-lauf", type=int, default=32)
    ap.add_argument("--fortsetzung", type=int, default=1024)
    ap.add_argument("--seeds", type=int, default=1)
    ap.add_argument("--max-texte", type=int, default=0, help="0 = alle Transkripte mit Schleife")
    ap.add_argument("--halte-zurueck", type=int, default=4, help="nur zur Auswertung: Teilmenge Index %% N == 0 getrennt zeigen")
    ap.add_argument("--aus", required=True)
    a = ap.parse_args()

    ev = lade_modul("eval03", a.eval_modul)
    ev.EXTRA.update(ev.VLLM_STIL)
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(a.tokenizer)
    think_zu_id = tok.convert_tokens_to_ids("</think>")

    texte = [json.loads(z) for z in open(a.ergebnisse, encoding="utf-8") if z.strip()]
    jobs = []
    for i, r in enumerate(texte):
        gen = r["gen_ids"][:a.max_len]
        _, _, onset = laeufe(gen, a.min_lauf)
        if onset >= len(gen):
            continue
        cut = min(onset + a.eintritt, len(gen))
        for s in range(a.seeds):
            jobs.append({"id": r["id"], "i": i, "zurueck": bool(a.halte_zurueck and i % a.halte_zurueck == 0),
                         "praefix_gen": gen[:cut], "ids": r["prompt_ids"] + gen[:cut], "seed": 1000 + s, "onset": onset})
    if a.max_texte:
        jobs = jobs[:a.max_texte * a.seeds]
    ctx = max(len(j["ids"]) for j in jobs) + a.fortsetzung + 64
    print(f"{len(jobs)} Fortsetzungen je Modell ({len({j['id'] for j in jobs})} Transkripte x {a.seeds} Seeds), "
          f"Kontext je Slot {ctx}", flush=True)

    def bewerte(j, g):
        cont = g["gen_ids"]
        voll = j["praefix_gen"] + cont
        _, lauf, _ = laeufe(voll, a.min_lauf)
        lc = lauf[len(j["praefix_gen"]):]
        zu = think_zu_id in cont or "</think>" in g["text"]
        raus = bool(zu or g["ende"] == "eos" or (len(lc) >= 64 and lc[-256:].mean() < 0.5))
        return {"id": j["id"], "seed": j["seed"], "zurueck": j["zurueck"], "n": len(cont), "ende": g["ende"],
                "raus": raus, "schleife": round(float(lc.mean()) if len(lc) else 1.0, 4), "think_zu": bool(zu),
                "dup8": round(ev.tail_dup8(g["text"]), 4)}

    erg = {"protokoll": {k: getattr(a, k) for k in ("eintritt", "min_lauf", "fortsetzung", "seeds", "max_len", "slots")},
           "sampling": dict(ev.THINK35, **ev.EXTRA), "modelle": {}}
    for spec in a.modell:
        name, gguf = spec.split("=", 1)
        t0 = time.time()
        p = server_start(a.llama_server, os.path.abspath(gguf), a.port, a.slots, ctx)
        try:
            server = f"http://127.0.0.1:{a.port}"
            with ThreadPoolExecutor(a.slots) as ex:
                einzel = list(ex.map(lambda j: bewerte(j, ev.generiere(server, j["ids"], a.fortsetzung, j["seed"],
                                                                     False, 0.9, 10 ** 9, 3600)), jobs))
        finally:
            server_stopp(p)

        def zus(rs):
            return {"n": len(rs), "raus": round(float(np.mean([r["raus"] for r in rs])), 4),
                    "schleife": round(float(np.mean([r["schleife"] for r in rs])), 4),
                    "think_zu": round(float(np.mean([r["think_zu"] for r in rs])), 4),
                    "dup8": round(float(np.mean([r["dup8"] for r in rs])), 4)}
        z = zus(einzel)
        z["zurueckgehalten"] = zus([r for r in einzel if r["zurueck"]]) if any(r["zurueck"] for r in einzel) else None
        z["sekunden"] = round(time.time() - t0)
        erg["modelle"][name] = {"gguf": gguf, "zusammenfassung": z, "einzel": einzel}
        print(f"{name:10s} raus {z['raus']:.1%}  schleife {z['schleife']:.3f}  </think> {z['think_zu']:.1%}  "
              f"dup8 {z['dup8']:.3f}  ({z['sekunden']} s)", flush=True)
        json.dump(erg, open(a.aus, "w", encoding="utf-8"), indent=1, ensure_ascii=False)

    real = {k: float(v) for k, v in (s.split("=", 1) for s in a.real)}
    wert = {n: m["zusammenfassung"]["raus"] - 1e-3 * m["zusammenfassung"]["schleife"] for n, m in erg["modelle"].items()}
    bek = [n for n in wert if n in real]
    if len(bek) >= 3:
        rho = spearman([wert[n] for n in bek], [real[n] for n in bek])
        reih_v2 = sorted(bek, key=lambda n: -wert[n])
        reih_echt = sorted(bek, key=lambda n: -real[n])
        k, d = np.polyfit([wert[n] for n in bek], [real[n] for n in bek], 1)
        vorh = {n: round(float(k * wert[n] + d), 3) for n in wert if n not in real}
        erg["eichung"] = {"spearman": round(rho, 3), "reihenfolge_v2": reih_v2, "reihenfolge_echt": reih_echt,
                          "vorhersage": vorh, "zeit": time.strftime("%Y-%m-%dT%H:%M:%S")}
        print(f"\nEICHUNG: Spearman {rho:+.2f} | v2: {' > '.join(reih_v2)} | echt: {' > '.join(reih_echt)}")
        for n, v in vorh.items():
            print(f"VORHERSAGE {n}: ~{v:.0%} richtig (lineare Anpassung an {len(bek)} Eichpunkte; grob)")
        json.dump(erg, open(a.aus, "w", encoding="utf-8"), indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
