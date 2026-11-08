"""„Frühes Vertrauen“ – erste Prüfung (07.11. ~14:30, Nutzer: „noch was Kleines reinschieben, was uns weiterbringt“; nur
vorhandene Daten, CPU, kurz). Hypothese aus dem WT-Leck: Am letzten Token der Aufgabenstellung (vor jedem Denken) trägt das
Modell ein Signal, das anzeigt, ob es die Aufgabe lösen wird – über die Schwierigkeitsstufe hinaus.
Merkmale am letzten Prompt-Token (Schicht-15-MLP-Eingang, eigen-vL = Basis bis Schicht 15): Wahrheitssonde s_T, Kandidaten-Ende
s_C und das V2.1-Gatter-Produkt aus gatter_lern.npz. Ziel: „gelöst“ in vorhandenen Läufen (Set B: ERGORE 0,6 und Gatter 0,6;
MATH-500 1–160: ERGORE und MIT). Vergleich: AUC des Merkmals, AUC der Stufe allein, AUC innerhalb gleicher Stufen (gemittelt).
  python 69_fruehes_vertrauen.py
"""
import json
import os
import re

import numpy as np

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(HIER)
ERG = os.path.join(WURZEL, "ergebnisse")


class Stopp(Exception):
    pass


def auc(s, y):
    s, y = np.asarray(s, float), np.asarray(y, bool)
    p, n = s[y], s[~y]
    if len(p) == 0 or len(n) == 0:
        return float("nan")
    return float((np.sum(p[:, None] > n[None, :]) + 0.5 * np.sum(p[:, None] == n[None, :])) / (len(p) * len(n)))


def lade(d):
    p = os.path.join(ERG, d, "ergebnisse.jsonl")
    return {json.loads(z)["id"]: json.loads(z) for z in open(p, encoding="utf-8")} if os.path.exists(p) else {}


def main():
    import torch
    import transformers as tf
    torch.set_num_threads(int(os.environ.get("WSP_THREADS", 2)))
    Lz = np.load(os.path.join(ERG, "gatter_lern.npz"))
    mz = json.load(open(os.path.join(WURZEL, "modelle", "Qwen3.5-0.8B-ergo-zig", "wsp_patch.json"), encoding="utf-8"))
    wT, bT, wC, bC, v = Lz["wT"], float(Lz["bT"]), Lz["wC"], float(Lz["bC"]), Lz["v"]
    stufe = {}
    for p in ("daten/practice/math_train_setB60.jsonl", "daten/math500.jsonl"):
        for z in open(os.path.join(WURZEL, p), encoding="utf-8"):
            r = json.loads(z)
            lv = str(r.get("level", "?"))
            stufe[r.get("id") or r.get("unique_id")] = int(re.sub(r"\D", "", lv) or 0)
    gruppen = {
        "Set B · ERGORE 0,6": lade("setB-ergore-t06"), "Set B · Gatter 0,6 (≈ eigen)": lade("setB-gatter-t06"),
        "MATH-500 1–160 · ERGORE": {**lade("tag2-test40-kw75"), **lade("kw75-b"), **lade("kw75-c")},
        "MATH-500 1–160 · MIT": {**lade("mit-vstil-L"), **lade("mit-vstil-L-b"), **lade("mit-vstil-L-c")},
    }
    cls = getattr(tf, "AutoModelForImageTextToText", None) or tf.AutoModelForCausalLM
    model = cls.from_pretrained(os.path.join(WURZEL, "modelle", "Qwen3.5-0.8B-eigen-vL"), dtype=torch.float32).eval()
    sp = {}
    for n, m in model.named_modules():
        if "visual" in n:
            continue
        if re.search(r"(language_model|model)\.layers\.15\.mlp$", n):
            m.register_forward_pre_hook(lambda mod, inp: sp.__setitem__("x", inp[0][0, -1].detach().float().numpy()))
        if re.search(r"(language_model|model)\.layers\.15\.mlp\.down_proj$", n):
            def stopp(mod, inp):
                raise Stopp()
            m.register_forward_pre_hook(stopp)
    cache = {}
    silu = lambda z: z / (1 + np.exp(-z))  # noqa: E731
    print(f"{'Gruppe':34s} {'n':>4s} {'gelöst':>6s} | AUC Stufe | AUC s_T | AUC s_C | AUC Gatter | s_T innerhalb der Stufen")
    for name, R in gruppen.items():
        ys, lv, sT, sC, gp = [], [], [], [], []
        for i, r in R.items():
            key = tuple(r["prompt_ids"])
            if key not in cache:
                sp.clear()
                try:
                    with torch.no_grad():
                        model(input_ids=torch.tensor([r["prompt_ids"]]))
                except Stopp:
                    pass
                cache[key] = sp["x"].astype(np.float64)
            x = cache[key]
            vx = x @ v
            g = mz["kappa_g"] * (x @ wT + (bT - mz["tau_T"]) * vx)
            u = mz["kappa_u"] * (x @ wC + (bC - mz["tau_C"]) * vx)
            ys.append(bool(r["korrekt"]))
            lv.append(stufe.get(i, 0))
            sT.append(x @ wT + bT)
            sC.append(x @ wC + bC)
            gp.append(silu(g) * u)
        ys, lv, sT = np.array(ys), np.array(lv), np.array(sT)
        innen = [auc(sT[lv == s], ys[lv == s]) for s in sorted(set(lv)) if 0 < ys[lv == s].sum() < (lv == s).sum()]
        innen = [a for a in innen if a == a]
        print(f"{name:34s} {len(ys):4d} {ys.sum():6d} | {auc(-lv, ys):9.3f} | {auc(sT, ys):7.3f} | {auc(sC, ys):7.3f} | "
              f"{auc(gp, ys):10.3f} | {np.mean(innen) if innen else float('nan'):.3f} (über {len(innen)} Stufen)", flush=True)


if __name__ == "__main__":
    main()
