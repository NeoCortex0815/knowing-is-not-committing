"""Nachuntersuchung Kompakt-Test (07.11. ~13:40): Warum schließen V2.1/V2.2 in rund einem Drittel der Läufe das Denken schon beim
ERSTEN Token? Prüft auf Set-B-Aufgabenstellungen (CPU, kurz): (a) p(`</think>` als erstes Token nach dem Prompt) für eigen und
V2.1, (b) wo im Prompt die 16 WT-Neuronen feuern (Summe der Aktivierungen am Eingang von down_proj, Schicht 15).
  python 64_wt_frueh_zuendung.py --ids <id1> <id2> ...
"""
import argparse
import importlib.util
import json
import os
import re

import numpy as np

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(HIER)


def lade_mod(name, pfad):
    s = importlib.util.spec_from_file_location(name, pfad)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ids", nargs="+", required=True)
    ap.add_argument("--lauf", default=os.path.join(WURZEL, "ergebnisse", "setB30-v21-t06", "ergebnisse.jsonl"))
    a = ap.parse_args()
    import torch
    import transformers as tf
    torch.set_num_threads(int(os.environ.get("WSP_THREADS", 4)))
    tok = tf.AutoTokenizer.from_pretrained(os.path.join(WURZEL, "modelle", "Qwen3.5-0.8B"))
    ZU = tok.convert_tokens_to_ids("</think>")
    R = {json.loads(z)["id"]: json.loads(z) for z in open(a.lauf, encoding="utf-8")}
    G = json.load(open(os.path.join(WURZEL, "modelle", "Qwen3.5-0.8B-ergo-zig", "wsp_patch.json"), encoding="utf-8"))["neuronen"]
    cls = getattr(tf, "AutoModelForImageTextToText", None) or tf.AutoModelForCausalLM
    for name, ordner in (("eigen", "Qwen3.5-0.8B-eigen-vL"), ("V2.1", "Qwen3.5-0.8B-ergo-zig")):
        model = cls.from_pretrained(os.path.join(WURZEL, "modelle", ordner), dtype=torch.float32).eval()
        akt = {}
        for n, m in model.named_modules():
            if re.search(r"(language_model|model)\.layers\.15\.mlp\.down_proj$", n) and "visual" not in n:
                m.register_forward_hook(lambda mod, inp, out: akt.__setitem__("x", inp[0][0, :, G].sum(-1).detach().numpy()))
        for i in a.ids:
            r = R[i]
            ids = r["prompt_ids"]
            with torch.no_grad():
                out = model(input_ids=torch.tensor([ids]))
            p = float(torch.softmax(out.logits[0, -1].float(), -1)[ZU])
            g = akt["x"]
            top = np.argsort(-g)[:3]
            stellen = ", ".join(f"{int(t)}:{tok.decode([ids[t]])!r}={g[t]:+.1f}" for t in top)
            erst = r["gen_ids"].index(ZU) if ZU in r["gen_ids"] else -1
            print(f"{name:5s} {i[11:40]:30s} (V2.1 im Lauf: </think> bei Token {erst:5d}) | p(</think> als 1. Token) {p:.3e} | "
                  f"WT-Summe max {g.max():+.2f} an {stellen}", flush=True)
        del model


if __name__ == "__main__":
    main()
