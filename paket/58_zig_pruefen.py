"""Offline-Prüfung V2.1 „Zünder im Gewicht“ (07.11. ~05:10; CPU; nur Übungsdaten, andere Läufe als für ĝ):
p(`</think>` als nächstes Token) an richtigen und falschen Kandidaten-Enden im Denken sowie an gewöhnlichen Denk-Tokens,
für eigen (ohne Gatter) und das gebaute V2.1-Modell. Erwartung: richtig → hoch (wenn Wahrheit über der Schwelle), falsch und
gewöhnlich → unverändert winzig.
  python 58_zig_pruefen.py --modelle eigen=modelle/Qwen3.5-0.8B-eigen-vL zig=modelle/Qwen3.5-0.8B-ergo-zig --n 8
"""
import argparse
import importlib.util
import json
import os

import numpy as np

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(HIER)


def lade(name, pfad):
    s = importlib.util.spec_from_file_location(name, pfad)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--modelle", nargs="+", required=True, help="name=ordner")
    ap.add_argument("--laeufe", nargs="+", default=[os.path.join(WURZEL, "ergebnisse", d, "ergebnisse.jsonl") for d in
                                                    ("tag2-kw75-s0", "temp10-kw75", "temp06-mit")])
    ap.add_argument("--n", type=int, default=8)
    ap.add_argument("--max-len", type=int, default=4500)
    ap.add_argument("--aus", default=os.path.join(WURZEL, "ergebnisse", "zig_pruefung.json"))
    a = ap.parse_args()
    import torch
    import transformers as tf
    torch.set_num_threads(int(os.environ.get("WSP_THREADS", 2)))
    wm = lade("wm", os.path.join(HIER, "42_wahrheitsmelder.py"))
    ev = wm.lade("ev", os.path.join(WURZEL, "eval", "03_eval.py"))
    tok = tf.AutoTokenizer.from_pretrained(os.path.join(WURZEL, "modelle", "Qwen3.5-0.8B"))
    ZU = tok.convert_tokens_to_ids("</think>")
    rng = np.random.default_rng(1)
    P = {"richtig": [], "falsch": [], "gewoehnlich": []}
    for p in a.laeufe:
        for z in open(p, encoding="utf-8"):
            if all(len(v) >= a.n for v in P.values()):
                break
            r = json.loads(z)
            gen = r["gen_ids"]
            stuecke = [tok.decode([t]) for t in gen]
            text = "".join(stuecke)
            zc = text.find("</think>")
            grenzen = np.cumsum([len(s) for s in stuecke])
            ks = [(s0, e, c) for (s0, e, c) in wm.kandidaten_mit_ende(text) if zc < 0 or s0 < zc]
            gesehen = set()
            for (s0, e, c) in ks:
                ti = min(int(np.searchsorted(grenzen, e - 1, side="right")), len(stuecke) - 1)
                if len(r["prompt_ids"]) + ti >= a.max_len:
                    break
                ok = bool(ev.korrekt(c, r["gold"])) or bool(ev.korrekt(wm.bereinige_kandidat(c), r["gold"]))
                art = "richtig" if ok else "falsch"
                if art not in gesehen and len(P[art]) < a.n:
                    P[art].append(r["prompt_ids"] + gen[:ti + 1])
                    gesehen.add(art)
            if len(P["gewoehnlich"]) < a.n and len(gen) > 300:
                t = int(rng.integers(100, min(len(gen) - 1, a.max_len - len(r["prompt_ids"]) - 1)))
                if all(abs(t - min(int(np.searchsorted(grenzen, e - 1, side="right")), len(stuecke) - 1)) > 5 for _, e, _ in ks):
                    P["gewoehnlich"].append(r["prompt_ids"] + gen[:t + 1])
    print({k: len(v) for k, v in P.items()}, flush=True)
    erg = {}
    for spec in a.modelle:
        name, ordner = spec.split("=", 1)
        pfad = ordner if os.path.isabs(ordner) else os.path.join(WURZEL, ordner)
        cls = getattr(tf, "AutoModelForImageTextToText", None) or tf.AutoModelForCausalLM
        try:
            model = cls.from_pretrained(pfad, dtype=torch.float32)
        except Exception:  # noqa: BLE001
            model = tf.AutoModelForCausalLM.from_pretrained(pfad, dtype=torch.float32)
        model.eval()
        erg[name] = {}
        for art, liste in P.items():
            ps = []
            for ids in liste:
                with torch.no_grad():
                    out = model(input_ids=torch.tensor([ids]))
                ps.append(float(torch.softmax(out.logits[0, -1].float(), -1)[ZU]))
            erg[name][art] = ps
            print(f"{name:8s} {art:12s}: p(</think>) Median {np.median(ps):.2e} | Anteil > 0,5: {100 * float(np.mean(np.array(ps) > 0.5)):.0f} % "
                  f"| Werte {', '.join(f'{x:.1e}' for x in ps)}", flush=True)
        del model
    json.dump(erg, open(a.aus, "w", encoding="utf-8"), indent=1)


if __name__ == "__main__":
    main()
