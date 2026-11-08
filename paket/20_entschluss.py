"""Entschluss-Hypothese: Fehlt unserer Richtung der Anteil „fertig, ich antworte jetzt“, den die MIT-Richtung enthält?

  auswahl: leichte Übungsaufgaben (MATH train, Stufe 1–2), ohne die Diagnose-Aufgaben
      python 20_entschluss.py auswahl --daten daten/practice/math_train.jsonl --ohne ergebnisse/diagnose-vL/ergebnisse.jsonl \
          --n 60 --aus daten/practice/math_train_leicht60.jsonl
  bauen: Kontrast aus fertig gedachten Übungs-Transkripten (03_eval-Ausgabe mit gen_ids)
      klasse_a = die --fenster Tokens bis einschließlich </think>   („Entschluss“)
      klasse_b = --je-text Fenster gleicher Länge mitten im Denken     („Weiterdenken“), mind. --abstand Tokens vor </think>
      python 20_entschluss.py bauen --ergebnisse ergebnisse/entschluss-uebung-eigen/ergebnisse.jsonl \
          --tokenizer modelle/Qwen3.5-0.8B --aus ergebnisse/entschluss.jsonl
  pruefe: Erklärt die Entschluss-Richtung den Teil der MIT-Richtung, den unsere bisherigen Richtungen nicht erklären?
      python 20_entschluss.py pruefe --mit minipc/mit_richtung.npz --eigene ergebnisse/richtung-vL-alle.npz \
          ergebnisse/richtung-messer3.npz --entschluss ergebnisse/richtung-entschluss.npz
"""
import argparse
import json
import random

import numpy as np


def auswahl(a):
    ohne = {json.loads(z)["id"] for z in open(a.ohne, encoding="utf-8") if z.strip()}
    z = [json.loads(l) for l in open(a.daten, encoding="utf-8")]
    kand = [r for r in z if r.get("level") in ("Level 1", "Level 2") and r["id"] not in ohne]
    random.Random(a.seed).shuffle(kand)
    with open(a.aus, "w", encoding="utf-8") as fh:
        for r in kand[:a.n]:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"{min(a.n, len(kand))} leichte Übungsaufgaben (von {len(kand)} Kandidaten) -> {a.aus}")


def bauen(a):
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(a.tokenizer)
    zu = tok.convert_tokens_to_ids("</think>")
    rng = random.Random(0)
    zeilen, n_fertig = [], 0
    for z in open(a.ergebnisse, encoding="utf-8"):
        r = json.loads(z)
        gen = r["gen_ids"]
        if zu not in gen:
            continue
        e = gen.index(zu)
        if e < a.abstand + a.fenster + 64:
            continue
        n_fertig += 1
        ka = list(range(e - a.fenster + 1, e + 1))  # Token-Index e = </think> -> gemessen an Position e-1 (sagt </think> voraus)
        kb = []
        for _ in range(a.je_text):
            s = rng.randint(64, e - a.abstand - a.fenster)
            kb += list(range(s, s + a.fenster))
        zeilen.append({"id": r["id"], "prompt_ids": r["prompt_ids"], "gen_ids": gen[:e + 1],
                       "klasse_a": ka, "klasse_b": sorted(set(kb))})
    with open(a.aus, "w", encoding="utf-8") as fh:
        for z in zeilen:
            fh.write(json.dumps(z) + "\n")
    print(f"ENTSCHLUSS-KONTRAST: {n_fertig} fertig gedachte Transkripte -> {len(zeilen)} Zeilen ({a.aus})")


def pruefe(a):
    M = dict(np.load(a.mit))
    E = [dict(np.load(p)) for p in a.eigene]
    X = dict(np.load(a.entschluss))
    for L in map(int, a.schichten.split(",")):
        um = M[f"u_{L}"].astype(np.float64); um /= np.linalg.norm(um)
        alt = np.stack([e[f"u_{L}"].astype(np.float64) for e in E], 1)
        ux = X[f"u_{L}"].astype(np.float64); ux /= np.linalg.norm(ux)
        erkl = lambda B: float(np.linalg.norm(np.linalg.qr(B)[0].T @ um))
        Q = np.linalg.qr(alt)[0]
        rest = um - Q @ (Q.T @ um); rest /= np.linalg.norm(rest)
        vorher, nachher = erkl(alt), erkl(np.concatenate([alt, ux[:, None]], 1))
        print(f"Schicht {L}: cos(Entschluss, MIT) {abs(ux @ um):.3f} | cos(Entschluss, MIT-Rest) {abs(ux @ rest):.3f} | "
              f"erklärter Anteil der MIT-Richtung: bisher {vorher:.3f} -> mit Entschluss {nachher:.3f}")
    print("Zum Vergleich: eine zufällige Richtung hätte cos ~ 1/sqrt(1024) = 0,03 zum MIT-Rest.")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("auswahl")
    s.add_argument("--daten", required=True); s.add_argument("--ohne", required=True)
    s.add_argument("--n", type=int, default=60); s.add_argument("--seed", type=int, default=7); s.add_argument("--aus", required=True)
    b = sub.add_parser("bauen")
    b.add_argument("--ergebnisse", required=True); b.add_argument("--tokenizer", required=True)
    b.add_argument("--fenster", type=int, default=16); b.add_argument("--je-text", type=int, default=4)
    b.add_argument("--abstand", type=int, default=256); b.add_argument("--aus", required=True)
    p = sub.add_parser("pruefe")
    p.add_argument("--mit", required=True); p.add_argument("--eigene", nargs="+", required=True)
    p.add_argument("--entschluss", required=True); p.add_argument("--schichten", default="15,19")
    a = ap.parse_args()
    {"auswahl": auswahl, "bauen": bauen, "pruefe": pruefe}[a.cmd](a)


if __name__ == "__main__":
    main()
