"""Messgerät „Entschluss vs. Zweifel“: Verlauf der Klingel-Achse über einen Denktext (wie ein EKG).

Je Token: cos(Residual-Ausgang von Schicht L, u_Klingel_L) – positiv = „folglich / nicht nötig“, negativ = „ist es wirklich so?“.
Markiert: τy (richtige Lösung erstmals im Denken), „Wait“-Tokens, </think>. Läuft auf der CPU (stört die Nachtkette nicht).
  python 25_achse_verlauf.py --modell modelle/Qwen3.5-0.8B --achse ergebnisse/richtung-klingel.npz --schicht 19 \
      --ergebnisse ergebnisse/entschluss-uebung-eigen/ergebnisse.jsonl --aus ergebnisse/achse_verlauf.png
"""
import argparse
import importlib.util
import json
import os

import numpy as np

HIER = os.path.dirname(os.path.abspath(__file__))


def lade(name, datei):
    spec = importlib.util.spec_from_file_location(name, os.path.join(HIER, datei))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--modell", required=True)
    ap.add_argument("--achse", required=True)
    ap.add_argument("--schicht", type=int, default=19)
    ap.add_argument("--ergebnisse", required=True)
    ap.add_argument("--max-len", type=int, default=6144)
    ap.add_argument("--glaetten", type=int, default=64)
    ap.add_argument("--aus", required=True)
    a = ap.parse_args()
    import torch
    import transformers as tf
    am = lade("am", "22_angstmarker.py")
    tok = tf.AutoTokenizer.from_pretrained(a.modell)
    u = np.load(a.achse)[f"u_{a.schicht}"].astype(np.float32)
    u = torch.tensor(u / np.linalg.norm(u))
    rs = [json.loads(z) for z in open(a.ergebnisse, encoding="utf-8")]
    zu = tok.convert_tokens_to_ids("</think>")

    def tau_tok(r):
        gen = r["gen_ids"][:a.max_len]
        stuecke = [tok.decode([t]) for t in gen]
        text = "".join(stuecke)
        denk = text.split("</think>")[0]
        p = am.tau(denk, r.get("gold"))
        if p is None:
            return None, stuecke
        acc = 0
        for i, s in enumerate(stuecke):
            acc += len(s)
            if acc >= p:
                return i, stuecke
        return None, stuecke

    # drei Fälle auswählen
    faelle = {}
    for r in rs:
        t, _ = tau_tok(r)
        if "fertig, richtig" not in faelle and r["ende"] == "eos" and r.get("korrekt") and zu in r["gen_ids"][:a.max_len]:
            faelle["fertig, richtig"] = r
        elif "verhaspelt (Lösung früh, kein Abschluss)" not in faelle and r["ende"] != "eos" and t is not None and t < 1500:
            faelle["verhaspelt (Lösung früh, kein Abschluss)"] = r
        elif "weiß es nicht (Lösung taucht nie auf)" not in faelle and r["ende"] != "eos" and t is None:
            faelle["weiß es nicht (Lösung taucht nie auf)"] = r
        if len(faelle) == 3:
            break

    cls = getattr(tf, "AutoModelForImageTextToText", None) or tf.AutoModelForCausalLM
    try:
        model = cls.from_pretrained(a.modell, dtype=torch.float32)
    except Exception:  # noqa: BLE001
        model = tf.AutoModelForCausalLM.from_pretrained(a.modell, dtype=torch.float32)
    model.eval()
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axs = plt.subplots(len(faelle), 1, figsize=(11, 3.1 * len(faelle)), sharey=True)
    axs = np.atleast_1d(axs)
    zusammen = {}
    for ax, (name, r) in zip(axs, faelle.items()):
        gen = r["gen_ids"][:a.max_len]
        ids = torch.tensor([r["prompt_ids"] + gen])
        with torch.no_grad():
            out = model(input_ids=ids, output_hidden_states=True)
        h = out.hidden_states[a.schicht + 1][0, len(r["prompt_ids"]):].float()  # Residual NACH Schicht L
        c = (h @ u / h.norm(dim=-1)).numpy()
        k = np.ones(a.glaetten) / a.glaetten
        cg = np.convolve(c, k, mode="same")
        t, stuecke = tau_tok(r)
        waits = [i for i, s in enumerate(stuecke) if "wait" in s.lower()]
        ende = gen.index(zu) if zu in gen else None
        ax.plot(cg, lw=1.2, color="#1d4ed8")
        ax.axhline(0, color="#9ca3af", lw=0.8)
        for w in waits:
            ax.axvline(w, color="#ef4444", lw=0.4, alpha=0.5)
        if t is not None:
            ax.axvline(t, color="#059669", lw=2, label="Lösung erstmals im Denken (τy)")
        if ende is not None:
            ax.axvline(ende, color="#111827", lw=2, label="</think> (Abschluss)")
        ax.set_title(f"{name} · {r['id']} · Ende: {r['ende']} · richtig: {bool(r.get('korrekt'))} · rote Linien = „Wait“", fontsize=9)
        ax.set_ylabel("Achse\n+ folglich / − zweifelnd", fontsize=8)
        ax.legend(fontsize=7, loc="lower right")
        vor = c[:t].mean() if t else c.mean()
        nach = c[t:].mean() if t else float("nan")
        zusammen[name] = {"id": r["id"], "tau": t, "waits": len(waits), "ende": ende, "mittel_vor": round(float(vor), 4),
                          "mittel_nach": round(float(nach), 4), "letzte_256": round(float(c[-256:].mean()), 4)}
        print(name, zusammen[name], flush=True)
    axs[-1].set_xlabel("Token im Denken")
    fig.suptitle(f"Messgerät „Entschluss vs. Zweifel“ – Klingel-Achse, Schicht {a.schicht}, Qwen3.5-0.8B (Basis) auf Denktexten unserer Reparatur", fontsize=10)
    fig.tight_layout()
    fig.savefig(a.aus, dpi=130)
    json.dump(zusammen, open(os.path.splitext(a.aus)[0] + ".json", "w"), indent=1)
    print("Grafik:", a.aus)


if __name__ == "__main__":
    main()
