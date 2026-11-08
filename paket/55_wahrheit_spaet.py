"""Nachuntersuchung für V2.1 (07.11. ~03:25, nur Übungsdaten, CPU): Ist „der zuletzt genannte Kandidat ist richtig“ auch SPÄTER
(nach +8 … +64 Tokens, an Weichen bis +200) linear lesbar – wenn man die Sonde an diesen Positionen lernt (nicht am
Kandidaten-Ende)? Positionen zählen nur bis vor den nächsten Kandidaten. Etikett = Richtigkeit des zuletzt genannten Kandidaten.
Zurückgehaltene AUC je Positionsgruppe (5-fach nach Aufgabe). MLP-Eingang Schicht 15 (Ort des Gatters).
  python 55_wahrheit_spaet.py --max-laeufe 80
"""
import argparse
import importlib.util
import json
import os
import re

import numpy as np

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(HIER)
GRUPPEN = {"+8": (8, 8), "+16": (16, 16), "+32": (32, 32), "+64": (64, 64)}


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
                                                    ("entschluss-uebung-eigen", "tag2-kw75-s0", "temp10-eigen", "temp10-kw75",
                                                     "tag1-eigen-s1", "temp06-mit")])
    ap.add_argument("--max-laeufe", type=int, default=80)
    ap.add_argument("--max-len", type=int, default=7000)
    ap.add_argument("--aus", default=os.path.join(WURZEL, "ergebnisse", "wahrheit_spaet.json"))
    a = ap.parse_args()
    import torch
    import transformers as tf
    torch.set_num_threads(int(os.environ.get("WSP_THREADS", 2)))
    wm = lade("wm", os.path.join(HIER, "42_wahrheitsmelder.py"))
    ev = wm.lade("ev", os.path.join(WURZEL, "eval", "03_eval.py"))
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
    daten = {g: {"X": [], "y": [], "auf": []} for g in list(GRUPPEN) + ["weiche"]}
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
            t_start = [int(np.searchsorted(grenzen, s0, side="right")) for s0, _, _ in ks]
            t_ende = [min(int(np.searchsorted(grenzen, e - 1, side="right")), len(stuecke) - 1) for _, e, _ in ks]
            t_denk = int(np.searchsorted(grenzen, ende_denk, side="right")) if zc >= 0 else len(gen)
            letzt = min(len(gen) - 1, t_denk, max(t_ende) + 200)
            if len(r["prompt_ids"]) + letzt > a.max_len:
                continue
            sp.clear()
            try:
                with torch.no_grad():
                    model(input_ids=torch.tensor([r["prompt_ids"] + gen[:letzt + 1]]))
            except Stopp:
                pass
            X = sp["x"][len(r["prompt_ids"]):]
            for i, ((s0, e, c), te) in enumerate(zip(ks, t_ende)):
                ok = bool(ev.korrekt(c, r["gold"])) or bool(ev.korrekt(wm.bereinige_kandidat(c), r["gold"]))
                grenze = min(t_start[i + 1] if i + 1 < len(ks) else 10 ** 9, t_denk, len(X))
                for g, (v, _) in GRUPPEN.items():
                    if te + v < grenze:
                        daten[g]["X"].append(X[te + v]); daten[g]["y"].append(ok); daten[g]["auf"].append(r["id"])
                n_w = 0
                for t in range(te + 4, min(grenze, te + 200)):
                    if re.search(r"(\n\n|[.!?]\s*$)", stuecke[t]):
                        daten["weiche"]["X"].append(X[t]); daten["weiche"]["y"].append(ok); daten["weiche"]["auf"].append(r["id"])
                        n_w += 1
                        if n_w >= 3:
                            break
            n_l += 1
            print(f"{os.path.basename(os.path.dirname(p))} {r['id']}: {len(ks)} Kandidaten", flush=True)
    erg = {}
    for g, d in daten.items():
        if len(set(d["y"])) < 2 or len(d["y"]) < 40:
            continue
        X = np.stack(d["X"]).astype(np.float64)
        y = np.array(d["y"], bool)
        auf = np.array(d["auf"])
        eind = sorted(set(auf))
        rng = np.random.default_rng(0)
        rng.shuffle(eind)
        f = np.array([{t: i % 5 for i, t in enumerate(eind)}[t] for t in auf])
        oof = np.zeros(len(y))
        for k in range(5):
            tr = f != k
            if not (f == k).any() or len(set(y[tr])) < 2:
                continue
            mu, sd = X[tr].mean(0), X[tr].std(0) + 1e-6
            w, b = wm.logreg((X[tr] - mu) / sd, y[tr].astype(float), 50.0)
            oof[f == k] = ((X[f == k] - mu) / sd) @ w + b
        auc = wm.auc(oof, y)
        erg[g] = {"auc": auc, "n": int(len(y)), "richtig": int(y.sum())}
        print(f"Gruppe {g:>6s}: zurückgehaltene AUC {auc:.3f} ({len(y)} Positionen, {y.sum()} nach richtigem Kandidaten)")
    json.dump(erg, open(a.aus, "w", encoding="utf-8"), indent=1)


if __name__ == "__main__":
    main()
