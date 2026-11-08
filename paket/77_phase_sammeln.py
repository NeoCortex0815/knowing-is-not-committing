"""Phasen-Daten für die WT-Reparatur (07.11. abends; Nutzer-Go „Ja, so machen“: Reparatur offline bauen, morgens auf Set B testen).
Befund: WT-A schreibt im Antwortteil wieder `</think>` (36/60 Läufe, 46 % der Tokens danach). Geplante Reparatur: eine kleine
„Antwort-Bremse“ (eigene ruhige Neuronen in Schicht 15), die NUR nach dem ersten `</think>` öffnet und entlang −ĝ schiebt.
Dafür braucht es ein Phasen-Signal am MLP-Eingang von Schicht 15: Denken gegen Antwortteil.
Sammelt mit eigen-vL (CPU, fp32; Schicht-15-MLP-Eingang ist für alle unsere Modelle gleich) aus vorhandenen Läufen:
  denken      – zufällige Denk-Tokens
  spaet       – die 12 Tokens direkt vor dem ersten `</think>` (harte Gegenbeispiele: hier soll WT zünden, die Bremse NICHT)
  antwort     – zufällige Tokens im Antwortteil
  vor_zweitem – die 4 Tokens vor jedem weiteren `</think>` im Antwortteil (hier soll die Bremse greifen)
  python 77_phase_sammeln.py --aus ergebnisse/phase_sammlung.npz
"""
import argparse
import json
import os
import re

import numpy as np

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(HIER)
ERG = os.path.join(WURZEL, "ergebnisse")
QUELLEN = ["setB30-wta-t06", "minipc-b2-wta-t06", "setB-ergore-t06", "tag2-test40-kw75", "mit-vstil-L", "setB30-eigen-t06"]


class Stopp(Exception):
    pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--aus", default=os.path.join(ERG, "phase_sammlung.npz"))
    ap.add_argument("--max-denken", type=int, default=6000, help="nur Läufe, deren erstes </think> davor liegt")
    ap.add_argument("--antwort-max", type=int, default=3000, help="Antwortteil höchstens so viele Tokens")
    ap.add_argument("--je-quelle", type=int, default=8)
    ap.add_argument("--zufall", type=int, default=40)
    a = ap.parse_args()
    import torch
    import transformers as tf
    torch.set_num_threads(int(os.environ.get("WSP_THREADS", 3)))
    tok = tf.AutoTokenizer.from_pretrained(os.path.join(WURZEL, "modelle", "Qwen3.5-0.8B"))
    ZU = tok.convert_tokens_to_ids("</think>")
    cls = getattr(tf, "AutoModelForImageTextToText", None) or tf.AutoModelForCausalLM
    model = cls.from_pretrained(os.path.join(WURZEL, "modelle", "Qwen3.5-0.8B-eigen-vL"), dtype=torch.float32).eval()
    sp = {}
    for n, m in model.named_modules():
        if "visual" in n:
            continue
        if re.search(r"(language_model|model)\.layers\.15\.mlp$", n):
            m.register_forward_pre_hook(lambda mod, inp: sp.__setitem__("x", inp[0][0].detach().float().numpy()))
        if re.search(r"(language_model|model)\.layers\.15\.mlp\.down_proj$", n):
            def stopp(mod, inp):
                raise Stopp()
            m.register_forward_pre_hook(stopp)
    rng = np.random.default_rng(0)
    X, art, lauf, phase = [], [], [], []
    for q in QUELLEN:
        p = os.path.join(ERG, q, "ergebnisse.jsonl")
        if not os.path.exists(p):
            continue
        R = [json.loads(z) for z in open(p, encoding="utf-8")]
        R = [r for r in R if ZU in r["gen_ids"] and r["gen_ids"].index(ZU) < a.max_denken]
        R = sorted(R, key=lambda r: r["id"])[:a.je_quelle]
        for r in R:
            g = r["gen_ids"]
            k1 = g.index(ZU)
            ende = min(len(g), k1 + 1 + a.antwort_max)
            ids = r["prompt_ids"] + g[:ende]
            p0 = len(r["prompt_ids"])
            sp.clear()
            try:
                with torch.no_grad():
                    model(input_ids=torch.tensor([ids]))
            except Stopp:
                pass
            H = sp["x"][p0:]
            weitere = [i for i in range(k1 + 1, ende) if g[i] == ZU]
            wahl = []
            if k1 > 20:
                wahl += [(int(t), "denken") for t in rng.choice(np.arange(0, k1 - 12), size=min(a.zufall, k1 - 12), replace=False)]
            wahl += [(t, "spaet") for t in range(max(0, k1 - 12), k1)]
            ant = [t for t in range(k1 + 1, ende) if g[t] != ZU]
            if ant:
                wahl += [(int(t), "antwort") for t in rng.choice(ant, size=min(a.zufall, len(ant)), replace=False)]
            for w in weitere:
                wahl += [(t, "vor_zweitem") for t in range(max(k1 + 1, w - 4), w)]
            for t, k in wahl:
                X.append(H[t].astype(np.float32))
                art.append(k)
                lauf.append(f"{q}/{r['id']}")
                phase.append(0 if k in ("denken", "spaet") else 1)
            print(f"{q} {r['id']}: Denken {k1}, Antwort {ende - k1 - 1}, weitere </think> {len(weitere)}", flush=True)
    np.savez_compressed(a.aus, X=np.stack(X), art=np.array(art), lauf=np.array(lauf), phase=np.array(phase))
    print(f"gespeichert: {a.aus} – {len(X)} Stellen: " + ", ".join(f"{k} {art.count(k)}" for k in ("denken", "spaet", "antwort", "vor_zweitem")))


if __name__ == "__main__":
    main()
