"""Wirktiefe des Abschluss-Schubs (08.11.; Nutzer: „Der Abschluss-Schub ĝ wirkt nur einen einzigen Schritt lang – das ist unser
Tiefenproblem“; Argon: Ein-Token-Impuls; NACHTRÄGLICH, erkundend; Vortest für einen Effektor mit „innerem fertig“).
Stellen: WT-As Reflex-Abschlüsse am richtigen Wert auf 161–300 (aus 82).
- Die Wahrheit ist dort gegeben.
- Präfix = Aufgabe + Denken bis einschließlich des Tokens, an dem der Reflex `</think>` auslöste.
Bedingungen (gierig, also deterministisch):
  WT-A     – das echte WT-A-Modell (Reflex wie gebaut)
  keiner   – eigen (= WT-A ohne Reflex)
  ĝ        – eigen + einmaliger Schub κ = 7 entlang ĝ an der letzten Präfix-Stelle (L15-MLP-Ausgang), also der Reflex nachgebaut
  −r⊥ / +r⊥ – eigen + einmaliger Schub κ = 7 entlang MITs Rest-Richtung r⊥ (MIT-u ohne den Anteil der eigenen Richtung).
              r⊥ steht senkrecht auf ĝ.
Lauf A (frei, 160 Tokens):
  - Schließt das Modell? Wann?
  - Steht vor `</think>` ein Schluss-Satz („so/therefore/thus/answer“)?
  - Folgt danach eine saubere Abgabe (`\\boxed`) oder Weiterdenken (Wait / Let me / zweites `</think>`)?
Lauf B (Wirktiefe, `</think>` 30 Schritte gesperrt): p(`</think>`) je Schritt. Ein Schub mit Wirktiefe hält p über
  mehrere Schritte hoch.
  python 93_wirktiefe.py [--n 46] [--geraet cuda]   → ergebnisse/wirktiefe.json
"""
import argparse
import json
import os
import re

