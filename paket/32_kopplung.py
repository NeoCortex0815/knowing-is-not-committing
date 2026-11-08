"""Kopplungs-Eingriff (Idee 06.11. ~03:30, „ERGO-Kante“; Nutzer: „Sicherheit ERGO gib jetzt ab“).

Eigener Auslöser bleibt (unsere u, unsere 64 Spalten S, alpha wie eigen-vL). Zur Umkehr kommt ein Schub entlang einer
eigenen Abschluss-Achse e (Entschluss-Achse, als Control Vector ursächlich), vorher orthogonal zu u gemacht:
    W1 = W0 - alpha * outer(u, k) + vz * beta * outer(e_perp, k),   k = maske_S * (u @ W0)
Wirkung je Token: Δh = (−alpha·u + vz·beta·e_perp) · s(t) mit s(t) = Σ_{j∈S} k_j a_j(t) – der Schub wirkt nur in dem
Maß, in dem die Spalten S feuern (bedingt statt Dauer-Schub wie beim Control Vector).
  messen: s(t) an Schicht 15/19 auf eigen-vL-Transkripten (CPU). Wiederholungs-Positionen (8-Gramm schon einmal da)
          gegen übrige Positionen → Vorzeichen vz (Schub Richtung Abschluss, während die Schleife läuft) und Bedingtheit.
  bauen:  Modell mit Kopplung. Kontrolle: der Teil ohne beta ist bitgleich mit eigen-vL (--vergleich).
  python 32_kopplung.py messen --modell modelle/Qwen3.5-0.8B-eigen-vL --basis modelle/Qwen3.5-0.8B \
      --richtung ergebnisse/eigene_richtung-vL.npz --ergebnisse ergebnisse/entschluss-uebung-eigen/ergebnisse.jsonl
  python 32_kopplung.py bauen --basis modelle/Qwen3.5-0.8B --richtung ergebnisse/eigene_richtung-vL.npz \
      --achse ergebnisse/richtung-entschluss.npz --beta 15:3,19:3 --vz 1 --vergleich modelle/Qwen3.5-0.8B-eigen-vL \
      --aus modelle/Qwen3.5-0.8B-kopplung
"""
import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wsp_lib as W  # noqa: E402

MUSTER = "model.language_model.layers.{L}.mlp.down_proj.weight"
SCHICHTEN = (15, 19)


def schluessel(basis, R):
    index = W.tensor_index(basis)
    out = {}
    for L in SCHICHTEN:
        _, bits = W.tensor_lesen(basis, W.tensorname(MUSTER, L), index)
        W0 = np.asarray(W.bf16_to_f32(np.asarray(bits)), dtype=np.float64)
        u = R[f"u_{L}"].astype(np.float64)
        u /= np.linalg.norm(u)
        S = np.asarray(R[f"spalten_{L}"], dtype=np.int64)
        k = np.zeros(W0.shape[1])
        k[S] = (u @ W0)[S]
        out[L] = (W0, u, S, k)
    return out


def wiederholung(gen, n=8):
    gesehen, mark = set(), []
    for t in range(len(gen)):
        g = tuple(gen[max(0, t - n + 1):t + 1])
        mark.append(len(g) == n and g in gesehen)
        gesehen.add(g)
    return np.array(mark)


def messen(a):
    import torch
    import transformers as tf
    R = dict(np.load(a.richtung))
    K = {L: torch.tensor(v[3], dtype=torch.float32) for L, v in schluessel(a.basis, R).items()}
    rs = [json.loads(z) for z in open(a.ergebnisse, encoding="utf-8")]
    tok = tf.AutoTokenizer.from_pretrained(a.modell)
    zu = tok.convert_tokens_to_ids("</think>")
    schleife = sorted([r for r in rs if r.get("ende") != "eos"],
                      key=lambda r: -wiederholung(r["gen_ids"][:a.max_len]).mean())[:a.n_schleife]
    fertig = [r for r in rs if r.get("ende") == "eos" and r.get("korrekt") and zu in r["gen_ids"]][:a.n_fertig]
    cls = getattr(tf, "AutoModelForImageTextToText", None) or tf.AutoModelForCausalLM
    try:
        model = cls.from_pretrained(a.modell, dtype=torch.float32)
    except Exception:  # noqa: BLE001
        model = tf.AutoModelForCausalLM.from_pretrained(a.modell, dtype=torch.float32)
    model.eval()
    speicher = {}
    for n, m in model.named_modules():
        for L in SCHICHTEN:
            if n.endswith(f"layers.{L}.mlp.down_proj") and "visual" not in n:
                m.register_forward_pre_hook(lambda mod, inp, L=L: speicher.__setitem__(L, (inp[0][0] @ K[L]).detach()))
    erg = {"texte": []}
    pool = {L: {"wdh": [], "rest": [], "vor_ende": []} for L in SCHICHTEN}
    for art, r in [("schleife", r) for r in schleife] + [("fertig", r) for r in fertig]:
        gen = r["gen_ids"][:a.max_len]
        if art == "fertig":
            gen = r["gen_ids"][:r["gen_ids"].index(zu) + 1][:a.max_len]
        with torch.no_grad():
            model(input_ids=torch.tensor([r["prompt_ids"] + gen]))
        mark = wiederholung(gen)
        z = {"id": r["id"], "art": art, "tokens": len(gen), "anteil_wdh": round(float(mark[100:].mean()), 3)}
        for L in SCHICHTEN:
            s = speicher[L][len(r["prompt_ids"]):].numpy()
            w, rest = s[100:][mark[100:]], s[100:][~mark[100:]]
            z[f"s{L}_wdh"] = round(float(w.mean()), 4) if len(w) else None
            z[f"s{L}_rest"] = round(float(rest.mean()), 4) if len(rest) else None
            pool[L]["wdh"] += list(w)
            pool[L]["rest"] += list(rest)
            if art == "fertig":
                z[f"s{L}_vor_ende"] = round(float(s[-33:-1].mean()), 4)
                pool[L]["vor_ende"] += list(s[-33:-1])
        erg["texte"].append(z)
        print(json.dumps(z, ensure_ascii=False), flush=True)
    for L in SCHICHTEN:
        p = {k: (round(float(np.mean(v)), 4), round(float(np.std(v)), 4), len(v)) for k, v in pool[L].items() if v}
        erg[f"schicht_{L}"] = p
        print(f"Schicht {L} (Mittel, Streuung, n):", p, flush=True)
    if a.aus:
        json.dump(erg, open(a.aus, "w"), indent=1)


