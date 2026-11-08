"""Fuchsbau-Beweis (06.11. ~05:20; Nutzer: „Fuchsbau ergründen und beweisen“): Gibt die Kopplung GENAU DANN ab, wenn ihr
Melder hoch steht?

Für jeden Lauf mit Lösung im Denken (τy) wird an Schicht 15 der Melder-Pegel s(t) = kᵀ a_S(t) berechnet (roh und
geschärft), mit dem Modell, das den Lauf erzeugt hat (CPU, Vorwärtslauf bricht nach Schicht 15 ab). An jeder Weiche nach τy
(Satzende, wie 34_weichen.py) wird der Pegel (Mittel der letzten 4 Tokens bis zur Weiche) mit dem Ausgang verglichen:
Ende / Warte / Weiter. Kennzahl: AUC = P(Pegel an Ende-Weiche > Pegel an anderer Weiche); 0,5 = kein Zusammenhang.
Erwartung, falls der Reflex wie gedacht arbeitet: AUC mit Kopplung deutlich über der ohne Kopplung.
Dazu der Pegel-Verlauf über die Weichen-Nummer (wächst der Auslöser mit der Zeit?).
  python 39_melder_weichen.py --laeufe eigen=ergebnisse/entschluss-uebung-eigen/ergebnisse.jsonl@modelle/Qwen3.5-0.8B-eigen-vL \
      b5=ergebnisse/kopplung-b5-12k-leicht20/ergebnisse.jsonl@modelle/Qwen3.5-0.8B-kopplung-b5 --nur-ids-aus ergebnisse/kopplung-b5-12k-leicht20/ergebnisse.jsonl
"""
import argparse
import importlib.util
import json
import os
import sys
from math import comb

import numpy as np

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
import wsp_lib as W  # noqa: E402

L = 15
BINS = [(0, 20), (20, 100), (100, 300), (300, 600), (600, 10 ** 9)]


def lade(name, datei):
    s = importlib.util.spec_from_file_location(name, os.path.join(HIER, datei))
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


class Stopp(Exception):
    pass


