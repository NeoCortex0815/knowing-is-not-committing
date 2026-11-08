"""Klingel-Regel trocken getestet (Idee Nutzer 06.11.): Abgeben, sobald dieselbe Antwort k-mal im Denken auftaucht.

Die Regel kennt die richtige Lösung NICHT. Antwort-Kandidaten im Denktext: \\boxed{…} und „answer is …“.
Je Transkript: löst die Regel aus (k gleiche Kandidaten)? Wenn ja: Kandidat = Antwort, Tokens bis dahin.
Vergleich: tatsächliches Ergebnis des Laufs vs. Ergebnis mit Regel (ausgelöst -> Regel-Antwort, sonst tatsächlich).
  python 23_klingel_regel.py --tokenizer modelle/Qwen3.5-0.8B --k 2 --laeufe ergebnisse/entschluss-uebung-eigen ...
"""
import argparse
import importlib.util
import json
import os
import re

HIER = os.path.dirname(os.path.abspath(__file__))


def kandidaten(text):
    out = []
    i = 0
    while True:
        j = text.find("\\boxed{", i)
        if j < 0:
            break
        k, tiefe = j + 7, 1
        while k < len(text) and tiefe:
            tiefe += {"{": 1, "}": -1}.get(text[k], 0)
            k += 1
        out.append((j, text[j + 7:k - 1]))
        i = k
    for m in re.finditer(r"answer is[:\s]*\$?([^\n$]{1,40}?)\$?(?:[.\n]|$)", text):
        out.append((m.start(), m.group(1)))
    return sorted(out)


def norm(s):
    s = (s or "").replace("\\dfrac", "\\frac").replace("\\tfrac", "\\frac").replace("\\left", "").replace("\\right", "")
    return re.sub(r"\s+|\\!|\\,", "", s).strip("$.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tokenizer", required=True)
    ap.add_argument("--laeufe", nargs="+", required=True)
    ap.add_argument("--k", type=int, default=2)
    ap.add_argument("--eval-modul", default=os.path.join(HIER, "..", "eval", "03_eval.py"))
    a = ap.parse_args()
    spec = importlib.util.spec_from_file_location("ev", a.eval_modul)
    ev = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ev)
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(a.tokenizer)
    for lauf in a.laeufe:
        rs = [json.loads(z) for z in open(os.path.join(lauf, "ergebnisse.jsonl"), encoding="utf-8")]
        n = len(rs)
        echt = regel = ausgeloest = treffer_regel = 0
        gespart, ausgeloest_offen, rettungen, verluste = [], 0, 0, 0
        for r in rs:
            text = tok.decode(r["gen_ids"])
            denk = text.split("</think>")[0]
            zaehl, hit = {}, None
            for pos, c in kandidaten(denk):
                c = norm(c)
                if not c:
                    continue
                zaehl[c] = zaehl.get(c, 0) + 1
                if zaehl[c] >= a.k:
                    hit = (pos, c)
                    break
            ok_echt = bool(r.get("korrekt"))
            echt += ok_echt
            if hit:
                ausgeloest += 1
                ok_regel = bool(ev.korrekt(hit[1], r.get("gold")))
                treffer_regel += ok_regel
                regel += ok_regel
                rettungen += ok_regel and not ok_echt
                verluste += ok_echt and not ok_regel
                ausgeloest_offen += r["ende"] != "eos"
                tok_bis = int(len(r["gen_ids"]) * hit[0] / max(len(text), 1))
                gespart.append(len(r["gen_ids"]) - tok_bis)
            else:
                regel += ok_echt
        print(f"\n== {os.path.basename(lauf)} ({n} Aufgaben, Regel: {a.k}× gleiche Antwort im Denken -> abgeben)")
        print(f"   tatsächlich richtig {echt}/{n} = {echt / n:.1%} | MIT Regel richtig {regel}/{n} = {regel / n:.1%}"
              f"  (Rettungen {rettungen}, Verluste {verluste})")
        if ausgeloest:
            print(f"   ausgelöst bei {ausgeloest} Aufgaben (davon {ausgeloest_offen} sonst NICHT abgeschlossen), "
                  f"dort richtig {treffer_regel}/{ausgeloest} = {treffer_regel / ausgeloest:.0%}; "
                  f"gespart im Mittel {sum(gespart) / len(gespart):,.0f} Tokens je ausgelöster Aufgabe")


if __name__ == "__main__":
    main()
