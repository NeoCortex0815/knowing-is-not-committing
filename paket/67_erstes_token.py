"""Pflicht-Prüfung „erstes Token“ (07.11., nach dem WT-Prompt-Leck): p(`</think>` als erstes erzeugtes Token) auf Set-B-
Aufgabenstellungen, je Modell. Muss bei jeder WT-Variante auf dem Niveau des Basis-Modells (eigen) bleiben. CPU, kurz.
  python 67_erstes_token.py --modelle eigen=Qwen3.5-0.8B-eigen-vL V2.1=Qwen3.5-0.8B-ergo-zig --n 30
"""
import argparse
import json
import os

import numpy as np

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(HIER)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--modelle", nargs="+", required=True, help="name=ordner unter modelle/")
    ap.add_argument("--n", type=int, default=30)
    ap.add_argument("--lauf", default=os.path.join(WURZEL, "ergebnisse", "setB-ergore-t06", "ergebnisse.jsonl"))
    a = ap.parse_args()
    import torch
    import transformers as tf
    torch.set_num_threads(int(os.environ.get("WSP_THREADS", 4)))
    tok = tf.AutoTokenizer.from_pretrained(os.path.join(WURZEL, "modelle", "Qwen3.5-0.8B"))
    ZU = tok.convert_tokens_to_ids("</think>")
    P = [json.loads(z)["prompt_ids"] for z in open(a.lauf, encoding="utf-8")][:a.n]
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
        print(f"{name:8s}: p(</think> als 1. Token) Median {np.median(ps):.2e}, Max {ps.max():.2e} | Anteil > 0,01: "
              f"{100 * float((ps > 0.01).mean()):.0f} % | > 0,5: {100 * float((ps > 0.5).mean()):.0f} %", flush=True)
        del model
    json.dump(erg, open(os.path.join(WURZEL, "ergebnisse", "erstes_token_pruefung.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
