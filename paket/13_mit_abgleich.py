"""Abgleich unserer Messung mit den MIT-Einzelergebnissen (lm_understand-logs/exp8_math/eval/<lauf>/parts/math500_*).

Das MIT rechnet alle 500 MATH-500-Aufgaben je 4-mal (bf16, vLLM). Wir rechnen die ersten 40 je einmal (Q8_0, llama.cpp).
Dieses Skript berechnet die MIT-Trefferquote auf GENAU unseren Aufgaben und vergleicht Aufgabe für Aufgabe.

  python 13_mit_abgleich.py --mit-eval .../exp8_math/eval --unsere basis=ergebnisse/basis mit=ergebnisse/mit
"""
import argparse
import glob
import json
import os


def lade_mit(eval_dir, lauf):
    pp = {}
    for d in sorted(glob.glob(os.path.join(eval_dir, lauf, "parts", "math500_s*"))):
        f = os.path.join(d, "math500_per_problem.json")
        if os.path.exists(f):
            j = json.load(open(f, encoding="utf-8"))
            if isinstance(j, dict):
                pp.update(j)
            else:  # Liste [{"id", "correct": [0/1 je Sample], "pred_first"}]
                pp.update({x["id"]: x for x in j})
    return pp


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mit-eval", required=True)
    ap.add_argument("--unsere", nargs="+", required=True, help="name=ordner (name: basis->unedited, mit->p50c)")
    ap.add_argument("--zeige", action="store_true", help="Struktur eines MIT-Eintrags zeigen")
    a = ap.parse_args()
    zuordnung = {"basis": "unedited", "mit": "p50c"}
    for spec in a.unsere:
        name, ordner = spec.split("=", 1)
        mit = lade_mit(a.mit_eval, zuordnung.get(name, name))
        if a.zeige:
            k = next(iter(mit))
            print("Beispiel-Schlüssel:", k, "->", json.dumps(mit[k], ensure_ascii=False)[:600])
        uns = [json.loads(z) for z in open(os.path.join(ordner, "ergebnisse.jsonl"), encoding="utf-8")]
        print(f"\n== {name}: {len(uns)} unserer Aufgaben, {len(mit)} MIT-Aufgaben geladen")
        if not mit:
            continue
        treffer, fehlt = [], 0
        for r in uns:
            e = mit.get(r["id"]) or mit.get(r["id"].replace("test/", ""))
            if e is None:
                fehlt += 1
                continue
            treffer.append((r, e))
        if fehlt:
            print(f"   {fehlt} Aufgaben nicht zuordenbar")
        if not treffer:
            continue

        n = len(treffer)
        mit_p = [sum(e["correct"]) / len(e["correct"]) for _, e in treffer]
        ok_uns = [bool(r["korrekt"]) for r, _ in treffer]
        print(f"   MIT auf unseren {n} Aufgaben: {sum(mit_p) / n:.1%} (Mittel über {len(treffer[0][1]['correct'])} Samples)"
              f" | wir: {sum(ok_uns) / n:.1%} (1 Sample)")
        print(f"   MIT auf allen {len(mit)} Aufgaben: {sum(sum(e['correct']) / len(e['correct']) for e in mit.values()) / len(mit):.1%}")
        # Erwartung: wenn wir wie das MIT sind, ist unser Treffer je Aufgabe ein Münzwurf mit p = MIT-Anteil
        import math
        erw = sum(mit_p); var = sum(p * (1 - p) for p in mit_p)
        z = (sum(ok_uns) - erw) / math.sqrt(var) if var else 0.0
        print(f"   erwartet bei gleichem Modellverhalten: {erw:.1f} ± {math.sqrt(var):.1f} richtige, wir: {sum(ok_uns)} -> z = {z:+.2f}")
        immer = sum(p == 1 for p in mit_p); nie = sum(p == 0 for p in mit_p)
        print(f"   MIT: {immer} Aufgaben 4/4 richtig, {nie} Aufgaben 0/4; davon bei uns richtig: "
              f"{sum(o for o, p in zip(ok_uns, mit_p) if p == 1)} bzw. {sum(o for o, p in zip(ok_uns, mit_p) if p == 0)}")


if __name__ == "__main__":
    main()
