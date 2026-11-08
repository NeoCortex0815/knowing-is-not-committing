"""Abschluss-Gradient für V2.1 „Zünder im Gewicht“ (07.11. ~04:45; nur Übungsdaten, CPU): ĝ = Mittel der normierten
∂ log p(`</think>`)/∂ h₁₅ an den Enden RICHTIGER Kandidaten im Denken. Speichert ĝ (Schicht-15-Ausgang = Residual nach Schicht 15).
Befund des Trockentests (2 Präfixe): ĝ einheitlich (Norm des Mittels 0,89), cos(ĝ, e⊥) ≈ 0; Anstoß κ = 5 entlang ĝ hebt
p(`</think>`) von ~10⁻¹² auf ~0,95 – e⊥ selbst bei κ = 80 nur auf ~10⁻⁴.
  python 57_abschluss_gradient.py --n 16 --aus ergebnisse/abschluss_gradient.npz
"""
import argparse
import importlib.util
import json
import os
import re

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
                                                    ("entschluss-uebung-eigen", "tag1-eigen-s1", "temp10-eigen")])
    ap.add_argument("--n", type=int, default=16)
    ap.add_argument("--max-len", type=int, default=4500)
    ap.add_argument("--aus", default=os.path.join(WURZEL, "ergebnisse", "abschluss_gradient.npz"))
    a = ap.parse_args()
    import torch
    import transformers as tf
    torch.set_num_threads(int(os.environ.get("WSP_THREADS", 2)))
    wm = lade("wm", os.path.join(HIER, "42_wahrheitsmelder.py"))
    ev = wm.lade("ev", os.path.join(WURZEL, "eval", "03_eval.py"))
    tok = tf.AutoTokenizer.from_pretrained(os.path.join(WURZEL, "modelle", "Qwen3.5-0.8B"))
    ZU = tok.convert_tokens_to_ids("</think>")
    praefixe, herkunft = [], []
    for p in a.laeufe:
        for z in open(p, encoding="utf-8"):
            if len(praefixe) >= a.n:
                break
            r = json.loads(z)
            gen = r["gen_ids"]
            stuecke = [tok.decode([t]) for t in gen]
            text = "".join(stuecke)
            zc = text.find("</think>")
            grenzen = np.cumsum([len(s) for s in stuecke])
            for (s0, e, c) in wm.kandidaten_mit_ende(text):
                if zc >= 0 and s0 > zc:
                    continue
                ti = min(int(np.searchsorted(grenzen, e - 1, side="right")), len(stuecke) - 1)
                if len(r["prompt_ids"]) + ti >= a.max_len:
                    break
                if bool(ev.korrekt(c, r["gold"])) or bool(ev.korrekt(wm.bereinige_kandidat(c), r["gold"])):
                    praefixe.append(r["prompt_ids"] + gen[:ti + 1])
                    herkunft.append(f"{os.path.basename(os.path.dirname(p))}/{r['id']}")
                    break
    print(f"{len(praefixe)} Präfixe (richtige Kandidaten-Enden im Denken)", flush=True)
    cls = getattr(tf, "AutoModelForImageTextToText", None) or tf.AutoModelForCausalLM
    pfad = os.path.join(WURZEL, "modelle", "Qwen3.5-0.8B-eigen-vL")
    try:
        model = cls.from_pretrained(pfad, dtype=torch.float32)
    except Exception:  # noqa: BLE001
        model = tf.AutoModelForCausalLM.from_pretrained(pfad, dtype=torch.float32)
    model.eval()
    for p_ in model.parameters():
        p_.requires_grad_(False)
    zustand = {"delta": None}
    for n, m in model.named_modules():
        if re.search(r"(language_model|model)\.layers\.15$", n) and "visual" not in n:
            schicht = m

    def hook(mod, inp, out):
        if zustand["delta"] is None:
            return out
        h = out[0] if isinstance(out, tuple) else out
        h = h.clone()
        h[0, -1] = h[0, -1] + zustand["delta"]
        return (h,) + tuple(out[1:]) if isinstance(out, tuple) else h
    schicht.register_forward_hook(hook)
    cfg = model.config.get_text_config() if hasattr(model.config, "get_text_config") else model.config
    grads = []
    for i, ids in enumerate(praefixe):
        delta = torch.zeros(cfg.hidden_size, requires_grad=True)
        zustand["delta"] = delta
        out = model(input_ids=torch.tensor([ids]))
        torch.log_softmax(out.logits[0, -1].float(), -1)[ZU].backward()
        g = delta.grad.detach().numpy().astype(np.float64)
        grads.append(g / (np.linalg.norm(g) + 1e-12))
        print(f"  {i + 1}/{len(praefixe)} {herkunft[i]}", flush=True)
    G = np.stack(grads)
    g_hat = G.mean(0)
    einig = float(np.linalg.norm(g_hat))
    g_hat /= np.linalg.norm(g_hat)
    paar_cos = float(np.mean([G[i] @ G[j] for i in range(len(G)) for j in range(i + 1, len(G))]))
    print(f"Einigkeit (Norm des Mittels) {einig:.3f}; mittlerer paarweiser Kosinus {paar_cos:.3f}")
    np.savez(a.aus, g_15=g_hat, einzel=G, herkunft=np.array(herkunft), einigkeit=einig)
    print(f"gespeichert: {a.aus}")


if __name__ == "__main__":
    main()
