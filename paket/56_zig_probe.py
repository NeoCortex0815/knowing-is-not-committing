"""Nachuntersuchung für V2.1 „Zünder im Gewicht“ (07.11. ~04:05; Nutzer: „kein Leerlauf … Optimierungen aufstellen“; CPU, nur
Übungsdaten). Frage: Welche Richtung und Stärke braucht ein Anstoß an Schicht 15 GENAU am Kandidaten-Ende, damit das Modell
SOFORT `</think>` schreibt (wie der Laufzeit-Zünder) – und lässt es falsche Kandidaten unberührt?
  1. Abschluss-Gradient ĝ = Mittel der normierten ∂ logit(`</think>`)/∂ h₁₅ am Kandidaten-Ende (8 richtige Präfixe).
  2. Idealisierter Anstoß h₁₅ += κ·r (r = ĝ oder e⊥) nur an der letzten Position: p(`</think>` als nächstes) je κ.
Beschreibend; kein Modell wird gespeichert.
  python 56_zig_probe.py --n 8
"""
import argparse
import importlib.util
import json
import os
import re

import numpy as np

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(HIER)
KAPPAS = [0, 5, 10, 20, 40, 80]


def lade(name, pfad):
    s = importlib.util.spec_from_file_location(name, pfad)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--laeufe", default=os.path.join(WURZEL, "ergebnisse", "entschluss-uebung-eigen", "ergebnisse.jsonl"))
    ap.add_argument("--n", type=int, default=8)
    ap.add_argument("--aus", default=os.path.join(WURZEL, "ergebnisse", "zig_probe.json"))
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
                continue
            ti = min(int(np.searchsorted(grenzen, e - 1, side="right")), len(stuecke) - 1)
            ok = bool(ev.korrekt(c, r["gold"])) or bool(ev.korrekt(wm.bereinige_kandidat(c), r["gold"]))
            art = "richtig" if ok else "falsch"
            if len(praefixe[art]) < a.n and len(r["prompt_ids"]) + ti < 5000:
                praefixe[art].append(r["prompt_ids"] + gen[:ti + 1])
                break
        if all(len(v) >= a.n for v in praefixe.values()):
            break
    print(f"Präfixe: richtig {len(praefixe['richtig'])}, falsch {len(praefixe['falsch'])}", flush=True)
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
    schicht = None
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
    d_model = model.config.get_text_config().hidden_size if hasattr(model.config, "get_text_config") else model.config.hidden_size
    # 1) Abschluss-Gradient an richtigen Kandidaten-Enden
    grads = []
    for ids in praefixe["richtig"]:
        delta = torch.zeros(d_model, requires_grad=True)
        zustand["delta"] = delta
        out = model(input_ids=torch.tensor([ids]))
        lp = torch.log_softmax(out.logits[0, -1].float(), -1)[ZU]
        lp.backward()
        g = delta.grad.detach().numpy().astype(np.float64)
        grads.append(g / (np.linalg.norm(g) + 1e-12))
    zustand["delta"] = None
    g_hat = np.mean(grads, 0)
    print(f"Abschluss-Gradient: Einigkeit der Einzelrichtungen (Norm des Mittels) {np.linalg.norm(g_hat):.3f}", flush=True)
    g_hat /= np.linalg.norm(g_hat)
    R = dict(np.load(os.path.join(WURZEL, "ergebnisse", "eigene_richtung-vL.npz")))
    u = R["u_15"].astype(np.float64)
    u /= np.linalg.norm(u)
    e = dict(np.load(os.path.join(WURZEL, "ergebnisse", "richtung-entschluss.npz")))["u_15"].astype(np.float64)
    e -= (e @ u) * u
    e /= np.linalg.norm(e)
    print(f"cos(ĝ, e⊥) = {g_hat @ e:+.3f}", flush=True)
    # Residual-Norm an der letzten Position (Maßstab für κ)
    normen = []

    def norm_hook(mod, inp, out):
        h = out[0] if isinstance(out, tuple) else out
        normen.append(float(h[0, -1].norm()))
    hh = schicht.register_forward_hook(norm_hook)
    with torch.no_grad():
        model(input_ids=torch.tensor([praefixe["richtig"][0]]))
    hh.remove()
    print(f"Residual-Norm Schicht 15 am Kandidaten-Ende ≈ {normen[0]:.1f}", flush=True)
    erg = {"cos_g_e": float(g_hat @ e), "residual_norm": normen[0], "p": {}}
    for rname, r in (("Gradient", g_hat), ("Entschluss e⊥", e)):
        for kappa in KAPPAS:
            zeile = {}
            for art, liste in praefixe.items():
                ps = []
                for ids in liste:
                    zustand["delta"] = torch.tensor(kappa * r, dtype=torch.float32)
                    with torch.no_grad():
                        out = model(input_ids=torch.tensor([ids]))
                    ps.append(float(torch.softmax(out.logits[0, -1].float(), -1)[ZU]))
                zeile[art] = ps
            zustand["delta"] = None
            erg["p"][f"{rname}|{kappa}"] = zeile
            print(f"{rname:14s} κ={kappa:3d}: p(</think>) richtig Median {np.median(zeile['richtig']):.2e} | falsch Median "
                  f"{np.median(zeile['falsch']):.2e}", flush=True)
    json.dump(erg, open(a.aus, "w", encoding="utf-8"), indent=1)


if __name__ == "__main__":
    main()
