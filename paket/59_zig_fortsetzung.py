"""Qualitative Fortsetzungs-Probe V2.1 (07.11. ~05:40; CPU; nur Übungsdaten): Was schreibt V2.1 NACH einem richtigen Kandidaten-
Ende? Erwartung: sofort `</think>`, danach im Antwortteil die Endantwort mit \\boxed{…} (richtig). Vergleich eigen. Kurze
Generierung (≤ 160 Tokens, Temperatur 0,6 wie im MIT-Protokoll, fester Seed) auf 4 Präfixen aus anderen Läufen als für ĝ.
  python 59_zig_fortsetzung.py --n 4
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
    ap.add_argument("--laeufe", nargs="+", default=[os.path.join(WURZEL, "ergebnisse", d, "ergebnisse.jsonl") for d in
                                                    ("tag2-kw75-s0", "temp06-mit")])
    ap.add_argument("--n", type=int, default=4)
    ap.add_argument("--neu", type=int, default=160)
    ap.add_argument("--aus", default=os.path.join(WURZEL, "ergebnisse", "zig_fortsetzung.json"))
    ap.add_argument("--modelle", nargs="+", default=["eigen=Qwen3.5-0.8B-eigen-vL", "V2.1=Qwen3.5-0.8B-ergo-zig"],
                    help="name=ordner unter modelle/ (07.11.: für V2.2 ergore=…-kopplung-kw75 V2.2=…-ergo-v22)")
    a = ap.parse_args()
    import torch
    import transformers as tf
    torch.set_num_threads(int(os.environ.get("WSP_THREADS", 2)))
    wm = lade("wm", os.path.join(HIER, "42_wahrheitsmelder.py"))
    ev = wm.lade("ev", os.path.join(WURZEL, "eval", "03_eval.py"))
    tok = tf.AutoTokenizer.from_pretrained(os.path.join(WURZEL, "modelle", "Qwen3.5-0.8B"))
    P = []
    for p in a.laeufe:
        for z in open(p, encoding="utf-8"):
            if len(P) >= a.n:
                break
            r = json.loads(z)
            gen = r["gen_ids"]
            stuecke = [tok.decode([t]) for t in gen]
            text = "".join(stuecke)
            zc = text.find("</think>")
            grenzen = np.cumsum([len(s) for s in stuecke])
            for (s0, e, c) in wm.kandidaten_mit_ende(text):
                if zc >= 0 and s0 > zc:
                    break
                ti = min(int(np.searchsorted(grenzen, e - 1, side="right")), len(stuecke) - 1)
                if len(r["prompt_ids"]) + ti > 4000:
                    break
                if bool(ev.korrekt(c, r["gold"])) or bool(ev.korrekt(wm.bereinige_kandidat(c), r["gold"])):
                    P.append({"id": r["id"], "gold": r["gold"], "ids": r["prompt_ids"] + gen[:ti + 1], "kand": c})
                    break
    erg = {}
    for name, ordner in (s.split("=", 1) for s in a.modelle):
        cls = getattr(tf, "AutoModelForImageTextToText", None) or tf.AutoModelForCausalLM
        pfad = os.path.join(WURZEL, "modelle", ordner)
        try:
            model = cls.from_pretrained(pfad, dtype=torch.float32)
        except Exception:  # noqa: BLE001
            model = tf.AutoModelForCausalLM.from_pretrained(pfad, dtype=torch.float32)
        model.eval()
        erg[name] = []
        for p in P:
            torch.manual_seed(0)
            with torch.no_grad():
                out = model.generate(input_ids=torch.tensor([p["ids"]]), max_new_tokens=a.neu, do_sample=True, temperature=0.6,
                                     top_p=0.95, top_k=20)
            neu = tok.decode(out[0][len(p["ids"]):])
            zu = neu.find("</think>")
            pred = ev.letztes_boxed(neu[zu:]) if zu >= 0 else None
            ok = bool(pred) and bool(ev.korrekt(pred, p["gold"]))
            erg[name].append({"id": p["id"], "zu_zeichen": zu, "endantwort": pred, "richtig": ok, "text": neu[:400]})
            print(f"{name:6s} {p['id']}: `</think>` bei Zeichen {zu} | Endantwort {pred!r} (gold {p['gold']!r}) richtig {ok}", flush=True)
            print("       " + repr(neu[:160]), flush=True)
        del model
    json.dump(erg, open(a.aus, "w", encoding="utf-8"), indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
