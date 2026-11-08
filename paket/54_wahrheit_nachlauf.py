"""Nachuntersuchung für V2.1 (07.11. ~02:55, nur Übungsdaten, CPU): Hält das Wahrheitssignal an Positionen NACH dem
Kandidaten-Ende – dort, wo das Modell tatsächlich entscheidet, ob es schließt (nächstes Satzende / Absatz)?
Misst mit der Wahrheitssonde s_T aus gatter_lern.npz (MLP-Eingang Schicht 15) an Versatz +0, +1, +2, +4, +8, +16, +32 Tokens
nach jedem Kandidaten-Ende im Denken und am nächsten Absatz/Satzende danach: AUC richtig gegen falsch je Versatz.
Dazu (nur Text): Abstand vom letzten Kandidaten-Ende bis `</think>` bei ordentlich geschlossenen Läufen.
  python 54_wahrheit_nachlauf.py --max-laeufe 80
"""
import argparse
import importlib.util
import json
import os
import re

import numpy as np

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(HIER)
VERSATZ = [0, 1, 2, 4, 8, 16, 32]


def lade(name, pfad):
    s = importlib.util.spec_from_file_location(name, pfad)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


class Stopp(Exception):
    pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--laeufe", nargs="+", default=[os.path.join(WURZEL, "ergebnisse", d, "ergebnisse.jsonl") for d in
                                                    ("entschluss-uebung-eigen", "tag2-kw75-s0", "temp10-eigen", "temp10-kw75")])
    ap.add_argument("--max-laeufe", type=int, default=80)
    ap.add_argument("--max-len", type=int, default=7000)
    ap.add_argument("--aus", default=os.path.join(WURZEL, "ergebnisse", "wahrheit_nachlauf.json"))
    a = ap.parse_args()
    import torch
    import transformers as tf
    torch.set_num_threads(int(os.environ.get("WSP_THREADS", 2)))
    wm = lade("wm", os.path.join(HIER, "42_wahrheitsmelder.py"))
    ev = wm.lade("ev", os.path.join(WURZEL, "eval", "03_eval.py"))
    Lz = np.load(os.path.join(WURZEL, "ergebnisse", "gatter_lern.npz"))
    wT, bT = Lz["wT"].astype(np.float64), float(Lz["bT"])
    tok = tf.AutoTokenizer.from_pretrained(os.path.join(WURZEL, "modelle", "Qwen3.5-0.8B"))
    cls = getattr(tf, "AutoModelForImageTextToText", None) or tf.AutoModelForCausalLM
    pfad = os.path.join(WURZEL, "modelle", "Qwen3.5-0.8B-eigen-vL")
    try:
        model = cls.from_pretrained(pfad, dtype=torch.float32)
    except Exception:  # noqa: BLE001
        model = tf.AutoModelForCausalLM.from_pretrained(pfad, dtype=torch.float32)
    model.eval()
    sp = {}

    def hook(mod, inp):
        sp["x"] = inp[0][0].detach().float().numpy()
        raise Stopp()
    for n, m in model.named_modules():
        if re.search(r"(language_model|model)\.layers\.15\.mlp$", n) and "visual" not in n:
            m.register_forward_pre_hook(hook)
    werte = {v: {"richtig": [], "falsch": []} for v in VERSATZ + ["weiche"]}
    abstaende = []
    n_l = 0
    for p in a.laeufe:
        for z in open(p, encoding="utf-8"):
            if n_l >= a.max_laeufe:
                break
            r = json.loads(z)
            gen = r["gen_ids"]
            stuecke = [tok.decode([t]) for t in gen]
            text = "".join(stuecke)
            zc = text.find("</think>")
            ende_denk = zc if zc >= 0 else len(text)
            grenzen = np.cumsum([len(s) for s in stuecke])
            ks = [(s0, e, c) for (s0, e, c) in wm.kandidaten_mit_ende(text) if s0 < ende_denk]
            if not ks:
                continue
            t_ende = [min(int(np.searchsorted(grenzen, e - 1, side="right")), len(stuecke) - 1) for _, e, _ in ks]
            if zc >= 0 and r["ende"] == "eos":
                zu_t = int(np.searchsorted(grenzen, zc, side="right"))
                abstaende.append(zu_t - t_ende[-1])
            letzt = min(len(gen) - 1, max(t_ende) + 40)
            if len(r["prompt_ids"]) + letzt > a.max_len:
                continue
            sp.clear()
            try:
                with torch.no_grad():
                    model(input_ids=torch.tensor([r["prompt_ids"] + gen[:letzt + 1]]))
            except Stopp:
                pass
            X = sp["x"][len(r["prompt_ids"]):]
            s = X.astype(np.float64) @ wT + bT
            for (s0, e, c), ti in zip(ks, t_ende):
                ok = bool(ev.korrekt(c, r["gold"])) or bool(ev.korrekt(wm.bereinige_kandidat(c), r["gold"]))
                art = "richtig" if ok else "falsch"
                for v in VERSATZ:
                    if ti + v < len(s):
                        werte[v][art].append(float(s[ti + v]))
                # nächste Weiche: erstes Token mit Absatz/Satzende nach dem Kandidaten
                for t in range(ti + 1, min(len(s), ti + 40)):
                    if re.search(r"(\n\n|[.!?]\s*$)", stuecke[t]):
                        werte["weiche"][art].append(float(s[t]))
                        break
            n_l += 1
            print(f"{os.path.basename(os.path.dirname(p))} {r['id']}: {len(ks)} Kandidaten", flush=True)
    erg = {}
    for v, d in werte.items():
        if d["richtig"] and d["falsch"]:
            auc = wm.auc(np.array(d["richtig"] + d["falsch"]), np.array([True] * len(d["richtig"]) + [False] * len(d["falsch"])))
            erg[str(v)] = {"auc": auc, "n_richtig": len(d["richtig"]), "n_falsch": len(d["falsch"]),
                           "median_richtig": float(np.median(d["richtig"])), "median_falsch": float(np.median(d["falsch"]))}
            print(f"Versatz {str(v):>6s}: AUC {auc:.3f} | richtig {len(d['richtig'])} (Median {np.median(d['richtig']):+.2f}) | "
                  f"falsch {len(d['falsch'])} (Median {np.median(d['falsch']):+.2f})")
    if abstaende:
        print(f"Abstand letztes Kandidaten-Ende → `</think>` (ordentlich geschlossen, {len(abstaende)} Läufe): Median "
              f"{np.median(abstaende):.0f}, 25 %–75 %: {np.quantile(abstaende, 0.25):.0f}–{np.quantile(abstaende, 0.75):.0f} Tokens")
        erg["abstand"] = {"median": float(np.median(abstaende)), "q25": float(np.quantile(abstaende, 0.25)),
                          "q75": float(np.quantile(abstaende, 0.75)), "n": len(abstaende)}
    json.dump(erg, open(a.aus, "w", encoding="utf-8"), indent=1)


if __name__ == "__main__":
    main()
