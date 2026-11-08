"""WT-A: Wo schließt das Denken? (NACHTRÄGLICH, BESCHREIBEND – nach dem vorab festgelegten WT-A-Urteil vom 07.11. 17:44)
Anlass: K2 war „nicht beurteilbar“ (nur 2 Gelegenheiten), weil WT-A das Denken meist schließt, BEVOR das Modell „\\boxed{…}“ oder
„answer is …“ schreibt – also bevor unser Kandidaten-Erkenner (42_wahrheitsmelder.kandidaten_mit_ende) etwas sieht. Die Stichprobe
zeigte Abschlüsse direkt nach Ergebnis-Sätzen wie „So $\\binom{10}{8} = 45$.“
Erweiterter Erkenner (nur für diese Beschreibung, NICHT die Vorab-Lesart): letzter Wert im Text vor dem ersten `</think>` (innerhalb
der letzten 400 Zeichen) nach „=“, „is“/„are“/„be“ oder als letzte Zahl; richtig = math-verify gegen gold (wie 03_eval).
Ausgabe je Modell: Abschlüsse direkt (≤ 64 Tokens) nach richtigem Wert / nach falschem Wert / ohne erkennbaren Wert.
  python 74_wta_abschluss_ort.py
"""
import importlib.util
import json
import os
import re

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(HIER)
ERG = os.path.join(WURZEL, "ergebnisse")
MODELLE = {"WT-A": ["setB30-wta-t06", "minipc-b2-wta-t06"], "eigen": ["setB30-eigen-t06", "minipc-b2-eigen-t06"]}
WERT = re.compile(r"(?:=|\bis\b|\bare\b|\bbe\b)\s*\$?\s*([^=$\n]{1,40}?)\s*\$?\s*(?:[.,;:]|\*\*|$)")
ZAHL = re.compile(r"(-?\d+(?:\.\d+)?(?:/\d+)?)\D*$")


def lade_mod(name, pfad):
    s = importlib.util.spec_from_file_location(name, pfad)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


def main():
    ev = lade_mod("ev", os.path.join(WURZEL, "eval", "03_eval.py"))
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(os.path.join(WURZEL, "modelle", "Qwen3.5-0.8B"))
    ZU = tok.convert_tokens_to_ids("</think>")
    erg = {}
    for name, dirs in MODELLE.items():
        z = {"geschlossen": 0, "nach_richtigem_wert": 0, "nach_falschem_wert": 0, "ohne_wert": 0,
             "lauf_richtig_nach_richtigem_wert": 0, "lauf_richtig_nach_falschem_wert": 0}
        for d in dirs:
            for zeile in open(os.path.join(ERG, d, "ergebnisse.jsonl"), encoding="utf-8"):
                r = json.loads(zeile)
                g = r["gen_ids"]
                if ZU not in g:
                    continue
                k = g.index(ZU)
                z["geschlossen"] += 1
                ende = tok.decode(g[max(0, k - 64):k])          # die letzten 64 Tokens vor </think>
                kandidaten = [m.group(1).strip() for m in WERT.finditer(ende)]
                m2 = ZAHL.search(ende.rstrip(" .$\n*"))
                if m2:
                    kandidaten.append(m2.group(1))
                kandidaten = [c for c in kandidaten if c]
                if not kandidaten:
                    z["ohne_wert"] += 1
                    continue
                ok = bool(ev.korrekt(kandidaten[-1], r["gold"]))
                z["nach_richtigem_wert" if ok else "nach_falschem_wert"] += 1
                z["lauf_richtig_nach_richtigem_wert" if ok else "lauf_richtig_nach_falschem_wert"] += bool(r["korrekt"])
        erg[name] = z
        print(f"{name:6s}: {z}")
    json.dump(erg, open(os.path.join(ERG, "wta_abschluss_ort.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
