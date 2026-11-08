"""Geschärfter Melder (Argon 06.11. ~04:30, Vorschlag C_off; Nutzer 05:00: „Messerschneide via Stärke-Druckpunkt auf den
Urknall-Moment lenken“).

Problem (Messung 03:45, Dosis-Reihe 04:15–05:00): Unser Auslöser s(t) = k_rawᵀ a_S(t) (64 Spalten S, Schicht 15) feuert
außerhalb von Schleifen noch mit ~37 % – vor τy und im Antwortteil → Früh-Schließen und „Flur“ (Denken zu, Antwort
rechnet weiter). Abhilfe: Auslöser gegen diese Bereiche weißen. C_off = ½ E_vorτy[a aᵀ] + ½ E_Antwort[a aᵀ] + λI (64×64).
Zwei Kandidaten, beide so skaliert, dass der mittlere Schleifen-Pegel gleich bleibt wie roh (β behält seine Bedeutung):
  argon: k ∝ C_off⁻¹ k_raw   (Argons Formel, bleibt nah an der Schreib-Richtung)
  lda:   k ∝ C_off⁻¹ μ_Schleife (Fisher-artig: Schleife gegen Aus-Bereiche bestmöglich trennen)
Gewählt wird VORAB FESTGELEGT der Kandidat mit der besten Trennung auf der zurückgehaltenen Hälfte B:
  Trennung = Schleifen-Pegel / max(Pegel vor τy, Pegel Antwortteil).
Nur der β-Teil der Kopplung nutzt den geschärften Melder; die Umkehr (α) bleibt wie eigen-vL (32_kopplung.py --ausloeser).
  sammeln: a_S(t) an Schicht 15 auf eigen-vL-Übungstranskripten (CPU) mit Bereichs-Etiketten (vor τy / Denken / Antwort)
  bauen:   C_off auf Hälfte A, Trennung auf Hälfte B, Auswahl, speichert k_15 (3584, nur S besetzt)
  python 37_melder_schaerfen.py sammeln --modell modelle/Qwen3.5-0.8B-eigen-vL --richtung ergebnisse/eigene_richtung-vL.npz \
      --ergebnisse ergebnisse/entschluss-uebung-eigen/ergebnisse.jsonl --aus ergebnisse/melder_sammlung.npz
  python 37_melder_schaerfen.py bauen --basis modelle/Qwen3.5-0.8B --richtung ergebnisse/eigene_richtung-vL.npz \
      --sammlung ergebnisse/melder_sammlung.npz --aus ergebnisse/melder_geschaerft.npz
"""
import argparse
import importlib.util
import json
import os
import sys

import numpy as np

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
import wsp_lib as W  # noqa: E402

MUSTER = "model.language_model.layers.{L}.mlp.down_proj.weight"
L = 15


def lade(name, datei):
    s = importlib.util.spec_from_file_location(name, os.path.join(HIER, datei))
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


def wiederholung(gen, n=8):
    gesehen, mark = set(), []
    for t in range(len(gen)):
        g = tuple(gen[max(0, t - n + 1):t + 1])
        mark.append(len(g) == n and g in gesehen)
        gesehen.add(g)
    return np.array(mark, bool)


