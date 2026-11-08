"""2×2-Trennversuch Wahrheit gegen Behauptung (Argon F7, Nutzer-Go 07.11. ~12:55; nur vorhandene Set-B-Läufe, CPU).
Frage: Liest die eingefrorene Wahrheitssonde (Schicht 13) „ist wahr“ oder „wird behauptet“? An harte Fälle (richtige Kandidaten
im Denken UNTER der 4-%-Schwelle, bevorzugt mit Prüf-Wort davor) werden hinter dem Satzende vier Fortsetzungen gehängt:
  (1) „\\nSo the answer is X_wahr.“  (2) „\\nSo the answer is X_falsch.“
  (3) „\\nLet's check if it is X_wahr.“  (4) „\\nLet's check if it is X_falsch.“
und die Sonde am letzten Token von X gelesen. Kennwerte je Fall:
  ΔWahr = ½[(s1−s2)+(s3−s4)] · ΔBehaupt = ½[(s1−s3)+(s2−s4)] · ΔInter = (s1−s2)−(s3−s4).
Widerlegung der reinen Wahrheits-These (Argon): (2) springt bei > 15 % der Fälle über die 4-%-Schwelle.
Brücken-Potenzial: Anteil der Fälle, in denen (1) die Schwelle erreicht, (2) aber nicht.
  python 63_wahrheit_behauptung.py --n 50 --max-len 3000
"""
import argparse
import collections
import importlib.util
import json
import os
import re

import numpy as np

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(HIER)
ERG = os.path.join(WURZEL, "ergebnisse")
PRUEF = re.compile(r"\b(verify|check|confirm|double[- ]check|indeed|correct|consistent|matches)\b", re.I)


def lade_mod(name, pfad):
    s = importlib.util.spec_from_file_location(name, pfad)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


def norm(c):
    return str(c).replace(" ", "").replace("$", "").replace("\\dfrac", "\\frac").replace("\\tfrac", "\\frac").strip(".").lower()


