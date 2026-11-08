"""EKG-Statistik (Umkehr-Messung des Nutzers „die Hand wird innerlich, die Wirkung äußerlich“):
Sagen Zuck-Spitzen der Klingel-Achse den Abschluss voraus? Haben Steckenbleiber nach τy weniger Spitzen?
Je Denktext (Übungsaufgaben, CPU): cos(Residual Schicht L, u_Klingel), geglättet (64); Spitze = Wert > Schwelle
(Schwelle = Perzentil --perz über alle Texte). Kennzahlen: Spitzen je 1.000 Tokens nach τy; bei Abschluss: höchster Wert
in den letzten --fenster Tokens vor </think> vs. in zufälligen Fenstern gleicher Länge davor.
"""
import argparse, importlib.util, json, os, random
import numpy as np
HIER = os.path.dirname(os.path.abspath(__file__))
def lade(n, d):
    s = importlib.util.spec_from_file_location(n, os.path.join(HIER, d)); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--modell", required=True); ap.add_argument("--achse", required=True); ap.add_argument("--schicht", type=int, default=19)
    ap.add_argument("--ergebnisse", required=True); ap.add_argument("--n", type=int, default=30); ap.add_argument("--max-len", type=int, default=6144)
    ap.add_argument("--glaetten", type=int, default=64); ap.add_argument("--fenster", type=int, default=300); ap.add_argument("--perz", type=float, default=95)
    ap.add_argument("--aus", required=True)
    a = ap.parse_args()
    import torch, transformers as tf
    am = lade("am", "22_angstmarker.py")
    tok = tf.AutoTokenizer.from_pretrained(a.modell)
    u = np.load(a.achse)[f"u_{a.schicht}"].astype(np.float32); u = torch.tensor(u / np.linalg.norm(u))
    zu = tok.convert_tokens_to_ids("</think>")
    rs = [json.loads(z) for z in open(a.ergebnisse, encoding="utf-8")][:a.n]
    cls = getattr(tf, "AutoModelForImageTextToText", None) or tf.AutoModelForCausalLM
    model = cls.from_pretrained(a.modell, dtype=torch.float32).eval()
    reihen = []
    for r in rs:
        gen = r["gen_ids"][:a.max_len]
        with torch.no_grad():
            h = model(input_ids=torch.tensor([r["prompt_ids"] + gen]), output_hidden_states=True).hidden_states[a.schicht + 1][0, len(r["prompt_ids"]):]
        c = (h @ u / h.norm(dim=-1)).numpy()
        cg = np.convolve(c, np.ones(a.glaetten) / a.glaetten, mode="same")
        stuecke = [tok.decode([t]) for t in gen]; text = "".join(stuecke); p = am.tau(text.split("</think>")[0], r.get("gold"))
        tau = None
        if p is not None:
            acc = 0
            for i, s in enumerate(stuecke):
                acc += len(s)
                if acc >= p: tau = i; break
        reihen.append({"id": r["id"], "cg": cg, "tau": tau, "ende": gen.index(zu) if zu in gen else None, "korrekt": bool(r.get("korrekt"))})
        print(r["id"], "fertig" if reihen[-1]["ende"] is not None else "offen", "tau", tau, flush=True)
    schwelle = np.percentile(np.concatenate([x["cg"] for x in reihen]), a.perz)
    def spitzen(cg):  # Anzahl Überschreitungen (Anstiege über die Schwelle)
        ueber = cg > schwelle
        return int(np.sum(ueber[1:] & ~ueber[:-1]))
    erg = {"schwelle": float(schwelle), "gruppen": {}}
    for name, filt in (("abgeschlossen", lambda x: x["ende"] is not None), ("nicht abgeschlossen", lambda x: x["ende"] is None)):
        g = [x for x in reihen if filt(x)]
        mit_tau = [x for x in g if x["tau"] is not None]
        rate_nach = [1000 * spitzen(x["cg"][x["tau"]:(x["ende"] or len(x["cg"]))]) / max((x["ende"] or len(x["cg"])) - x["tau"], 1) for x in mit_tau]
        rate_ges = [1000 * spitzen(x["cg"][:(x["ende"] or len(x["cg"]))]) / max(x["ende"] or len(x["cg"]), 1) for x in g]
        erg["gruppen"][name] = {"n": len(g), "n_mit_tau": len(mit_tau), "spitzen_je_1000_nach_tau": round(float(np.median(rate_nach)), 2) if rate_nach else None,
                                "spitzen_je_1000_gesamt": round(float(np.median(rate_ges)), 2) if rate_ges else None,
                                "mittel_achse": round(float(np.mean([x["cg"].mean() for x in g])), 4) if g else None}
    rng = random.Random(0); vor_ende, zufall = [], []
    for x in reihen:
        e = x["ende"]
        if e is None or e < 3 * a.fenster: continue
        vor_ende.append(float(x["cg"][e - a.fenster:e].max()))
        s = rng.randint(0, e - 2 * a.fenster); zufall.append(float(x["cg"][s:s + a.fenster].max()))
    if vor_ende:
        gewinnt = np.mean([v > z for v, z in zip(vor_ende, zufall)])
        erg["vor_abschluss"] = {"n": len(vor_ende), "max_letzte_fenster": round(float(np.median(vor_ende)), 4),
                                "max_zufallsfenster": round(float(np.median(zufall)), 4), "anteil_hoeher_als_zufall": round(float(gewinnt), 3)}
    json.dump(erg, open(a.aus, "w"), indent=1); print(json.dumps(erg, indent=1, ensure_ascii=False))
if __name__ == "__main__":
    main()
