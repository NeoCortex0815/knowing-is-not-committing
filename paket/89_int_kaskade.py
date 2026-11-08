"""INT-Kaskade (08.11.; Nutzer: „INT: gerne versuchen, da etwas zu bauen“; „Wenn INT wahr, dann kein Thinking nötig?“).
Die Frage vorher am Prompt-Ende war widerlegt (N3). Hier wird die Wahrheit NACH der INT-Antwort gelesen.
Teil A (GPU, --sonde): Die eingefrorene L13-Wahrheitssonde (wie Ehrlichkeit Schritt 1) wird am Ende der Antwort jedes Laufs OHNE
  Denken gelesen, am letzten Token des letzten \\boxed{…}. Ergebnis: ergebnisse/int_sonde.jsonl (fortsetzbar).
Teil B (CPU, Standard): Kaskade je Aufgabe:
  1) INT antwortet (ohne Denken). Liegt die Sonde über der Schwelle, wird abgegeben.
  2) Sonst zweite Chance: die Antwort aus dem Denklauf von Modell X. Offizielle oder erzwungene Antwort; ihr Sondenwert stammt aus
     Ehrlichkeit Schritt 1. Liegt er über der Schwelle, wird abgegeben.
  3) Sonst „weiß ich nicht“.
  Verglichen mit: INT allein, INT + Harnisch, X allein, X + Zwang + Harnisch (Ehrlichkeit Schritt 1).
  Kennzahlen: richtig / falsch / enthalten, S₂ = (richtig − 2·falsch)/N, Tokens (INT immer, X nur wenn gebraucht).
NACHTRÄGLICH, beschreibend; Sonde und Schwelle eingefroren (06.11.), keine Anpassung.
  python 89_int_kaskade.py --sonde [--geraet cuda]   → Teil A
  python 89_int_kaskade.py                            → Teil B (ergebnisse/int_kaskade.json)
"""
import argparse
import collections
import importlib.util
import json
import os

import numpy as np

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(HIER)
ERG = os.path.join(WURZEL, "ergebnisse")
AUS = os.path.join(ERG, "int_sonde.jsonl")
SAETZE = {
    "Set B": {"int": ["setB60-ohne-eigen-t06"],
              "x": {"eigen": "Set B · eigen", "WT-A": "Set B · WT-A", "ERGORE": "Set B · ERGORE 0,6"}},
    "1–160": {"int": ["m500-001-080-ohne-eigen-t06", "m500-081-160-ohne-eigen-t06"],
              "x": {"MIT": "1–160 · MIT", "ERGORE": "1–160 · ERGORE"}},
    "161–300": {"int": ["s3-int-eigen-161-210", "s3-int-eigen-211-260", "s3-int-eigen-261-300"],
                "x": {"MIT": "161–300 · MIT", "ERGORE": "161–300 · ERGORE", "WT-A": "161–300 · WT-A"}},
}


def lade_mod(name, pfad):
    s = importlib.util.spec_from_file_location(name, pfad)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


def laufe(dirs):
    R = {}
    for d in dirs:
        p = os.path.join(ERG, d, "ergebnisse.jsonl")
        if os.path.exists(p):
            for z in open(p, encoding="utf-8"):
                r = json.loads(z)
                R[r["id"]] = r
    return R


def teil_a(a):
    S = np.load(os.path.join(ERG, "wahrheitsmelder_eingefroren.npz"))
    L = int(S["schicht"])
    wm = lade_mod("wm", os.path.join(HIER, "42_wahrheitsmelder.py"))
    import transformers as tf
    tok = tf.AutoTokenizer.from_pretrained(os.path.join(WURZEL, "modelle", "Qwen3.5-0.8B"))
    fertig = {json.loads(z)["lauf"] for z in open(AUS, encoding="utf-8")} if os.path.exists(AUS) else set()
    speicher, model, notfall = {}, None, {"cpu": None, "probe": False}
    pfad = os.path.join(WURZEL, "modelle", "Qwen3.5-0.8B-eigen-vL")

    def wert(h):
        return float(((h.astype(np.float64) - S["mu"]) / S["sd"]) @ S["w"] + S["b"])
    with open(AUS, "a", encoding="utf-8") as fo:
        for satz, cfg in SAETZE.items():
            for d in cfg["int"]:
                p = os.path.join(ERG, d, "ergebnisse.jsonl")
                if not os.path.exists(p):
                    print(f"FEHLT (noch): {d}", flush=True)
                    continue
                for z in open(p, encoding="utf-8"):
                    r = json.loads(z)
                    lauf = f"{d}/{r['id']}"
                    if lauf in fertig:
                        continue
                    st = [tok.decode([t]) for t in r["gen_ids"]]
                    text = "".join(st)
                    boxed = [(s0, e) for s0, e, _ in wm.kandidaten_mit_ende(text) if text.startswith("\\boxed{", s0)]
                    rec = {"satz": satz, "lauf": lauf, "id": r["id"], "korrekt": bool(r["korrekt"]), "tokens": r["tokens"],
                           "antwort": bool(boxed)}
                    if boxed:
                        gr = np.cumsum([len(s) for s in st])
                        ti = min(int(np.searchsorted(gr, boxed[-1][1] - 1, side="right")), len(st) - 1)
                        ids = r["prompt_ids"] + r["gen_ids"][:ti + 1]
                        if model is None:
                            model = wm.lesemodell(pfad, a.geraet, [L], speicher)
                        rec["geraet"] = wm.vorwaerts(model, ids, a.geraet, speicher, notfall, pfad, [L])
                        rec["wert"] = wert(speicher[L][len(ids) - 1].numpy())
                    fo.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    fo.flush()
                    fertig.add(lauf)
                print(f"{satz} {d}: fertig", flush=True)