def sammeln(a):
    import torch
    import transformers as tf
    torch.set_num_threads(max(1, (os.cpu_count() or 2) // 2))
    am = lade("am", "22_angstmarker.py")
    R = dict(np.load(a.richtung))
    S = torch.tensor(np.asarray(R[f"spalten_{L}"], dtype=np.int64))
    rs = [json.loads(z) for z in open(a.ergebnisse, encoding="utf-8")]
    tok = tf.AutoTokenizer.from_pretrained(a.modell)
    zu = tok.convert_tokens_to_ids("</think>")
    fertig = sorted([r for r in rs if r.get("ende") == "eos" and zu in r["gen_ids"] and len(r["gen_ids"]) <= a.max_len],
                    key=lambda r: len(r["gen_ids"]))[:a.n_fertig]
    schleife = sorted([r for r in rs if r.get("ende") != "eos"],
                      key=lambda r: -wiederholung(r["gen_ids"][:a.max_len]).mean())[:a.n_schleife]
    cls = getattr(tf, "AutoModelForImageTextToText", None) or tf.AutoModelForCausalLM
    try:
        model = cls.from_pretrained(a.modell, dtype=torch.float32)
    except Exception:  # noqa: BLE001
        model = tf.AutoModelForCausalLM.from_pretrained(a.modell, dtype=torch.float32)
    model.eval()
    speicher = {}
    for n, m in model.named_modules():
        if n.endswith(f"layers.{L}.mlp.down_proj") and "visual" not in n:
            m.register_forward_pre_hook(lambda mod, inp: speicher.__setitem__("a", inp[0][0][:, S].detach().float()))
    out, info = {}, []
    for j, r in enumerate(fertig + schleife):
        gen = r["gen_ids"][:a.max_len]
        with torch.no_grad():
            model(input_ids=torch.tensor([r["prompt_ids"] + gen]))
        A = speicher["a"][len(r["prompt_ids"]):].numpy().astype(np.float32)
        T = len(gen)
        zu_i = gen.index(zu) if zu in gen else T
        stuecke = [tok.decode([t]) for t in gen[:zu_i]]
        tchar = am.tau("".join(stuecke), r.get("gold"))
        tau_i = None
        if tchar is not None:
            acc = 0
            for i, s in enumerate(stuecke):
                acc += len(s)
                if acc >= tchar:
                    tau_i = i
                    break
        region = np.zeros(T, np.int8)          # 0 Denken (nach τy / ohne τy) · 1 vor τy · 2 Antwortteil
        if tau_i is not None:
            region[:tau_i] = 1
        if zu_i < T:
            region[zu_i + 1:] = 2
        out[f"a_{j}"], out[f"region_{j}"], out[f"wdh_{j}"] = A, region, wiederholung(gen)
        z = {"id": r["id"], "art": "fertig" if j < len(fertig) else "schleife", "tokens": T, "tau": tau_i,
             "zu": zu_i if zu_i < T else None, "vor_tau": int((region == 1).sum()), "antwort": int((region == 2).sum()),
             "wdh": int(out[f"wdh_{j}"].sum())}
        info.append(z)
        print(json.dumps(z, ensure_ascii=False), flush=True)
    np.savez_compressed(a.aus, n=len(info), info=json.dumps(info), **out)
    print("gespeichert:", a.aus)


def bauen(a):
    Z = np.load(a.sammlung)
    n = int(Z["n"])
    R = dict(np.load(a.richtung))
    S = np.asarray(R[f"spalten_{L}"], dtype=np.int64)
    _, bits = W.tensor_lesen(a.basis, W.tensorname(MUSTER, L), W.tensor_index(a.basis))
    W0 = np.asarray(W.bf16_to_f32(np.asarray(bits)), dtype=np.float64)
    u = R[f"u_{L}"].astype(np.float64)
    u /= np.linalg.norm(u)
    k_raw = (u @ W0)[S]

    def teil(idx):
        Av, rg, wd = [], [], []
        for j in idx:
            Av.append(Z[f"a_{j}"].astype(np.float64))
            rg.append(Z[f"region_{j}"])
            wd.append(Z[f"wdh_{j}"])
        return np.concatenate(Av), np.concatenate(rg), np.concatenate(wd)

    A_A, rg_A, wd_A = teil(range(0, n, 2))      # Hälfte A: anpassen
    A_B, rg_B, wd_B = teil(range(1, n, 2))      # Hälfte B: prüfen
    schleife_A = (rg_A == 0) & wd_A
    C = 0.5 * np.cov(A_A[rg_A == 1].T, bias=True) + 0.5 * np.cov(A_A[rg_A == 2].T, bias=True)
    C += 0.5 * np.outer(A_A[rg_A == 1].mean(0), A_A[rg_A == 1].mean(0)) + 0.5 * np.outer(A_A[rg_A == 2].mean(0), A_A[rg_A == 2].mean(0))
    C += a.lam * np.trace(C) / len(C) * np.eye(len(C))
    mu = A_A[schleife_A].mean(0)
    kand = {"roh": k_raw, "argon": np.linalg.solve(C, k_raw), "lda": np.linalg.solve(C, mu)}

    def pegel(k, A, rg, wd):
        s = A @ k
        return {"schleife": float(s[(rg == 0) & wd].mean()), "denken_sonst": float(s[(rg == 0) & ~wd].mean()),
                "vor_tau": float(s[rg == 1].mean()), "antwort": float(s[rg == 2].mean())}

    bericht = {}
    ziel = float(mu @ k_raw)
    for name, k in kand.items():
        k = k * (ziel / float(mu @ k))           # Schleifen-Pegel (Hälfte A) wie roh
        kand[name] = k
        pb = pegel(k, A_B, rg_B, wd_B)
        trenn = pb["schleife"] / max(pb["vor_tau"], pb["antwort"], 1e-9)
        bericht[name] = {"haelfte_B": {x: round(y, 4) for x, y in pb.items()}, "trennung_B": round(trenn, 3)}
        print(f"{name:6s} Hälfte B: {bericht[name]['haelfte_B']} | Trennung {trenn:.2f}", flush=True)
    wahl = max(("argon", "lda"), key=lambda x: bericht[x]["trennung_B"])
    if bericht[wahl]["trennung_B"] <= bericht["roh"]["trennung_B"]:
        print("KEIN Gewinn gegenüber roh – nichts gespeichert", flush=True)
        json.dump({"bericht": bericht, "wahl": None}, open(os.path.splitext(a.aus)[0] + ".json", "w"), indent=1)
        return
    k15 = np.zeros(W0.shape[1])
    k15[S] = kand[wahl]
    np.savez(a.aus, k_15=k15)
    json.dump({"bericht": bericht, "wahl": wahl, "lam": a.lam}, open(os.path.splitext(a.aus)[0] + ".json", "w"), indent=1)
    print(f"gewählt: {wahl} (Trennung {bericht[wahl]['trennung_B']} statt roh {bericht['roh']['trennung_B']}) → {a.aus}")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("sammeln")
    s.add_argument("--modell", required=True); s.add_argument("--richtung", required=True)
    s.add_argument("--ergebnisse", required=True); s.add_argument("--aus", required=True)
    s.add_argument("--max-len", type=int, default=9000); s.add_argument("--n-fertig", type=int, default=6)
    s.add_argument("--n-schleife", type=int, default=4)
    b = sub.add_parser("bauen")
    b.add_argument("--basis", required=True); b.add_argument("--richtung", required=True)
    b.add_argument("--sammlung", required=True); b.add_argument("--aus", required=True)
    b.add_argument("--lam", type=float, default=0.05)
    a = ap.parse_args()
    sammeln(a) if a.cmd == "sammeln" else bauen(a)


if __name__ == "__main__":
    main()