def auc(pos, neg):
    if not pos or not neg:
        return None
    pos, neg = np.asarray(pos), np.asarray(neg)
    gr = (pos[:, None] > neg[None, :]).mean() + 0.5 * (pos[:, None] == neg[None, :]).mean()
    return float(gr)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--laeufe", nargs="+", required=True, help="name=ergebnisse.jsonl@modellordner")
    ap.add_argument("--richtung", default="ergebnisse/eigene_richtung-vL.npz")
    ap.add_argument("--basis", default="modelle/Qwen3.5-0.8B")
    ap.add_argument("--geschaerft", default="ergebnisse/melder_geschaerft.npz")
    ap.add_argument("--nur-ids-aus", default="")
    ap.add_argument("--max-len", type=int, default=12288)
    ap.add_argument("--aus", default="ergebnisse/melder_weichen.json")
    a = ap.parse_args()
    import torch
    import transformers as tf
    # schonend neben den llama-servern (06.11. 05:15: 8 Threads bremsten das Sampling der Server auf ein Drittel)
    torch.set_num_threads(int(os.environ.get("WSP_THREADS", max(1, (os.cpu_count() or 2) // 2))))
    am = lade("am", "22_angstmarker.py")
    wm = lade("wm", "34_weichen.py")
    R = dict(np.load(a.richtung))
    S = np.asarray(R[f"spalten_{L}"], dtype=np.int64)
    _, bits = W.tensor_lesen(a.basis, f"model.language_model.layers.{L}.mlp.down_proj.weight", W.tensor_index(a.basis))
    W0 = np.asarray(W.bf16_to_f32(np.asarray(bits)), dtype=np.float64)
    u = R[f"u_{L}"].astype(np.float64)
    u /= np.linalg.norm(u)
    K = {"roh": torch.tensor((u @ W0)[S], dtype=torch.float32),
         "lda": torch.tensor(np.load(a.geschaerft)[f"k_{L}"][S], dtype=torch.float32)}
    St = torch.tensor(S)
    nur = {json.loads(z)["id"] for z in open(a.nur_ids_aus, encoding="utf-8")} if a.nur_ids_aus else None
    tok = tf.AutoTokenizer.from_pretrained(a.basis)
    zu = tok.convert_tokens_to_ids("</think>")
    erg = {}
    for spec in a.laeufe:
        name, rest = spec.split("=", 1)
        pfad, modell = rest.split("@", 1)
        cls = getattr(tf, "AutoModelForImageTextToText", None) or tf.AutoModelForCausalLM
        try:
            model = cls.from_pretrained(modell, dtype=torch.float32)
        except Exception:  # noqa: BLE001
            model = tf.AutoModelForCausalLM.from_pretrained(modell, dtype=torch.float32)
        model.eval()
        speicher = {}

        def hook(mod, inp):
            speicher["a"] = inp[0][0][:, St].detach().float()
            raise Stopp()
        for n, m in model.named_modules():
            if n.endswith(f"layers.{L}.mlp.down_proj") and "visual" not in n:
                m.register_forward_pre_hook(hook)
        weichen = {"roh": {"Ende": [], "Warte": [], "Weiter": []}, "lda": {"Ende": [], "Warte": [], "Weiter": []}}
        je_lauf = {"roh": [], "lda": []}   # (Pegel an der Ende-Weiche, Median der übrigen Weichen) je abgebendem Lauf
        verlauf = {"roh": [[] for _ in BINS], "lda": [[] for _ in BINS]}
        n_laeufe = 0
        for z in open(pfad, encoding="utf-8"):
            r = json.loads(z)
            if nur is not None and r["id"] not in nur:
                continue
            gen = r["gen_ids"][:a.max_len]
            ende_i = gen.index(zu) if zu in gen else len(gen)
            stuecke = [tok.decode([t]) for t in gen[:ende_i]]
            denk = "".join(stuecke)
            tchar = am.tau(denk, r.get("gold"))
            if tchar is None:
                continue
            grenzen = np.cumsum([len(s) for s in stuecke])
            try:
                with torch.no_grad():
                    model(input_ids=torch.tensor([r["prompt_ids"] + gen[:ende_i + 1]]))
            except Stopp:
                pass
            A = speicher["a"][len(r["prompt_ids"]):]
            s_alle = {k: (A @ v).numpy() for k, v in K.items()}
            geschlossen = zu in gen
            enden = [m.end() for m in wm.SATZENDE.finditer(denk, tchar)]
            n_laeufe += 1
            lauf_werte = {k: {"Ende": [], "rest": []} for k in s_alle}
            for nr, e in enumerate(enden):
                rest_txt = denk[e:]
                if not rest_txt.strip():
                    art = "Ende" if geschlossen else None
                elif wm.WARTE.match(rest_txt):
                    art = "Warte"
                else:
                    art = "Weiter"
                if art is None:
                    continue
                ti = int(np.searchsorted(grenzen, e - 1, side="right"))
                ti = min(ti, len(stuecke) - 1)
                for k, s in s_alle.items():
                    p = float(s[max(0, ti - 3):ti + 1].mean())
                    weichen[k][art].append(p)
                    lauf_werte[k]["Ende" if art == "Ende" else "rest"].append(p)
                    for b, (lo, hi) in enumerate(BINS):
                        if lo <= nr < hi:
                            verlauf[k][b].append(p)
            if geschlossen and (not enden or denk[enden[-1]:].strip()):
                for k, s in s_alle.items():
                    p = float(s[max(0, len(stuecke) - 4):len(stuecke)].mean())
                    weichen[k]["Ende"].append(p)
                    lauf_werte[k]["Ende"].append(p)
            for k in s_alle:
                if lauf_werte[k]["Ende"] and lauf_werte[k]["rest"]:
                    je_lauf[k].append((lauf_werte[k]["Ende"][-1], float(np.median(lauf_werte[k]["rest"]))))
            print(f"{name}: {r['id']} τy-Zeichen {tchar}, Weichen {len(enden)}, geschlossen {geschlossen}", flush=True)
        res = {"laeufe": n_laeufe}
        for k in K:
            w = weichen[k]
            res[k] = {"n": {x: len(v) for x, v in w.items()},
                      "mittel": {x: round(float(np.mean(v)), 4) if v else None for x, v in w.items()},
                      "AUC_Ende_gegen_rest": auc(w["Ende"], w["Warte"] + w["Weiter"]),
                      "AUC_Warte_gegen_Weiter": auc(w["Warte"], w["Weiter"]),
                      "verlauf_mittel": [round(float(np.mean(v)), 4) if v else None for v in verlauf[k]]}
            # Vorzeichentest je Lauf (konservativ: ein Wert je abgebendem Lauf): Pegel an der Ende-Weiche über dem Median?
            hoeher = sum(e > m for e, m in je_lauf[k])
            nl = len(je_lauf[k])
            p1 = sum(comb(nl, x) for x in range(hoeher, nl + 1)) / 2 ** nl if nl else None
            res[k]["je_lauf"] = {"laeufe_mit_abgabe": nl, "ende_ueber_median": hoeher, "p_einseitig": p1}
        erg[name] = res
        print(f"\n== {name}: {json.dumps(res, ensure_ascii=False)}\n", flush=True)
        del model
    json.dump(erg, open(a.aus, "w"), indent=1)
    print("gespeichert:", a.aus)


if __name__ == "__main__":
    main()
