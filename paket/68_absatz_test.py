"""Pflicht-Prüfung „frühe Absätze“ (07.11., nach dem Befund eigen-WT4: Denken schließt nach im Median 274 Tokens ohne Kandidat):
p(`</think>` als nächstes Token) an Absatz-Enden (`\\n\\n`) in den ersten 1.500 Denk-Tokens echter Läufe, je Modell. Diese Stellen
sind – wie das Prompt-Ende – „empfindlich“ (das Modell könnte dort aufhören zu denken) und waren in der Offline-Prüfung 58 nicht
gezielt dabei. Muss bei WT-Varianten auf eigen-Niveau bleiben. CPU.
  python 68_absatz_test.py --modelle eigen=Qwen3.5-0.8B-eigen-vL fixA=Qwen3.5-0.8B-ergo-zigA --laeufe 20 --je-lauf 8
"""
import argparse
import json
import os

import numpy as np

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(HIER)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--modelle", nargs="+", required=True)
    ap.add_argument("--quelle", default=os.path.join(WURZEL, "ergebnisse", "setB-gatter-t06", "ergebnisse.jsonl"))
    ap.add_argument("--laeufe", type=int, default=20)
    ap.add_argument("--je-lauf", type=int, default=8)
    ap.add_argument("--bis", type=int, default=1500)
    a = ap.parse_args()
    import torch
    import transformers as tf
    torch.set_num_threads(int(os.environ.get("WSP_THREADS", 4)))
    tok = tf.AutoTokenizer.from_pretrained(os.path.join(WURZEL, "modelle", "Qwen3.5-0.8B"))
    ZU = tok.convert_tokens_to_ids("</think>")
    P = []
    for z in open(a.quelle, encoding="utf-8"):
        r = json.loads(z)
        g = r["gen_ids"]
        ende = g.index(ZU) if ZU in g else len(g)
        stellen = [t for t in range(min(ende, a.bis)) if "\n\n" in tok.decode([g[t]])][:a.je_lauf]
        P += [r["prompt_ids"] + g[:t + 1] for t in stellen]
        if len(set(map(len, P))) and sum(1 for _ in P) >= a.laeufe * a.je_lauf:
            break
    print(f"{len(P)} Absatz-Enden aus den ersten {a.bis} Denk-Tokens", flush=True)
    cls = getattr(tf, "AutoModelForImageTextToText", None) or tf.AutoModelForCausalLM
    erg = {}
    for spec in a.modelle:
        name, ordner = spec.split("=", 1)
        model = cls.from_pretrained(os.path.join(WURZEL, "modelle", ordner), dtype=torch.float32).eval()
        ps = []
        for ids in P:
            with torch.no_grad():
                out = model(input_ids=torch.tensor([ids]))
            ps.append(float(torch.softmax(out.logits[0, -1].float(), -1)[ZU]))
        ps = np.array(ps)
        erg[name] = ps.tolist()
        print(f"{name:9s}: p(</think> nach Absatz) Median {np.median(ps):.2e}, 90 % {np.quantile(ps, .9):.2e}, Max {ps.max():.2e} | "
              f"> 0,01: {100 * float((ps > 0.01).mean()):.0f} % | > 0,1: {100 * float((ps > 0.1).mean()):.0f} %", flush=True)
        del model
    json.dump(erg, open(os.path.join(WURZEL, "ergebnisse", "absatz_test.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
