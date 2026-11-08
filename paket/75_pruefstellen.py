"""Pflicht-Prüfstellen 3–5 nach Argon (07.11. abends; Nutzer: „ein extra Werkzeug basteln und bei dir testen, ohne Laptop und
MiniPC zu gefährden“) – reine CPU-Messung auf VORHANDENEN Läufen, keine Generierung, keine neuen Aufgaben.
Gemessen wird p(`</think>` als nächstes Token) an empfindlichen Stellen, für jedes Modell auf DENSELBEN Texten (Teacher-Forcing):
  P0  Gültigkeitsprobe: Stelle direkt vor dem ersten `</think>` des Quell-Laufs (dort hat das Quell-Modell geschlossen)
  P3  Satzende nach verworfener Probe im Denken („… which is impossible.“, „… is not a digit.“)
  P4z Zwischenergebnis im Denken: Wert-Aussage („= 12.“, „is 7.“), Wert ≠ gold        → soll NICHT schließen
  P4r Ergebnis im Denken: Wert-Aussage mit Wert = gold                                → hier DARF/SOLL WT schließen
  P5  Antwortteil (nach dem ersten `</think>`): Wert-Aussagen und Satzenden          → ein zweites `</think>` ist ein Fehler
Je Lauf ein Vorwärtslauf bis zur letzten gewählten Stelle (höchstens --max-tokens), Logits nur an den gewählten Stellen.
  python 75_pruefstellen.py --modelle eigen=Qwen3.5-0.8B-eigen-vL WT-A=Qwen3.5-0.8B-ergo-zigA \
      --quellen setB30-eigen-t06 setB30-wta-t06 --max-laeufe 12 --je-klasse 6 --max-tokens 6000
"""
import argparse
import importlib.util
import json
import os
import re

import numpy as np

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(HIER)
ERG = os.path.join(WURZEL, "ergebnisse")
VERWORFEN = re.compile(r"\b(impossible|not possible|contradiction|doesn't work|does not work|doesn't satisfy|does not satisfy|"
                       r"not valid|invalid|not an integer|not a digit|not prime|can't be|cannot be|no solution|incorrect|wrong|"
                       r"not equal|isn't|is not)\b", re.I)
WERT = re.compile(r"(?:=|\bis\b|\bare\b)\s*\$?\s*(-?[\d][\d,./\\{}a-z^+\-]*?|\\frac\{[^}]+\}\{[^}]+\})\s*\$?\s*(?=[.,;:]\s|[.,;:]?$|\$|\n)")


def lade_mod(name, pfad):
    s = importlib.util.spec_from_file_location(name, pfad)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


