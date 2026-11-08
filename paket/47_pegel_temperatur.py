"""Schritt 1a (vorab festgelegt 06.11. ~20:05, ANNAHMEN): Pegel des Schleifen-Melders bei Temperatur 0,6 gegen 1,0.

Die 64 Spalten S von Schicht 15 (Eingang von down_proj = SiLU(gate)·up) sind für denselben Text bei eigen, ERGORE und MIT
identisch – die Eingriffe wirken erst IN down_proj. Darum liest ein einziges Lesemodell alle Läufe. Pegel:
  roh      s_roh(t) = (u_eᵀ W₀)[S] · a_S(t)       (Auslöser der Umkehr)
  geschärft s_lda(t) = k_scharf[S] · a_S(t)       (Auslöser des Abschluss-Schubs bei ERGORE)
Kennzahlen je Lauf: Feuerrate (Anteil Denk-Tokens mit s_lda > θ; θ = 95-%-Quantil über alle Denk-Tokens der ERGORE-0,6-Läufe),
Pegel beim Schließen (Mittel der 16 Tokens vor </think>). Lesart (vorab): (i) Regime = mediane Feuerrate ERGORE bei 1,0 < ½ von
0,6. (ii) Fehlzündung = leere Schließungen (Flur) ERGORE 1,0 im Median ≥ Median der ordentlichen Schließungen bei 0,6.
(iii) thermisches Zucken = diese im Median < Median aller Denk-Tokens bei 0,6.
  python 47_pegel_temperatur.py --laeufe ERGORE06=ergebnisse/tag2-kw75-s0/ergebnisse.jsonl ERGORE10=ergebnisse/temp10-kw75/ergebnisse.jsonl \
      ... --aus ergebnisse/pegel_temperatur
"""
import argparse
import json
import os
import sys

import numpy as np

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(HIER)
sys.path.insert(0, HIER)
import wsp_lib as W  # noqa: E402

L = 15
FENSTER = 16


class Stopp(Exception):
    pass


def lesemodell(pfad, geraet, St, speicher):
    import torch
    import transformers as tf
    dt = torch.bfloat16 if geraet == "cuda" else torch.float32
    cls = getattr(tf, "AutoModelForImageTextToText", None) or tf.AutoModelForCausalLM
    try:
        model = cls.from_pretrained(pfad, dtype=dt)
    except Exception:  # noqa: BLE001
        model = tf.AutoModelForCausalLM.from_pretrained(pfad, dtype=dt)
    model.to(geraet).eval()

    def hook(mod, inp):
        speicher["a"] = inp[0][0][:, St.to(inp[0].device)].detach().float().cpu()
        raise Stopp()
    for n, m in model.named_modules():
        if n.endswith(f"layers.{L}.mlp.down_proj") and "visual" not in n:
            m.register_forward_pre_hook(hook)
    return model


