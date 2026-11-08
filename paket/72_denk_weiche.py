"""Denk-Weiche – Auswertung (Nutzer-Go 07.11. kurz nach 15:00; Prüfprotokoll nach Argon, Lesart vorab in ANNAHMEN).
Frage: Sagt das Signal am Ende der Aufgabenstellung (vor jedem Denken) voraus, ob das Modell die Aufgabe OHNE Denken löst –
über Schwierigkeitsstufe, Prompt-Länge und Datensatz hinaus?
Daten: eigen ohne Denken (eval/03b_eval_ohne_denken.py) auf Set B (60) und MATH-500 1–160.
Merkmale am letzten Token des Denk-Prompts (`…<think>\\n`), Schicht-15-MLP-Eingang (eigen-vL, fp32, CPU; bis Schicht 15 für alle
Modelle gleich): s_T (Wahrheitssonde) und s_C (Kandidaten-Ende) aus gatter_lern.npz.
Haupttest (vorab): logistische Regression Y_ohne ~ Stufe (Dummies) + log(Prompt-Tokens) + Datensatz (M0) gegen M0 + s_T + s_C (M1);
Likelihood-Ratio-Test mit 2 Freiheitsgraden (p = exp(−LR/2)); WIDERLEGT bei p > 0,05. Dazu 5-fach-Kreuzvalidierung: AUC M0 gegen M1.
Beschreibend: ohne gegen mit Denken je Aufgabe (McNemar); Weiche = oberstes Quintil der zurückgehaltenen M1-Vorhersage ohne Denken,
sonst Denken – Treffer und Tokens gegen „immer Denken“ (Set B: eigen; 1–160: ERGORE und MIT).
  python 72_denk_weiche.py [--ohne setB60-ohne-eigen-t06 m500-001-160-ohne-eigen-t06]
"""
import argparse
import json
import os
import re
from math import comb, exp

import numpy as np

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(HIER)
ERG = os.path.join(WURZEL, "ergebnisse")
DENKEN = {
    "Set B": {"eigen": ["setB30-eigen-t06", "minipc-b2-eigen-t06"]},
    "MATH-500 1–160": {"ERGORE": ["tag2-test40-kw75", "kw75-b", "kw75-c"], "MIT": ["mit-vstil-L", "mit-vstil-L-b", "mit-vstil-L-c"]},
}


class Stopp(Exception):
    pass


def lade(dirs):
    R = {}
    for d in dirs:
        p = os.path.join(ERG, d, "ergebnisse.jsonl")
        if os.path.exists(p):
            R.update({json.loads(z)["id"]: json.loads(z) for z in open(p, encoding="utf-8")})
    return R


def auc(s, y):
    s, y = np.asarray(s, float), np.asarray(y, bool)
    p, n = s[y], s[~y]
    if len(p) == 0 or len(n) == 0:
        return float("nan")
    return float((np.sum(p[:, None] > n[None, :]) + 0.5 * np.sum(p[:, None] == n[None, :])) / (len(p) * len(n)))


def logreg(X, y, lam=1e-3, it=100):
    """IRLS mit kleinem Ridge (ohne Achsenabschnitt-Strafe); X ohne Einsenspalte. Rückgabe: Koeffizienten, Log-Likelihood."""
    Xa = np.hstack([np.ones((len(X), 1)), X])
    w = np.zeros(Xa.shape[1])
    P = lam * np.eye(Xa.shape[1])
    P[0, 0] = 0.0
    for _ in range(it):
        z = Xa @ w
        p = 1 / (1 + np.exp(-z))
        W = p * (1 - p) + 1e-9
        H = Xa.T @ (Xa * W[:, None]) + P
        g = Xa.T @ (y - p) - P @ w
        d = np.linalg.solve(H, g)
        w += d
        if np.max(np.abs(d)) < 1e-8:
            break
    p = np.clip(1 / (1 + np.exp(-(Xa @ w))), 1e-12, 1 - 1e-12)
    return w, float(np.sum(y * np.log(p) + (1 - y) * np.log(1 - p)))


def vorhersage(w, X):
    return 1 / (1 + np.exp(-(np.hstack([np.ones((len(X), 1)), X]) @ w)))


