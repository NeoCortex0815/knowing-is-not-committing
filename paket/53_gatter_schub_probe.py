"""Nachuntersuchung in der Nacht (07.11. ~02:10; Nutzer: „kein Leerlauf … Nachuntersuchungen“): Hebt der Gatter-Schub an einem
richtigen Kandidaten-Ende die Wahrscheinlichkeit für `</think>` als nächstes Token überhaupt merklich an – und senkt der
Gegenschub sie an falschen? Vergleich eigen (ohne Gatter) gegen Gatter (Schub 1) gegen Gatter3 (Schub 3) auf denselben Präfixen
aus alten Übungsläufen (eigen bei 0,6). CPU, fp32, 2 Threads (stört die laufenden GPU-Server kaum).
  python 53_gatter_schub_probe.py --n 8
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
    ap.add_argument("--laeufe", default=os.path.join(WURZEL, "ergebnisse", "entschluss-uebung-eigen", "ergebnisse.jsonl"))
    ap.add_argument("--n", type=int, default=8)
    ap.add_argument("--aus", default=os.path.join(WURZEL, "ergebnisse", "gatter_schub_probe.json"))
    a = ap.parse_args()
    import torch
    import transformers as tf
    torch.set_num_threads(int(os.environ.get("WSP_THREADS", 2)))
    wm = lade("wm", os.path.join(HIER, "42_wahrheitsmelder.py"))
    ev = wm.lade("ev", os.path.join(WURZEL, "eval", "03_eval.py"))
    tok = tf.AutoTokenizer.from_pretrained(os.path.join(WURZEL, "modelle", "Qwen3.5-0.8B"))
    ZU = tok.convert_tokens_to_ids("</think>")
    praefixe = {"richtig": [], "falsch": []}
    for z in open(a.laeufe, encoding="utf-8"):
        r = json.loads(z)
        gen = r["gen_ids"]
        stuecke = [tok.decode([t]) for t in gen]
        text = "".join(stuecke)
        zc = text.find("</think>")
        grenzen = np.cumsum([len(s) for s in stuecke])
        for (s0, e, c) in wm.kandidaten_mit_ende(text):
            if zc >= 0 and s0 > zc:
                continue  # nur Kandidaten im Denken
            ti = min(int(np.searchsorted(grenzen, e - 1, side="right")), len(stuecke) - 1)
            ok = bool(ev.korrekt(c, r["gold"])) or bool(ev.korrekt(wm.bereinige_kandidat(c), r["gold"]))
            art = "richtig" if ok else "falsch"
            if len(praefixe[art]) < a.n and len(r["prompt_ids"]) + ti < 6000:
                praefixe[art].append({"id": r["id"], "ids": r["prompt_ids"] + gen[:ti + 1]})
                break  # höchstens ein Präfix je Lauf und Art
        if all(len(v) >= a.n for v in praefixe.values()):
            break
    print(f"Präfixe: richtig {len(praefixe['richtig'])}, falsch {len(praefixe['falsch'])}", flush=True)
    modelle = {"eigen": "Qwen3.5-0.8B-eigen-vL", "Gatter": "Qwen3.5-0.8B-ergo-gatter", "Gatter3": "Qwen3.5-0.8B-ergo-gatter-s3"}
    erg = {}
    for name, ordner in modelle.items():
        cls = getattr(tf, "AutoModelForImageTextToText", None) or tf.AutoModelForCausalLM
        pfad = os.path.join(WURZEL, "modelle", ordner)
        try:
            model = cls.from_pretrained(pfad, dtype=torch.float32)
        except Exception:  # noqa: BLE001
            model = tf.AutoModelForCausalLM.from_pretrained(pfad, dtype=torch.float32)
        model.eval()
        erg[name] = {}
        for art, liste in praefixe.items():
            p_zu = []
            for p in liste:
                with torch.no_grad():
                    out = model(input_ids=torch.tensor([p["ids"]]))
                logits = out.logits[0, -1].float()
                lp = torch.log_softmax(logits, -1)
                p_zu.append(float(lp[ZU].exp()))
            erg[name][art] = p_zu
            print(f"{name:8s} {art:8s}: p(</think> als nächstes) Median {np.median(p_zu):.2e}, Mittel {np.mean(p_zu):.2e}, "
                  f"Max {np.max(p_zu):.2e}", flush=True)
        del model
    for art in ("richtig", "falsch"):
        e = np.array(erg["eigen"][art])
        for name in ("Gatter", "Gatter3"):
            g = np.array(erg[name][art])
            print(f"Verhältnis {name}/eigen an {art}en Kandidaten-Enden: Median {np.median(g / np.maximum(e, 1e-12)):.2f}×")
    json.dump(erg, open(a.aus, "w", encoding="utf-8"), indent=1)


if __name__ == "__main__":
    main()
