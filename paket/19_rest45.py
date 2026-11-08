"""Die „45 %“ auseinandernehmen: Aufgaben, die der MIT-Edit (unser Nachbau, mit-vstil-L) NICHT löst, nach Topf.

Topf 1 „fertig, aber falsch“ (EOS, falsch) · Topf 2 „kein Entschluss bis 32k“ (limit) · Topf 3 „noch in der Schleife“.
Je Aufgabe:
  - MIT selbst (p50c) und unbearbeitet: richtig in k von 4 Samples  -> „nie / manchmal / meistens“
  - unsere Varianten: wer löst sie, mit wie vielen Tokens
  - Topf 1: Antworten der Varianten, die fertig wurden – dieselbe falsche Antwort (systematisch) oder verschiedene (Irren)?
  - Topf 2/3: taucht die richtige Lösung im Denktext schon auf (\\boxed{Lösung} bzw. „= Lösung“), und wo (Token-Position)?
  python 19_rest45.py --ergebnisse ergebnisse --mit-eval archiv/minipc/lm_understand-logs/exp8_math/eval --tokenizer modelle/Qwen3.5-0.8B
"""
import argparse
import importlib.util
import json
import os
import re

HIER = os.path.dirname(os.path.abspath(__file__))
VARIANTEN = ["basis-vstil-L", "zufall-gleich-vL", "eigen-vL", "opt1-vL", "kreuz-vL", "kreuz2-vL", "mit-vstil-L"]


def norm(s):
    s = (s or "").replace("\\dfrac", "\\frac").replace("\\tfrac", "\\frac").replace("\\left", "").replace("\\right", "")
    return re.sub(r"\s+", "", s).strip("$.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ergebnisse", required=True)
    ap.add_argument("--mit-eval", required=True)
    ap.add_argument("--tokenizer", required=True)
    a = ap.parse_args()
    spec = importlib.util.spec_from_file_location("ma", os.path.join(HIER, "13_mit_abgleich.py"))
    ma = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ma)
    p50, une = ma.lade_mit(a.mit_eval, "p50c"), ma.lade_mit(a.mit_eval, "unedited")
    k4 = lambda pp, i: sum((pp.get(i) or pp.get(i.replace("test/", "")) or {}).get("correct", [])) \
        if (pp.get(i) or pp.get(i.replace("test/", ""))) else None
    R = {v: {json.loads(z)["id"]: json.loads(z) for z in open(os.path.join(a.ergebnisse, v, "ergebnisse.jsonl"), encoding="utf-8")}
         for v in VARIANTEN if os.path.exists(os.path.join(a.ergebnisse, v, "ergebnisse.jsonl"))}
    mit = R["mit-vstil-L"]
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(a.tokenizer)

    toepfe = {"richtig": [], "1 fertig, aber falsch": [], "2 kein Entschluss (32k)": [], "3 noch in der Schleife": []}
    for i, r in mit.items():
        if r.get("korrekt"):
            toepfe["richtig"].append(i)
        elif r["ende"] == "eos":
            toepfe["1 fertig, aber falsch"].append(i)
        elif r["ende"] == "limit":
            toepfe["2 kein Entschluss (32k)"].append(i)
        else:
            toepfe["3 noch in der Schleife"].append(i)

    for name, ids in toepfe.items():
        verteil = [k4(p50, i) for i in ids]
        vu = [k4(une, i) for i in ids]
        txt = lambda v: "/".join(str(sum(1 for x in v if x == k)) for k in range(5))
        print(f"\n=== Topf {name}: {len(ids)} Aufgaben | MIT selbst richtig in 0/1/2/3/4 von 4: {txt(verteil)} "
              f"| unbearbeitet: {txt(vu)}")
        if name == "richtig":
            continue
        for i in sorted(ids, key=lambda x: -(k4(p50, x) or 0)):
            r = mit[i]
            loeser = [f"{v.split('-')[0]}({R[v][i]['tokens'] // 1000}k)" for v in R if v != "mit-vstil-L" and i in R[v] and R[v][i].get("korrekt")]
            zeile = f"  {i:36s} MIT {k4(p50, i)}/4, unbearb. {k4(une, i)}/4 | gelöst von: {', '.join(loeser) or '-'}"
            if name.startswith("1"):
                antw = {v.split('-')[0]: R[v][i].get("pred") for v in R if i in R[v] and R[v][i]["ende"] == "eos" and not R[v][i].get("korrekt")}
                zeile += f" | Lösung {r['gold']!r}; falsche Antworten: {antw}"
            else:
                text = tok.decode(r["gen_ids"])
                g = norm(r["gold"])
                tn = norm(text)
                boxed = [m.start() for m in re.finditer(re.escape("\\boxed{" + g + "}"), tn)]
                gleich = [m.start() for m in re.finditer(re.escape("=" + g), tn)] if len(g) >= 2 else []
                pos = (boxed or gleich)
                erste = f"~{int(len(r['gen_ids']) * pos[0] / max(len(tn), 1)) // 1000}k" if pos else "-"
                zeile += f" | Lösung {r['gold']!r}: im Denken \\boxed {len(boxed)}x, '=Lösung' {len(gleich)}x, zuerst bei {erste}"
            print(zeile)


if __name__ == "__main__":
    main()