def mcnemar(a, b):
    n = a + b
    return min(1.0, 2 * sum(comb(n, x) for x in range(0, min(a, b) + 1)) / 2 ** n) if n else 1.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ohne", nargs="+", default=["setB60-ohne-eigen-t06", "m500-001-160-ohne-eigen-t06"])
    a = ap.parse_args()
    import importlib.util
    s_ = importlib.util.spec_from_file_location("ev", os.path.join(WURZEL, "eval", "03_eval.py"))
    ev = importlib.util.module_from_spec(s_)
    s_.loader.exec_module(ev)
    import torch
    import transformers as tf
    torch.set_num_threads(int(os.environ.get("WSP_THREADS", 2)))
    tok = tf.AutoTokenizer.from_pretrained(os.path.join(WURZEL, "modelle", "Qwen3.5-0.8B"))
    Lz = np.load(os.path.join(ERG, "gatter_lern.npz"))
    wT, bT, wC, bC = Lz["wT"], float(Lz["bT"]), Lz["wC"], float(Lz["bC"])
    aufgaben = {}
    for p, ds in (("daten/practice/math_train_setB60.jsonl", "Set B"), ("daten/math500.jsonl", "MATH-500 1–160")):
        zeilen = [json.loads(z) for z in open(os.path.join(WURZEL, p), encoding="utf-8")]
        if ds.startswith("MATH-500"):
            zeilen = zeilen[:160]
        for r in zeilen:
            aufgaben[r.get("unique_id") or r.get("id")] = {"ds": ds, "problem": r["problem"],
                                                           "stufe": int(re.sub(r"\D", "", str(r.get("level", "0"))) or 0)}
    O = lade(a.ohne)
    ids = [i for i in aufgaben if i in O]
    print(f"ohne Denken: {len(ids)} von {len(aufgaben)} Aufgaben vorhanden "
          f"({sum(aufgaben[i]['ds'] == 'Set B' for i in ids)} Set B, {sum(aufgaben[i]['ds'] != 'Set B' for i in ids)} MATH-500)")
    if len(ids) < len(aufgaben):
        raise SystemExit("unvollständig – keine Auswertung (Vorab-Regel)")
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
    sT, sC, L, D, S, Y, T = [], [], [], [], [], [], []
    for i in ids:
        ptext = ev.PREFIX + aufgaben[i]["problem"] + ev.SUFFIX          # Denk-Prompt (endet mit <think>\n)
        pid = tok(ptext, add_special_tokens=False)["input_ids"]
        sp.clear()
        try:
            with torch.no_grad():
                model(input_ids=torch.tensor([pid]))
        except Stopp:
            pass
        x = sp["x"].astype(np.float64)
        sT.append(x @ wT + bT)
        sC.append(x @ wC + bC)
        L.append(np.log(len(pid)))
        D.append(aufgaben[i]["stufe"])
        S.append(aufgaben[i]["ds"] == "Set B")
        Y.append(bool(O[i]["korrekt"]))
        T.append(int(O[i]["tokens"]))
    sT, sC, L, D, S, Y, T = map(np.array, (sT, sC, L, D, S, Y, T))
    stufen = sorted(set(D))
    dummies = np.stack([(D == s).astype(float) for s in stufen[1:]], 1) if len(stufen) > 1 else np.zeros((len(D), 0))
    z = lambda v: (v - v.mean()) / (v.std() + 1e-12)  # noqa: E731
    X0 = np.hstack([dummies, z(L)[:, None], S.astype(float)[:, None]])
    X1 = np.hstack([X0, z(sT)[:, None], z(sC)[:, None]])
    w0, ll0 = logreg(X0, Y.astype(float))
    w1, ll1 = logreg(X1, Y.astype(float))
    lr = max(0.0, 2 * (ll1 - ll0))
    p_lr = exp(-lr / 2)
    print(f"\nOhne Denken gelöst: {Y.sum()}/{len(Y)} (Set B {Y[S].sum()}/{S.sum()}, MATH-500 1–160 {Y[~S].sum()}/{(~S).sum()}); "
          f"Ø Tokens {T.mean():.0f}")
    print(f"HAUPTTEST Likelihood-Ratio M1 (+ s_T, s_C) gegen M0 (Stufe, log Länge, Datensatz): LR = {lr:.2f}, df 2, p = {p_lr:.4g} → "
          f"{'WIDERLEGT (p > 0,05)' if p_lr > 0.05 else 'BESTANDEN (p ≤ 0,05)'}")
    print(f"  Koeffizienten (standardisiert) s_T {w1[-2]:+.3f}, s_C {w1[-1]:+.3f}")
    rng = np.random.default_rng(0)
    falte = rng.permutation(len(Y)) % 5
    oof0, oof1 = np.zeros(len(Y)), np.zeros(len(Y))
    for k in range(5):
        tr, te = falte != k, falte == k
        oof0[te] = vorhersage(logreg(X0[tr], Y[tr].astype(float))[0], X0[te])
        oof1[te] = vorhersage(logreg(X1[tr], Y[tr].astype(float))[0], X1[te])
    print(f"  5-fach-CV-AUC: M0 {auc(oof0, Y):.3f}, M1 {auc(oof1, Y):.3f} | einzeln: −s_T {auc(-sT, Y):.3f}, s_C {auc(sC, Y):.3f}, "
          f"−Stufe {auc(-D, Y):.3f}")
    erg = {"n": int(len(Y)), "geloest_ohne": int(Y.sum()), "lr": lr, "p_lr": p_lr, "widerlegt": bool(p_lr > 0.05),
           "auc_cv_m0": auc(oof0, Y), "auc_cv_m1": auc(oof1, Y), "koef_sT": float(w1[-2]), "koef_sC": float(w1[-1]),
           "vergleich": {}}
    # Beschreibend: ohne gegen mit Denken; Weiche (oberstes Quintil der OOF-M1-Vorhersage → ohne Denken)
    idx = {i: k for k, i in enumerate(ids)}
    for ds, modelle in DENKEN.items():
        sel = [i for i in ids if aufgaben[i]["ds"] == ds]
        q = np.quantile(oof1[[idx[i] for i in sel]], 0.8)
        for name, dirs in modelle.items():
            R = lade(dirs)
            gem = [i for i in sel if i in R]
            if not gem:
                print(f"  {ds} · Denken {name}: keine Läufe")
                continue
            ja_o = sum(Y[idx[i]] and not R[i]["korrekt"] for i in gem)
            ja_d = sum(R[i]["korrekt"] and not Y[idx[i]] for i in gem)
            weiche = [i for i in gem if oof1[idx[i]] >= q]
            treffer_w = sum((Y[idx[i]] if i in weiche else bool(R[i]["korrekt"])) for i in gem)
            tok_w = sum((T[idx[i]] if i in weiche else R[i]["tokens"]) for i in gem)
            tok_d = sum(R[i]["tokens"] for i in gem)
            r_d = sum(bool(R[i]["korrekt"]) for i in gem)
            print(f"  {ds} · ohne Denken (eigen) {sum(Y[idx[i]] for i in gem)} gegen Denken {name} {r_d} von {len(gem)} | "
                  f"nur ohne {ja_o}, nur mit {ja_d}, McNemar p = {mcnemar(ja_o, ja_d):.3f} | Weiche ({len(weiche)} ohne Denken): "
                  f"{treffer_w} Treffer ({treffer_w - r_d:+d}), Tokens {100 * (tok_w / tok_d - 1):+.0f} %")
            erg["vergleich"][f"{ds} · {name}"] = {"n": len(gem), "ohne": int(sum(Y[idx[i]] for i in gem)), "mit": r_d,
                                                 "nur_ohne": int(ja_o), "nur_mit": int(ja_d), "p": mcnemar(ja_o, ja_d),
                                                 "weiche_n": len(weiche), "weiche_treffer": int(treffer_w),
                                                 "weiche_tokens_rel": tok_w / tok_d - 1}
    json.dump(erg, open(os.path.join(ERG, "denk_weiche.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print("gespeichert: ergebnisse/denk_weiche.json")


if __name__ == "__main__":
    main()