import numpy as np

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(HIER)
ERG = os.path.join(WURZEL, "ergebnisse")
DIRS = ["s3-wta-161-210", "s3-wta-211-260", "s3-wta-261-300"]
SCHLUSS = re.compile(r"\b(so|therefore|thus|hence|the answer|final answer)\b", re.I)
WEITER = re.compile(r"(Wait|wait,|Let me|let me|Hmm|</think>)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=46)
    ap.add_argument("--geraet", default="cuda")
    ap.add_argument("--dtype", default="bf16")
    ap.add_argument("--frei", type=int, default=160)
    ap.add_argument("--sperre", type=int, default=30)
    a = ap.parse_args()
    import torch
    import transformers as tf
    dev = torch.device(a.geraet)
    dt = torch.bfloat16 if a.dtype == "bf16" else torch.float32
    tok = tf.AutoTokenizer.from_pretrained(os.path.join(WURZEL, "modelle", "Qwen3.5-0.8B"))
    ZU = tok.convert_tokens_to_ids("</think>")
    # Stellen
    runs = {}
    for d in DIRS:
        for z in open(os.path.join(ERG, d, "ergebnisse.jsonl"), encoding="utf-8"):
            r = json.loads(z)
            runs[r["id"]] = r
    stellen = []
    for z in open(os.path.join(ERG, "zucken_WT-A_ergo-zigA.jsonl"), encoding="utf-8"):
        r = json.loads(z)
        if r["zu_tok"] is None:
            continue
        xc = [x for x in r["stellen"] if x[0] == r["zu_tok"] - 1 and x[7] is not None]
        if not xc or not (xc[0][7] < 0.02 and xc[0][5] >= 0.2):
            continue
        A = [s for s in r["aussagen"] if s["t"] < r["zu_tok"]]
        if not A:
            continue
        letzte = max(A, key=lambda s: s["t"])
        if letzte["ok"] and r["zu_tok"] - letzte["t"] <= 64:
            stellen.append((r["id"], r["zu_tok"]))
    stellen = stellen[:a.n]
    print(f"Reflex-Abschlüsse am richtigen Wert: {len(stellen)}", flush=True)
    # Richtungen
    g = np.load(os.path.join(ERG, "abschluss_gradient.npz"))["g_15"].astype(np.float64)
    g /= np.linalg.norm(g)
    um = np.load(os.path.join(WURZEL, "minipc", "mit_richtung.npz"))["u_15"].astype(np.float64)
    ue = np.load(os.path.join(ERG, "eigene_richtung-vL.npz"))["u_15"].astype(np.float64)
    um /= np.linalg.norm(um)
    ue /= np.linalg.norm(ue)
    rp = um - (um @ ue) * ue
    rp /= np.linalg.norm(rp)
    print(f"cos(ĝ, r⊥) = {g @ rp:+.3f}", flush=True)
    kappa = 7.0
    richt = {"ĝ": g, "−r⊥": -rp, "+r⊥": rp}
    cls = getattr(tf, "AutoModelForImageTextToText", None) or tf.AutoModelForCausalLM

    def lade(name):
        m = cls.from_pretrained(os.path.join(WURZEL, "modelle", name), dtype=dt).to(dev).eval()
        mlp = [mm for n_, mm in m.named_modules() if re.search(r"language_model\.layers\.15\.mlp$", n_)][0]
        return m, mlp
    erg = {}
    pfad_erg = os.path.join(ERG, "wirktiefe.json")
    if os.path.exists(pfad_erg) and "--neu" not in __import__("sys").argv:  # fortsetzbar (08.11. ~11:55)
        erg = json.load(open(pfad_erg, encoding="utf-8"))
        print(f"schon fertig: {list(erg)}", flush=True)
    # 08.11. ~11:20 (Nutzer-Bild „Tür aufreißen“ gegen „zur Tür begleiten“): zusätzlich „begleitet“ – derselbe Gesamtschub κ,
    # verteilt auf die letzte Präfix-Stelle und die 2 folgenden Schritte (je κ/3), statt einmal κ.
    for modellname, bedingungen in (("Qwen3.5-0.8B-ergo-zigA", ["WT-A"]),
                                    ("Qwen3.5-0.8B-eigen-vL", ["keiner", "ĝ", "−r⊥", "+r⊥", "ĝ begleitet", "−r⊥ begleitet"])):
        model, mlp = lade(modellname)
        schub = {"v": None, "rest": 0}

        def haken(mod, inp, out):
            if schub["v"] is None:
                return out
            if out.shape[1] > 1:  # Vorlauf über das Präfix: letzte Stelle
                out = out.clone()
                out[0, -1] = out[0, -1] + schub["v"].to(out.dtype)
                return out
            if schub["rest"] > 0:  # „begleitet“: auch die nächsten Schritte
                schub["rest"] -= 1
                out = out.clone()
                out[0, -1] = out[0, -1] + schub["v"].to(out.dtype)
                return out
            return out
        mlp.register_forward_hook(haken)
        for bed in bedingungen:
            if bed in erg:
                continue
            begleitet = bed.endswith("begleitet")
            basis = bed.replace(" begleitet", "")
            schub["v"] = None if bed in ("WT-A", "keiner") else torch.tensor(
                (kappa / 3 if begleitet else kappa) * richt[basis], dtype=torch.float32, device=dev)
            A_, B_ = [], []
            for i, zu_tok in stellen:
                r = runs[i]
                ids = torch.tensor([r["prompt_ids"] + r["gen_ids"][:zu_tok]], device=dev)
                schub["rest"] = 2 if begleitet else 0
                with torch.no_grad():
                    out = model.generate(ids, max_new_tokens=a.frei, do_sample=False, pad_token_id=tok.eos_token_id)
                neu = out[0, ids.shape[1]:].tolist()
                zu = neu.index(ZU) if ZU in neu else None
                vor = tok.decode(neu[:zu] if zu is not None else neu[:40])
                nach = tok.decode(neu[zu + 1:zu + 121]) if zu is not None else ""
                A_.append({"id": i, "zu_schritt": zu, "schluss_satz": bool(SCHLUSS.search(vor)) if zu is not None else None,
                           "abgabe": ("\\boxed" in nach) if zu is not None else None,
                           "weiterdenken": bool(WEITER.search(nach)) if zu is not None else None,
                           "vor": vor[-100:], "nach": nach[:120]})
                # Lauf B: </think> gesperrt, p(</think>) je Schritt
                ps = []

                class Sperre(tf.LogitsProcessor):
                    def __call__(self, input_ids, scores):
                        ps.append(float(torch.softmax(scores.float(), -1)[0, ZU]))
                        scores[:, ZU] = -float("inf")
                        return scores
                schub["rest"] = 2 if begleitet else 0
                with torch.no_grad():
                    model.generate(ids, max_new_tokens=a.sperre, do_sample=False, pad_token_id=tok.eos_token_id,
                                   logits_processor=tf.LogitsProcessorList([Sperre()]))
                B_.append(ps)
            P = np.array([p + [np.nan] * (a.sperre - len(p)) for p in B_])
            zus = [x for x in A_ if x["zu_schritt"] is not None]
            e = {"n": len(A_), "geschlossen": len(zus), "zu_sofort(Schritt 0)": sum(1 for x in zus if x["zu_schritt"] == 0),
                 "zu_schritt_median": float(np.median([x["zu_schritt"] for x in zus])) if zus else None,
                 "schluss_satz_vorher": sum(1 for x in zus if x["schluss_satz"]),
                 "abgabe_nach": sum(1 for x in zus if x["abgabe"]), "weiterdenken_nach": sum(1 for x in zus if x["weiterdenken"]),
                 "p_profil_median": [float(np.nanmedian(P[:, k])) for k in range(a.sperre)],
                 "p_profil_mittel": [float(np.nanmean(P[:, k])) for k in range(a.sperre)],
                 "beispiele": A_[:4]}
            erg[bed] = e
            json.dump(erg, open(os.path.join(ERG, "wirktiefe.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
            prof = e["p_profil_mittel"]
            print(f"{bed:6s}: geschlossen {e['geschlossen']}/{e['n']} (sofort {e['zu_sofort(Schritt 0)']}, Median-Schritt "
                  f"{e['zu_schritt_median']}) | Schluss-Satz davor {e['schluss_satz_vorher']} | danach Abgabe {e['abgabe_nach']}, "
                  f"Weiterdenken {e['weiterdenken_nach']} | p(</think>) gesperrt, Mittel Schritt 0/1/2/5/10/20: "
                  + "/".join(f"{prof[k]:.3f}" for k in (0, 1, 2, 5, 10, 20) if k < len(prof)), flush=True)
        del model
        if dev.type == "cuda":
            torch.cuda.empty_cache()
    json.dump(erg, open(os.path.join(ERG, "wirktiefe.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(f"gespeichert: {os.path.join(ERG, 'wirktiefe.json')}")


if __name__ == "__main__":
    main()