def bauen(a):
    R = dict(np.load(a.richtung))
    A = dict(np.load(a.achse))
    K2 = dict(np.load(a.ausloeser)) if a.ausloeser else {}   # geschärfter Melder (37_melder_schaerfen.py): nur für den β-Teil
    beta = {int(k): float(v) for k, v in (x.split(":") for x in a.beta.split(","))}
    patches, info = {}, {}
    for L, (W0, u, S, k) in schluessel(a.basis, R).items():
        name = W.tensorname(MUSTER, L)
        W1 = np.asarray(W.rang1_edit(W0, u, S, a.alpha), dtype=np.float64)
        i = {"spalten": int(len(S)), "alpha": a.alpha, "beta": beta[L], "vz": a.vz}
        if a.vergleich:
            _, ref = W.tensor_lesen(a.vergleich, name)
            i["ohne_beta_bitgleich_wie_vergleich"] = round(float(np.mean(np.asarray(ref) == W.bf16_bits(W1))), 6)
        e = A[f"u_{L}"].astype(np.float64)
        i["cos_e_u"] = round(float(e @ u / np.linalg.norm(e)), 4)
        e -= (e @ u) * u
        e /= np.linalg.norm(e)
        kb = K2.get(f"k_{L}", k)
        i["ausloeser"] = "geschaerft" if f"k_{L}" in K2 else "roh"
        W1 = W1 + a.vz * beta[L] * np.outer(e, kb)
        neu = W.bf16_bits(W1)
        patches[name] = neu
        i["relative_aenderung"] = round(float(np.linalg.norm(W1 - W0) / np.linalg.norm(W0)), 5)
        info[name] = i
        print(name, i, flush=True)
    meta = {"richtung": os.path.abspath(a.richtung), "achse": os.path.abspath(a.achse), "alpha": a.alpha,
            "beta": beta, "vz": a.vz, "ausloeser": os.path.abspath(a.ausloeser) if a.ausloeser else None,
            "formel": "W = W0 - alpha*outer(u,k) + vz*beta*outer(e_perp,k), k = maske*(u@W0)", "tensoren": info}
    W.modell_mit_patch(a.basis, a.aus, patches, meta)
    print("Modell:", a.aus)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("messen")
    m.add_argument("--modell", required=True); m.add_argument("--basis", required=True)
    m.add_argument("--richtung", required=True); m.add_argument("--ergebnisse", required=True)
    m.add_argument("--max-len", type=int, default=3000); m.add_argument("--n-schleife", type=int, default=2)
    m.add_argument("--n-fertig", type=int, default=2); m.add_argument("--aus", default="")
    b = sub.add_parser("bauen")
    b.add_argument("--basis", required=True); b.add_argument("--richtung", required=True)
    b.add_argument("--achse", required=True); b.add_argument("--alpha", type=float, default=6.0)
    b.add_argument("--beta", required=True, help="je Schicht, z.B. 15:3,19:3")
    b.add_argument("--vz", type=int, choices=[-1, 1], required=True); b.add_argument("--vergleich", default="")
    b.add_argument("--ausloeser", default="", help="npz mit k_15 (geschärfter Melder) – ersetzt den Auslöser nur im β-Teil")
    b.add_argument("--aus", required=True)
    a = ap.parse_args()
    messen(a) if a.cmd == "messen" else bauen(a)


if __name__ == "__main__":
    main()