def kennzahlen(liste):
    """liste von (art, tokens): art ∈ richtig / falsch / enthalten"""
    n = len(liste)
    r = sum(1 for x in liste if x[0] == "richtig")
    f = sum(1 for x in liste if x[0] == "falsch")
    return {"n": n, "richtig": r, "falsch": f, "enthalten": n - r - f, "S2": (r - 2 * f) / max(1, n),
            "tokens_mittel": round(sum(x[1] for x in liste) / max(1, n))}


def teil_b():
    """Kaskade (N9). Varianten: F = feste Schwelle (eingefroren) für INT- und Denk-Antworten; K = auf 1–160 geeicht (S₂-Maximum),
    blind auf die übrigen Sätze angewandt. „streng“: INT zählt nur bei regulärem Ende (eos), sonst Rückgriff."""
    S = np.load(os.path.join(ERG, "wahrheitsmelder_eingefroren.npz"))
    thr = float(S["thr"])
    I, ende = {}, {}
    for z in open(AUS, encoding="utf-8"):
        e = json.loads(z)
        I[(e["satz"], e["id"])] = e
    for satz, cfg in SAETZE.items():
        for i, r in laufe(cfg["int"]).items():
            ende[(satz, i)] = r["ende"]
    H = {}
    for z in open(os.path.join(ERG, "ehrlichkeit_schritt1.jsonl"), encoding="utf-8"):
        e = json.loads(z)
        H[(e["satz"], e["id"])] = e
    tok_cache = {}

    def x_daten(satz, xn):
        xs = SAETZE[satz]["x"][xn]
        Rx = {i: e for (s, i), e in H.items() if s == xs}
        for e in Rx.values():
            d = e["lauf"].split("/")[0]
            if d not in tok_cache:
                tok_cache[d] = laufe([d])
        return Rx

    def x_art(Rx, i, harnisch, tau):
        e = Rx.get(i)
        if e is None:
            return "enthalten", 0
        t = tok_cache[e["lauf"].split("/")[0]][i]["tokens"]
        if not harnisch:
            return ("enthalten" if not e["pred_offiziell"] else ("richtig" if e["korrekt_offiziell"] else "falsch")), t
        if e["art"] == "keine" or e.get("wert") is None or e["wert"] < tau:
            return "enthalten", t
        return ("richtig" if e["korrekt"] else "falsch"), t

    def int_ok(satz, i, tau, streng):
        e = I[(satz, i)]
        return e["antwort"] and e["wert"] >= tau and (not streng or ende.get((satz, i)) == "eos")

    def ids_von(satz):
        return sorted(i for (s, i) in I if s == satz)

    gitter = np.round(np.linspace(-6, 4, 201), 3)
    tau_int_k, tau_denk_k = thr, thr
    if ids_von("1–160"):
        def s2_int(tau):
            L_ = [("richtig" if I[("1–160", i)]["korrekt"] else "falsch") if int_ok("1–160", i, tau, False) else "enthalten"
                  for i in ids_von("1–160")]
            return (L_.count("richtig") - 2 * L_.count("falsch")) / len(L_)
        tau_int_k = float(max(gitter, key=s2_int))
        Rm = x_daten("1–160", "MIT")

        def s2_denk(tau):
            L_ = [x_art(Rm, i, True, tau)[0] for i in Rm]
            return (L_.count("richtig") - 2 * L_.count("falsch")) / max(1, len(L_))
        tau_denk_k = float(max(gitter, key=s2_denk))
    print(f"Schwellen: F (eingefroren) {thr:.3f} | K (auf 1–160 geeicht) INT {tau_int_k:.3f}, Denken (MIT) {tau_denk_k:.3f}")
    B = {"schwelle_F": thr, "schwelle_K_int": tau_int_k, "schwelle_K_denken": tau_denk_k}
    for satz, cfg in SAETZE.items():
        ids = ids_von(satz)
        if not ids:
            print(f"\n== {satz}: noch keine INT-Sondenwerte")
            continue
        mit_a = [I[(satz, i)] for i in ids if I[(satz, i)]["antwort"]]
        ra = [e["wert"] for e in mit_a if e["korrekt"]]
        fa = [e["wert"] for e in mit_a if not e["korrekt"]]
        auc = None
        if ra and fa:
            alle = np.concatenate([ra, fa])
            rang = alle.argsort().argsort() + 1.0
            auc = float((rang[:len(ra)].sum() - len(ra) * (len(ra) + 1) / 2) / (len(ra) * len(fa)))
        n_ok = sum(I[(satz, i)]["korrekt"] for i in ids)
        n_ok_eos = sum(1 for i in ids if I[(satz, i)]["korrekt"] and ende.get((satz, i)) == "eos")
        vb = "" if auc is None else (" (Vorbedingung ≥ 0,75 erfüllt)" if auc >= 0.75 else " (Vorbedingung NICHT erfüllt)")
        print(f"\n== {satz}: {len(ids)} Aufgaben | INT richtig {n_ok} (streng, nur reguläres Ende: {n_ok_eos}) | INT-Antworten "
              f"{len(mit_a)} | Sonde AUC richtig/falsch {auc if auc is None else round(auc, 3)}{vb}")
        B[satz] = {"auc_int": auc, "int_richtig": n_ok, "int_richtig_streng": n_ok_eos, "varianten": {}, "zweige": {}}
        V = {}
        for var, ti in (("F", thr), ("K", tau_int_k)):
            V[f"INT + Harnisch [{var}]"] = [
                (("richtig" if I[(satz, i)]["korrekt"] else "falsch") if int_ok(satz, i, ti, False) else "enthalten", I[(satz, i)]["tokens"])
                for i in ids]
        V["INT allein (offiziell)"] = [
            (("richtig" if I[(satz, i)]["korrekt"] else "falsch") if I[(satz, i)]["antwort"] else "enthalten", I[(satz, i)]["tokens"])
            for i in ids]
        for xn in cfg["x"]:
            Rx = x_daten(satz, xn)
            gem = [i for i in ids if i in Rx]
            V[f"{xn} allein (offiziell)"] = [x_art(Rx, i, False, thr) for i in gem]
            V[f"{xn} + Zwang + Harnisch [F]"] = [x_art(Rx, i, True, thr) for i in gem]
            for var, ti, td in (("F", thr, thr), ("K", tau_int_k, tau_denk_k)):
                for streng in (False, True):
                    kas, matrix = [], collections.Counter()
                    for i in gem:
                        e = I[(satz, i)]
                        if int_ok(satz, i, ti, streng):
                            a_ = "richtig" if e["korrekt"] else "falsch"
                            kas.append((a_, e["tokens"]))
                            matrix[("INT", a_)] += 1
                        else:
                            a_, t_ = x_art(Rx, i, True, td)
                            kas.append((a_, e["tokens"] + t_))
                            matrix[("Denken" if a_ != "enthalten" else "weiß nicht", a_)] += 1
                    name = f"Kaskade INT → {xn} → weiß nicht [{var}{', streng' if streng else ''}]"
                    V[name] = kas
                    B[satz]["zweige"][name] = {f"{k[0]}/{k[1]}": v for k, v in matrix.items()}
        for name, liste in V.items():
            k = kennzahlen(liste)
            B[satz]["varianten"][name] = k
            print(f"   {name:46s}: n {k['n']:3d} | richtig {k['richtig']:3d} | falsch {k['falsch']:3d} | enthalten {k['enthalten']:3d} | "
                  f"S₂ {k['S2']:+.3f} | Ø Tokens {k['tokens_mittel']}")
        haupt = "Kaskade INT → MIT → weiß nicht [K, streng]"
        if satz == "161–300" and haupt in B[satz]["varianten"]:
            k = B[satz]["varianten"][haupt]
            vor = auc is not None and auc >= 0.75
            urteil = ("bestätigt" if k["S2"] >= 0.25 and k["richtig"] >= 75 else
                      "widerlegt" if k["S2"] <= 0.19 or k["richtig"] < 75 else "offen")
            print(f"\nURTEIL N9 (vorab): {haupt}: S₂ {k['S2']:+.3f}, richtig {k['richtig']} → {urteil.upper()}"
                  f"{'' if vor else ' – nur beschreibend, Vorbedingung AUC ≥ 0,75 nicht erfüllt'} | Zweige: {B[satz]['zweige'][haupt]}")
            B["urteil_N9"] = {"variante": haupt, "S2": k["S2"], "richtig": k["richtig"], "urteil": urteil, "vorbedingung": vor}
    json.dump(B, open(os.path.join(ERG, "int_kaskade.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(f"\ngespeichert: {os.path.join(ERG, 'int_kaskade.json')}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sonde", action="store_true")
    ap.add_argument("--geraet", default="cuda")
    a = ap.parse_args()
    if a.sonde:
        teil_a(a)
    teil_b()


if __name__ == "__main__":
    main()