def stoeren(x):
    """Falsche, aber formgleiche Zahl, wenn keine echte falsche Antwort derselben Aufgabe vorliegt."""
    m = re.fullmatch(r"-?\d+", x.strip())
    if m:
        return str(int(x) + 1)
    m = re.fullmatch(r"\\frac\{(-?\d+)\}\{(\d+)\}", x.strip())
    if m:
        return f"\\frac{{{int(m.group(1)) + 1}}}{{{m.group(2)}}}"
    m = re.fullmatch(r"(-?\d+)/(\d+)", x.strip())
    if m:
        return f"{int(m.group(1)) + 1}/{m.group(2)}"
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=50)
    ap.add_argument("--max-len", type=int, default=3000)
    ap.add_argument("--aus", default=os.path.join(ERG, "wahrheit_behauptung_2x2.json"))
    ap.add_argument("--pro-aufgabe", type=int, default=1, help="höchstens so viele Fälle je Aufgabe (verschiedene Läufe)")
    ap.add_argument("--ueberspringen", default="", help="frühere Ausgabe: deren Fälle (lauf, x_wahr) nicht erneut rechnen")
    ap.add_argument("--geraet", default="cpu", help="cpu oder cuda (07.11.: Erweiterung auf der GPU nach Kettenende)")
    a = ap.parse_args()
    import torch
    import transformers as tf
    torch.set_num_threads(int(os.environ.get("WSP_THREADS", 3)))
    wm = lade_mod("wm", os.path.join(HIER, "42_wahrheitsmelder.py"))
    ev = wm.lade("ev", os.path.join(WURZEL, "eval", "03_eval.py"))
    tok = tf.AutoTokenizer.from_pretrained(os.path.join(WURZEL, "modelle", "Qwen3.5-0.8B"))
    Z = np.load(os.path.join(ERG, "setB_kandidaten.npz"))
    S = np.load(os.path.join(ERG, "wahrheitsmelder_eingefroren.npz"))

    def score(X):
        return float(((np.asarray(X, dtype=np.float64) - S["mu"]) / S["sd"]) @ S["w"] + S["b"])
    sc = ((Z["X_13"].astype(np.float64) - S["mu"]) / S["sd"]) @ S["w"] + S["b"]
    y, lauf, kand, tpos, ber, aufg = Z["y"].astype(bool), Z["lauf"], Z["kand"], Z["tpos"], Z["bereich"], Z["aufgabe"]
    denken = ber == 0
    tau4 = float(np.quantile(sc[denken & ~y], 0.96))
    falsche = collections.defaultdict(collections.Counter)
    for i in np.where(~y)[0]:
        falsche[aufg[i]][str(kand[i])] += 1
    R = {}
    for tag in set(l.split("/")[0] for l in lauf.tolist()):
        for z in open(os.path.join(ERG, tag, "ergebnisse.jsonl"), encoding="utf-8"):
            r = json.loads(z)
            R[f"{tag}/{r['id']}"] = r
    # Kandidaten: hart (unter 4 %), im Denken, richtig, Präfix kurz genug; erst mit Prüf-Wort, je Aufgabe höchstens einer
    kandidaten = []
    for i in np.where(denken & y & (sc < tau4))[0]:
        r = R[lauf[i]]
        if len(r["prompt_ids"]) + int(tpos[i]) + 45 > a.max_len:
            continue
        vor = tok.decode(r["gen_ids"][max(0, int(tpos[i]) - 60):int(tpos[i]) + 1])
        kandidaten.append((not bool(PRUEF.search(vor)), float(sc[i]), i))
    # Reihenfolge: zuerst Fälle mit Prüf-Wort davor, innerhalb der Gruppen zufällig (fester Seed) statt nach Score –
    # sonst kämen nur die extremsten harten Fälle dran.
    zufall = np.random.default_rng(0).permutation(len(kandidaten))
    kandidaten = [kandidaten[j] for j in sorted(range(len(kandidaten)), key=lambda j: (kandidaten[j][0], zufall[j]))]
    gewaehlt, aufgaben = [], collections.Counter()
    schon = set()
    if a.ueberspringen and os.path.exists(a.ueberspringen):
        schon = {(e["lauf"], e["x_wahr"]) for e in json.load(open(a.ueberspringen, encoding="utf-8"))["faelle"]}
    laeufe_gewaehlt = set()
    for pruef_fehlt, s0, i in kandidaten:
        if aufgaben[aufg[i]] >= a.pro_aufgabe or lauf[i] in laeufe_gewaehlt or (str(lauf[i]), str(kand[i]).strip()) in schon:
            continue
        x_w = str(kand[i]).strip()
        x_f = None
        for c, _ in falsche[aufg[i]].most_common():
            if norm(c) != norm(x_w) and not ev.korrekt(c, R[lauf[i]]["gold"]) and len(c) <= 40:
                x_f = c.strip()
                break
        x_f = x_f or stoeren(x_w)
        if not x_f:
            continue
        gewaehlt.append((i, x_w, x_f, not pruef_fehlt))
        aufgaben[aufg[i]] += 1
        laeufe_gewaehlt.add(lauf[i])
        if len(gewaehlt) >= a.n:
            break
    print(f"τ(4 %) = {tau4:+.3f}; harte Fälle mit kurzem Präfix: {len(kandidaten)}; gewählt: {len(gewaehlt)} "
          f"(mit Prüf-Wort davor: {sum(g[3] for g in gewaehlt)})", flush=True)
    speicher = {}
    pfad = os.path.join(WURZEL, "modelle", "Qwen3.5-0.8B")
    model = wm.lesemodell(pfad, a.geraet, [13], speicher)
    ergebnisse = []
    for nr, (i, x_w, x_f, mit_pruef) in enumerate(gewaehlt, 1):
        r = R[lauf[i]]
        gen, t = r["gen_ids"], int(tpos[i])
        ende = t
        for k in range(t + 1, min(len(gen), t + 41)):
            stueck = tok.decode([gen[k]])
            if "\n" in stueck or stueck.rstrip().endswith("."):
                ende = k
                break
        praefix = r["prompt_ids"] + gen[:ende + 1]
        s = {}
        for name, satz, x in (("s1", "\nSo the answer is ", x_w), ("s2", "\nSo the answer is ", x_f),
                              ("s3", "\nLet's check if it is ", x_w), ("s4", "\nLet's check if it is ", x_f)):
            bis_x = tok.encode(satz + x, add_special_tokens=False)
            ids = praefix + bis_x + tok.encode(".", add_special_tokens=False)
            wm.vorwaerts(model, ids, a.geraet, speicher, {}, pfad, [13])
            s[name] = score(speicher[13][len(praefix) + len(bis_x) - 1].numpy())
        d_wahr = 0.5 * ((s["s1"] - s["s2"]) + (s["s3"] - s["s4"]))
        d_beh = 0.5 * ((s["s1"] - s["s3"]) + (s["s2"] - s["s4"]))
        d_int = (s["s1"] - s["s2"]) - (s["s3"] - s["s4"])
        ergebnisse.append({"lauf": str(lauf[i]), "x_wahr": x_w, "x_falsch": x_f, "pruef_davor": mit_pruef,
                           "s0_original": float(sc[i]), **s, "d_wahr": d_wahr, "d_behaupt": d_beh, "d_inter": d_int})
        print(f"{nr:2d}/{len(gewaehlt)} {lauf[i][:44]:44s} s0 {sc[i]:+.2f} | s1 {s['s1']:+.2f} s2 {s['s2']:+.2f} "
              f"s3 {s['s3']:+.2f} s4 {s['s4']:+.2f} | ΔW {d_wahr:+.2f} ΔB {d_beh:+.2f} ΔI {d_int:+.2f}", flush=True)
    E = ergebnisse
    f = lambda k: np.array([e[k] for e in E])  # noqa: E731
    zus = {"n": len(E), "tau4": tau4,
           "d_wahr_mittel": float(f("d_wahr").mean()), "d_wahr_anteil_pos": float((f("d_wahr") > 0).mean()),
           "d_behaupt_mittel": float(f("d_behaupt").mean()), "d_behaupt_anteil_pos": float((f("d_behaupt") > 0).mean()),
           "d_inter_mittel": float(f("d_inter").mean()),
           "anteil_s1_ueber_tau": float((f("s1") >= tau4).mean()), "anteil_s2_ueber_tau": float((f("s2") >= tau4).mean()),
           "anteil_s3_ueber_tau": float((f("s3") >= tau4).mean()), "anteil_s4_ueber_tau": float((f("s4") >= tau4).mean()),
           "bruecke_sicher": float(((f("s1") >= tau4) & (f("s2") < tau4)).mean())}
    print(json.dumps(zus, indent=1), flush=True)
    print(f"URTEIL (Argon-Kriterium): Behauptung schiebt FALSCHE über die Schwelle bei {100 * zus['anteil_s2_ueber_tau']:.0f} % "
          f"(Grenze 15 %) → {'Sonde liest vor allem BEHAUPTUNG' if zus['anteil_s2_ueber_tau'] > 0.15 else 'Wahrheits-These hält'}")
    json.dump({"zusammenfassung": zus, "faelle": E}, open(a.aus, "w", encoding="utf-8"), indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
