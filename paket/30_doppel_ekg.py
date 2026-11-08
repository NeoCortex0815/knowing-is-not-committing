"""Doppel-EKG (Einwand Nutzer 06.11.): innen (Klingel-/Entschluss-Achse, Schicht 19) vs. außen (Abschluss-Impuls p(</think>))
auf denselben Denktexten (Aufzeichnung 28_faire_klingel). CPU. Welche inneren Ausschläge kommen oben an, welche verpuffen?"""
import argparse, json, os
import numpy as np
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--modell", required=True); ap.add_argument("--achse", required=True); ap.add_argument("--auf", required=True)
    ap.add_argument("--schicht", type=int, default=19); ap.add_argument("--aus", required=True); ap.add_argument("--glaetten", type=int, default=64)
    a = ap.parse_args()
    import torch, transformers as tf, matplotlib
    matplotlib.use("Agg"); import matplotlib.pyplot as plt
    tok = tf.AutoTokenizer.from_pretrained(a.modell)
    u = np.load(a.achse)[f"u_{a.schicht}"].astype(np.float32); u = torch.tensor(u / np.linalg.norm(u))
    rs = [json.loads(z) for z in open(os.path.join(a.auf, "aufzeichnung.jsonl"), encoding="utf-8")]
    fertig = [r for r in rs if r["zu_bei"] is not None]; offen = sorted([r for r in rs if r["zu_bei"] is None], key=lambda r: -max(r["p_zu"]))
    faelle = [("schließt ab", fertig[0])] if fertig else []
    faelle += [("bleibt stecken (höchster Oberflächen-Impuls)", offen[0]), ("bleibt stecken (typisch)", offen[len(offen) // 2])]
    ids0 = None
    model = (getattr(tf, "AutoModelForImageTextToText", None) or tf.AutoModelForCausalLM).from_pretrained(a.modell, dtype=torch.float32).eval()
    fig, axs = plt.subplots(len(faelle), 1, figsize=(11, 3.2 * len(faelle)))
    ev_pre = "<|im_start|>user\n"
    for ax, (name, r) in zip(np.atleast_1d(axs), faelle):
        row_prompt = None
        gen = r["gen_ids"]
        # Prompt rekonstruieren wie in 28: PREFIX + Aufgabe + SUFFIX – hier aus Text nicht verfügbar -> nur Antwortteil messen ist zu ungenau;
        # daher Prompt-IDs aus den Übungsdaten neu bauen
        ax.set_title(name + " · " + r["id"], fontsize=9)
        faelle_prompt = json.load(open(os.path.join(a.auf, "prompts.json"), encoding="utf-8"))[r["id"]]
        with torch.no_grad():
            h = model(input_ids=torch.tensor([faelle_prompt + gen]), output_hidden_states=True).hidden_states[a.schicht + 1][0, len(faelle_prompt):]
        c = (h @ u / h.norm(dim=-1)).numpy(); cg = np.convolve(c, np.ones(a.glaetten) / a.glaetten, mode="same")
        ax.plot(cg, color="#1d4ed8", lw=1.1, label="innen: Entschluss-Achse (Schicht 19)")
        ax.set_ylabel("innen", fontsize=8); ax.axhline(0, color="#9ca3af", lw=0.6)
        ax2 = ax.twinx(); ax2.plot(r["p_zu"], color="#dc2626", lw=0.8, alpha=0.8, label="außen: p(</think>)")
        ax2.set_ylim(0, max(0.05, max(r["p_zu"]) * 1.1)); ax2.set_ylabel("außen p(</think>)", fontsize=8, color="#dc2626")
        if r["zu_bei"] is not None: ax.axvline(r["zu_bei"], color="#111827", lw=2)
        ax.legend(loc="upper left", fontsize=7); ax2.legend(loc="upper right", fontsize=7)
        print(name, r["id"], "max innen", round(float(cg.max()), 3), "max außen", max(r["p_zu"]), flush=True)
    np.atleast_1d(axs)[-1].set_xlabel("Token im Denken")
    fig.suptitle("Doppel-EKG: innerer Entschluss (blau) vs. Abschluss-Impuls an der Oberfläche (rot)", fontsize=10); fig.tight_layout(); fig.savefig(a.aus, dpi=130)
    print("Grafik:", a.aus)
if __name__ == "__main__":
    main()