def stellen(r, tok, ev, zu_id, je_klasse, max_tokens):
    """Liefert {klasse: [Token-Index im erzeugten Teil]} für einen Lauf."""
    g = r["gen_ids"][:max_tokens]
    st = [tok.decode([t]) for t in g]
    gr = np.cumsum([len(s) for s in st])
    text = "".join(st)
    zu_tok = g.index(zu_id) if zu_id in g else len(g)
    zu_c = int(gr[zu_tok - 1]) if 0 < zu_tok <= len(g) else 0
    def tok_von(c):  # Token, das das Zeichen c enthält
        return min(int(np.searchsorted(gr, c, side="right")), len(st) - 1)
    K = {"P0": [], "P3": [], "P4z": [], "P4r": [], "P5": []}
    if 0 < zu_tok < len(g):  # Gültigkeitsprobe: die Stelle direkt vor dem ersten </think> des Laufs (dort wurde geschlossen)
        K["P0"].append(zu_tok - 1)
    # Satzenden (Punkt gefolgt von Leerraum/Zeilenende)
    satz_start = 0
    for m in re.finditer(r"\.(?=\s|$)", text):
        c = m.start()
        satz = text[satz_start:c]
        satz_start = c + 1
        t = tok_von(c)
        if c < zu_c and VERWORFEN.search(satz):
            K["P3"].append(t)
        elif c > zu_c + 8 and zu_tok < len(g):
            K["P5"].append(t)
    for m in WERT.finditer(text):
        c = m.end(1) - 1
        t = tok_von(c)
        if c < zu_c:
            ok = bool(ev.korrekt(m.group(1).strip().rstrip(".,"), r["gold"]))
            K["P4r" if ok else "P4z"].append(t)
        elif c > zu_c + 8 and zu_tok < len(g):
            K["P5"].append(t)
    out = {}
    for k, v in K.items():
        v = sorted(set(v))
        if len(v) > je_klasse:  # gleichmäßig über den Lauf verteilt
            v = [v[int(i)] for i in np.linspace(0, len(v) - 1, je_klasse)]
        out[k] = v
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--modelle", nargs="+", required=True)
    ap.add_argument("--quellen", nargs="+", required=True, help="Ordner unter ergebnisse/ (Texte als Kontext)")
    ap.add_argument("--max-laeufe", type=int, default=12, help="je Quelle")
    ap.add_argument("--je-klasse", type=int, default=6)
    ap.add_argument("--max-tokens", type=int, default=6000)
    ap.add_argument("--aus", default=os.path.join(ERG, "pruefstellen_3_5.json"))
    a = ap.parse_args()
    import torch
    import transformers as tf
    torch.set_num_threads(int(os.environ.get("WSP_THREADS", 3)))
    ev = lade_mod("ev", os.path.join(WURZEL, "eval", "03_eval.py"))
    tok = tf.AutoTokenizer.from_pretrained(os.path.join(WURZEL, "modelle", "Qwen3.5-0.8B"))
    ZU = tok.convert_tokens_to_ids("</think>")
    # Stellen einmal festlegen (gleiche Texte für alle Modelle)
    F = []
    for q in a.quellen:
        R = [json.loads(z) for z in open(os.path.join(ERG, q, "ergebnisse.jsonl"), encoding="utf-8")]
        R = sorted(R, key=lambda r: r["id"])[:a.max_laeufe]
        for r in R:
            S = stellen(r, tok, ev, ZU, a.je_klasse, a.max_tokens)
            if any(S.values()):
                F.append((q, r, S))
    n_kl = {k: sum(len(S[k]) for _, _, S in F) for k in ("P0", "P3", "P4z", "P4r", "P5")}
    print(f"{len(F)} Läufe, Stellen je Klasse: {n_kl}", flush=True)
    cls = getattr(tf, "AutoModelForImageTextToText", None) or tf.AutoModelForCausalLM
    erg = {"stellen": n_kl, "modelle": {}}
    roh = {}
    for spec in a.modelle:
        name, ordner = spec.split("=", 1)
        model = cls.from_pretrained(os.path.join(WURZEL, "modelle", ordner), dtype=torch.float32).eval()
        head = model.get_output_embeddings()
        norm = None
        for n_, m_ in model.named_modules():
            if re.search(r"(language_model|model)\.norm$", n_) and "visual" not in n_:
                norm = m_
        P = {k: [] for k in n_kl}
        geprueft = False
        for q, r, S in F:
            letzte = max(t for v in S.values() for t in v)
            ids = r["prompt_ids"] + r["gen_ids"][:letzte + 1]
            p0 = len(r["prompt_ids"])
            with torch.no_grad():
                out = model(input_ids=torch.tensor([ids]), output_hidden_states=True, logits_to_keep=1)
                h = out.hidden_states[-1][0]
                if not geprueft:  # Ist hidden_states[-1] schon normiert? Abgleich mit den echten Logits der letzten Stelle
                    l_roh = head(h[-1:]).float()
                    if not torch.allclose(l_roh, out.logits[0, -1:].float(), atol=1e-3, rtol=1e-3):
                        assert norm is not None and torch.allclose(head(norm(h[-1:])).float(), out.logits[0, -1:].float(),
                                                                   atol=1e-3, rtol=1e-3), "Logit-Abgleich gescheitert"
                        print("  (hidden_states[-1] ist vor der Endnorm – Norm wird angewandt)", flush=True)
                    else:
                        norm = None
                    geprueft = True
                for k, ts in S.items():
                    if not ts:
                        continue
                    hs = h[[p0 + t for t in ts]]
                    lg = head(norm(hs) if norm is not None else hs).float()
                    P[k] += torch.softmax(lg, -1)[:, ZU].tolist()
        roh[name] = P
        erg["modelle"][name] = {}
        for k, v in P.items():
            v = np.array(v)
            if len(v) == 0:
                continue
            erg["modelle"][name][k] = {"n": int(len(v)), "median": float(np.median(v)), "q90": float(np.quantile(v, .9)),
                                       "max": float(v.max()), "anteil_ueber_0.01": float((v > 0.01).mean()),
                                       "anteil_ueber_0.1": float((v > 0.1).mean()), "anteil_ueber_0.5": float((v > 0.5).mean())}
            e = erg["modelle"][name][k]
            print(f"{name:6s} {k:4s} n {e['n']:3d} | Median {e['median']:.1e}, 90 % {e['q90']:.1e}, Max {e['max']:.1e} | "
                  f"> 0,01: {100 * e['anteil_ueber_0.01']:.0f} %, > 0,1: {100 * e['anteil_ueber_0.1']:.0f} %, > 0,5: {100 * e['anteil_ueber_0.5']:.0f} %",
                  flush=True)
        del model
    if len(roh) == 2:
        (n1, a1), (n2, a2) = roh.items()
        for k in n_kl:
            if a1[k] and a2[k]:
                v = np.log10(np.maximum(np.array(a2[k]), 1e-30) / np.maximum(np.array(a1[k]), 1e-30))
                print(f"  {k:4s}: log10({n2}/{n1}) Median {np.median(v):+.2f}, 90 % {np.quantile(v, .9):+.2f}", flush=True)
                erg.setdefault("verhaeltnis", {})[k] = {"median_log10": float(np.median(v)), "q90_log10": float(np.quantile(v, .9))}
    json.dump(erg, open(a.aus, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(f"gespeichert: {a.aus}")


if __name__ == "__main__":
    main()