def lies(model, ids, geraet, speicher, notfall, pfad, St):
    import torch
    speicher.clear()
    oom = False
    try:
        with torch.no_grad():
            model(input_ids=torch.tensor([ids], device=geraet))
    except Stopp:
        pass
    except torch.OutOfMemoryError:
        oom = True
    if not oom:
        return geraet
    speicher.clear()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    if notfall.get("cpu") is None:
        print("Speicher reicht nicht: Notausgang CPU (fp32)", flush=True)
        notfall["cpu"] = lesemodell(pfad, "cpu", St, speicher)
    try:
        with torch.no_grad():
            notfall["cpu"](input_ids=torch.tensor([ids]))
    except Stopp:
        pass
    return "cpu"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--laeufe", nargs="+", required=True, help="name=ergebnisse.jsonl")
    ap.add_argument("--richtung", default=os.path.join(WURZEL, "ergebnisse", "eigene_richtung-vL.npz"))
    ap.add_argument("--basis", default=os.path.join(WURZEL, "modelle", "Qwen3.5-0.8B"))
    ap.add_argument("--lesemodell", default=os.path.join(WURZEL, "modelle", "Qwen3.5-0.8B-eigen-vL"))
    ap.add_argument("--geschaerft", default=os.path.join(WURZEL, "ergebnisse", "melder_geschaerft.npz"))
    ap.add_argument("--geraet", default="cuda")
    ap.add_argument("--max-laeufe", type=int, default=0)
    ap.add_argument("--max-len", type=int, default=12288)
    ap.add_argument("--aus", required=True, help="Pfad ohne Endung (.npz + .json)")
    a = ap.parse_args()
    import torch
    import transformers as tf
    torch.set_num_threads(int(os.environ.get("WSP_THREADS", 2)))
    R = dict(np.load(a.richtung))
    S = np.asarray(R[f"spalten_{L}"], dtype=np.int64)
    _, bits = W.tensor_lesen(a.basis, f"model.language_model.layers.{L}.mlp.down_proj.weight", W.tensor_index(a.basis))
    W0 = np.asarray(W.bf16_to_f32(np.asarray(bits)), dtype=np.float64)
    u = R[f"u_{L}"].astype(np.float64)
    u /= np.linalg.norm(u)
    k_roh = (u @ W0)[S].astype(np.float32)
    k_lda = np.load(a.geschaerft)[f"k_{L}"][S].astype(np.float32)
    St = torch.tensor(S)
    tok = tf.AutoTokenizer.from_pretrained(a.basis)
    ZU = tok.convert_tokens_to_ids("</think>")
    speicher, notfall = {}, {"cpu": None}
    model = lesemodell(a.lesemodell, a.geraet, St, speicher)
    zeilen, arrays = [], {}
    for spec in a.laeufe:
        name, pfad = spec.split("=", 1)
        n = 0
        for z in open(pfad, encoding="utf-8"):
            if a.max_laeufe and n >= a.max_laeufe:
                break
            r = json.loads(z)
            gen = r["gen_ids"][:a.max_len]
            zu_i = gen.index(ZU) if ZU in gen else -1
            g_r = lies(model, r["prompt_ids"] + gen, a.geraet, speicher, notfall, a.lesemodell, St)
            A = speicher["a"][len(r["prompt_ids"]):].numpy()
            s_roh, s_lda = A @ k_roh, A @ k_lda
            ende_denk = zu_i if zu_i >= 0 else len(gen)
            arrays[f"{name}|{r['id']}|lda"] = s_lda[:ende_denk].astype(np.float32)
            arrays[f"{name}|{r['id']}|roh"] = s_roh[:ende_denk].astype(np.float32)
            zeilen.append({"name": name, "id": r["id"], "korrekt": bool(r["korrekt"]), "geschlossen": zu_i >= 0,
                           "zu_token": zu_i, "ende": r["ende"], "flur": zu_i >= 0 and r["ende"] != "eos",
                           "pegel_zu_lda": float(s_lda[max(0, zu_i - FENSTER):zu_i].mean()) if zu_i > 0 else None,
                           "pegel_zu_roh": float(s_roh[max(0, zu_i - FENSTER):zu_i].mean()) if zu_i > 0 else None,
                           "geraet": g_r})
            n += 1
            print(f"{name} {r['id']}: {ende_denk} Denk-Tokens, geschlossen {zu_i >= 0}, flur {zeilen[-1]['flur']}", flush=True)
    np.savez_compressed(a.aus + ".npz", **arrays)
    # Auswertung nach vorab festgelegter Lesart
    def denk(name, art="lda"):
        return [arrays[f"{z['name']}|{z['id']}|{art}"] for z in zeilen if z["name"] == name]
    ref = np.concatenate([x for x in denk("ERGORE06") if len(x)]) if any(z["name"] == "ERGORE06" for z in zeilen) else None
    erg = {"fenster": FENSTER, "bedingungen": {}}
    if ref is None:
        print("Keine ERGORE06-Läufe – Auswertung übersprungen")
        json.dump({"zeilen": zeilen}, open(a.aus + ".json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
        return
    theta = float(np.quantile(ref, 0.95))
    erg["theta"] = theta
    erg["median_denk_06"] = float(np.median(ref))
    print(f"θ (95-%-Quantil Denk-Tokens ERGORE 0,6) = {theta:.3f}; Median Denk-Tokens ERGORE 0,6 = {erg['median_denk_06']:.3f}")
    for name in sorted({z["name"] for z in zeilen}):
        zz = [z for z in zeilen if z["name"] == name]
        raten = [float((arrays[f"{name}|{z['id']}|lda"] > theta).mean()) for z in zz if len(arrays[f"{name}|{z['id']}|lda"])]
        zu_ordentl = [z["pegel_zu_lda"] for z in zz if z["geschlossen"] and not z["flur"] and z["pegel_zu_lda"] is not None]
        zu_flur = [z["pegel_zu_lda"] for z in zz if z["flur"] and z["pegel_zu_lda"] is not None]
        d = {"laeufe": len(zz), "geschlossen": sum(z["geschlossen"] for z in zz), "flur": sum(z["flur"] for z in zz),
             "feuerrate_median": float(np.median(raten)) if raten else None,
             "pegel_zu_ordentlich_median": float(np.median(zu_ordentl)) if zu_ordentl else None,
             "pegel_zu_flur_median": float(np.median(zu_flur)) if zu_flur else None,
             "pegel_denk_median": float(np.median(np.concatenate(denk(name)))) if denk(name) else None}
        erg["bedingungen"][name] = d
        print(f"  {name:9s} Läufe {d['laeufe']:2d} | geschlossen {d['geschlossen']:2d} | Flur {d['flur']:2d} | Feuerrate (Median) "
              f"{d['feuerrate_median']} | Pegel beim Schließen: ordentlich {d['pegel_zu_ordentlich_median']}, Flur "
              f"{d['pegel_zu_flur_median']} | Denk-Median {d['pegel_denk_median']}")
    B = erg["bedingungen"]
    if "ERGORE06" in B and "ERGORE10" in B:
        f06, f10 = B["ERGORE06"]["feuerrate_median"], B["ERGORE10"]["feuerrate_median"]
        regime = f06 is not None and f10 is not None and f10 < 0.5 * f06
        fz = B["ERGORE10"]["pegel_zu_flur_median"]
        ord06 = B["ERGORE06"]["pegel_zu_ordentlich_median"]
        fehlz = fz is not None and ord06 is not None and fz >= ord06
        therm = fz is not None and fz < erg["median_denk_06"]
        erg["urteil"] = {"regime": regime, "fehlzuendung": fehlz, "thermisch": therm}
        print(f"URTEIL 1a: Regime (Feuerrate {f06} → {f10}): {'JA' if regime else 'nein'} | Fehlzündung (Flur-Pegel {fz} ≥ "
              f"ordentlich 0,6 {ord06}): {'JA' if fehlz else 'nein'} | thermisches Zucken (Flur-Pegel < Denk-Median 0,6 "
              f"{erg['median_denk_06']:.3f}): {'JA' if therm else 'nein'}")
    erg["zeilen"] = zeilen
    json.dump(erg, open(a.aus + ".json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
