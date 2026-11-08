"""Breiterer Antwort-Erkenner für ein künftiges K2 (07.11. abends, NACHTRÄGLICH entwickelt, nur Text, keine Generierung).
Anlass: WT-A schließt das Denken meist direkt nach Ergebnis-Sätzen („So $\\binom{10}{8} = 45$.“), bevor „\\boxed{…}“ oder
„answer is …“ erscheint – der alte Erkenner (42_wahrheitsmelder.kandidaten_mit_ende) sieht diese Stellen nicht.
v2 = alter Erkenner ∪ Wert-Aussagen: „= W“ / „is W“ / „are W“ am Satz- oder Formelende (W bis 40 Zeichen, endet vor . , ; : $ oder
Zeilenende) – richtig, wenn math-verify(W, gold).
Ausgabe je Modell (beschreibend; die Vorab-Lesart des WT-A-Tests bleibt unberührt):
  - Abdeckung: Anteil der richtigen Läufe, in deren Denken der richtige Wert vorkommt – alt gegen v2;
  - Vorsprung: Tokens zwischen dem ersten richtigen Wert (v2) und dem ersten richtigen alten Kandidaten;
  - K2 nach v2: Gelegenheiten, Zündungen (Denken schließt ≤ 64 Tokens nach einem richtigen Wert, der zugleich die letzte
    Wert-Aussage vor `</think>` ist), Präzision der schnellen Abschlüsse (≤ 64 Tokens nach irgendeiner Wert-Aussage).
  python 76_kandidaten_v2.py [eigen ERGORE …]
VORAB-TEST H-WT2 (Nutzer-Go 07.11. ~18:25; festgelegt, bevor ein WT-A-Lauf auf 161–300 existierte):
  python 76_kandidaten_v2.py --schritt3   → MATH-500 161–300, Seed 0, WT-A gegen MIT (und ERGORE beschreibend), gleiche Aufgaben
  H-WT2 bestanden, wenn (a) Zünd-Quote v2 WT-A ≥ MIT + 20 Prozentpunkte UND (b) Präzision v2 WT-A ≥ MIT − 5 Prozentpunkte;
  (c) weniger als 20 WT-A-Gelegenheiten → „nicht beurteilbar“. Beschreibend: Fisher einseitig für (a), je Block, gegen ERGORE.
  --codetest nur Programmtest mit alten Set-B-Läufen (schreibt *_CODETEST.json).
"""
import importlib.util
import json
import os
import re

import numpy as np

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(HIER)
ERG = os.path.join(WURZEL, "ergebnisse")
MODELLE = {"WT-A": ["setB30-wta-t06", "minipc-b2-wta-t06"], "eigen": ["setB30-eigen-t06", "minipc-b2-eigen-t06"],
           "ERGORE": ["setB-ergore-t06"]}
WERT = re.compile(r"(?:=|\bis\b|\bare\b)\s*\$?\s*([^=$\n]{1,40}?)\s*\$?\s*(?=[.,;:](?:\s|$)|\$|\n|$)")


def lade_mod(name, pfad):
    s = importlib.util.spec_from_file_location(name, pfad)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


def wert_aussagen(text):
    """[(start, ende, wert)] – ende = Zeichenindex hinter dem Wert."""
    out = []
    for m in WERT.finditer(text):
        w = m.group(1).strip().rstrip(".,;:")
        if w and re.search(r"\d", w):
            out.append((m.start(1), m.start(1) + len(m.group(1).rstrip()), w))
    return out


def main():
    wm = lade_mod("wm", os.path.join(HIER, "42_wahrheitsmelder.py"))
    ev = wm.lade("ev", os.path.join(WURZEL, "eval", "03_eval.py"))
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(os.path.join(WURZEL, "modelle", "Qwen3.5-0.8B"))
    import sys
    global MODELLE
    schritt3 = "--schritt3" in sys.argv
    aus = os.path.join(ERG, "kandidaten_v2.json")
    if schritt3:
        MODELLE = {"WT-A": ["s3-wta-161-210", "s3-wta-211-260", "s3-wta-261-300"], "MIT": ["s3-mit-161-260", "s3-mit-261-300"],
                   "ERGORE": ["s3-ergore-161-260", "s3-ergore-261-300"]}
        aus = os.path.join(ERG, "kandidaten_v2_schritt3.json")
        if "--codetest" in sys.argv:
            MODELLE = {"WT-A": ["setB30-wta-t06", "minipc-b2-wta-t06"], "MIT": ["setB-mit-t10"], "ERGORE": ["setB-ergore-t06"]}
            aus = os.path.join(ERG, "kandidaten_v2_schritt3_CODETEST.json")
    if "--seed1" in sys.argv:  # 08.11. (N7, beschreibend): WT-A Seed 1 gegen Seed 0 auf 161–260; MIT nur Seed 0
        MODELLE = {"WT-A s1": ["s3-wta-161-210-s1", "s3-wta-211-260-s1"], "WT-A s0": ["s3-wta-161-210", "s3-wta-211-260"],
                   "MIT s0": ["s3-mit-161-260"]}
        aus = os.path.join(ERG, "kandidaten_v2_seed1.json")
    nur = [a for a in sys.argv[1:] if a in MODELLE]
    memo = {}
    cpfad = os.path.join(ERG, "wertcache.json")
    if os.path.exists(cpfad):  # 07.11. ~23:50, rein technisch: paralleler Vorab-Abgleich (80_wertcache.py), gleiche Prüfung, nur schneller
        memo = {(c, g): bool(v) for c, g, v in json.load(open(cpfad, encoding="utf-8"))}

    def pruefe(c, g):  # math-verify ist langsam: Zwischenspeicher je (Wert, gold)
        k = (c, g)
        if k not in memo:
            memo[k] = bool(ev.korrekt(c, g)) or bool(ev.korrekt(wm.bereinige_kandidat(c), g))
        return memo[k]
    erg = json.load(open(aus, encoding="utf-8")) if os.path.exists(aus) and not schritt3 else {}
    for name, dirs in MODELLE.items():
        if nur and name not in nur:
            continue
        z = {"laeufe": 0, "richtig": 0, "abdeckung_alt": 0, "abdeckung_v2": 0, "vorsprung_tokens": [],
             "gelegenheiten_v2": 0, "zuendungen_v2": 0, "schnell_v2": 0, "schnell_richtig_v2": 0, "je_ordner": {}}
        for d in dirs:
            p = os.path.join(ERG, d, "ergebnisse.jsonl")
            if not os.path.exists(p):
                print(f"FEHLT: {d}", flush=True)
                continue
            vor = {k: z[k] for k in ("laeufe", "richtig", "gelegenheiten_v2", "zuendungen_v2", "schnell_v2", "schnell_richtig_v2")}
            for zeile in open(p, encoding="utf-8"):
                r = json.loads(zeile)
                z["laeufe"] += 1
                st = [tok.decode([t]) for t in r["gen_ids"]]
                gr = np.cumsum([len(s) for s in st]) if st else np.array([0])
                text = "".join(st)
                zc = text.find("</think>")
                denk = text if zc < 0 else text[:zc]
                alt = [(s0, e, c) for (s0, e, c) in wm.kandidaten_mit_ende(denk)]
                neu = wert_aussagen(denk)
                alle = sorted(alt + neu)
                ok = lambda c, g=r["gold"]: pruefe(c, g)  # noqa: E731
                ok_alle = [ok(c) for (_, _, c) in alle]
                ok_alt = [ok(c) for (_, _, c) in alt]
                if r["korrekt"]:
                    z["richtig"] += 1
                    z["abdeckung_alt"] += any(ok_alt)
                    z["abdeckung_v2"] += any(ok_alle)
                    if any(ok_alt) and any(ok_alle):
                        c_v2 = alle[ok_alle.index(True)][1]
                        c_alt = alt[ok_alt.index(True)][1]
                        t = lambda c: int(np.searchsorted(gr, c - 1, side="right"))  # noqa: E731
                        z["vorsprung_tokens"].append(t(c_alt) - t(c_v2))
                z["gelegenheiten_v2"] += any(ok_alle)
                if zc >= 0 and alle:
                    t_zu = int(np.searchsorted(gr, zc, side="right"))
                    tl = min(int(np.searchsorted(gr, alle[-1][1] - 1, side="right")), len(st) - 1)
                    if t_zu - tl <= 64:
                        z["schnell_v2"] += 1
                        z["schnell_richtig_v2"] += ok_alle[-1]
                        z["zuendungen_v2"] += ok_alle[-1]
            z["je_ordner"][d] = {k: z[k] - vor[k] for k in vor}
        v = z.pop("vorsprung_tokens")
        z["vorsprung_median"] = float(np.median(v)) if v else None
        z["vorsprung_n"] = len(v)
        z["zuend_quote_v2"] = z["zuendungen_v2"] / z["gelegenheiten_v2"] if z["gelegenheiten_v2"] else None
        z["praezision_v2"] = z["schnell_richtig_v2"] / z["schnell_v2"] if z["schnell_v2"] else None
        erg[name] = z
        print(f"{name:6s}: {z}", flush=True)
        json.dump(erg, open(aus, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    if schritt3 and "WT-A" in erg and "MIT" in erg:
        from math import comb
        w, m = erg["WT-A"], erg["MIT"]
        if w["gelegenheiten_v2"] < 20:
            urteil = "NICHT BEURTEILBAR (< 20 WT-A-Gelegenheiten)"
        else:
            a_ok = (w["zuend_quote_v2"] or 0) >= (m["zuend_quote_v2"] or 0) + 0.20
            b_ok = (w["praezision_v2"] or 0) >= (m["praezision_v2"] or 0) - 0.05
            urteil = ("BESTANDEN" if a_ok and b_ok else "NICHT bestanden") + f" ((a) Zünd-Quote {'✓' if a_ok else '✗'}, (b) Präzision {'✓' if b_ok else '✗'})"
        # Fisher einseitig (beschreibend): Zünd-Quote WT-A > MIT
        a1, n1, a2, n2 = w["zuendungen_v2"], w["gelegenheiten_v2"], m["zuendungen_v2"], m["gelegenheiten_v2"]
        K, N = a1 + a2, n1 + n2
        p_f = sum(comb(K, x) * comb(N - K, n1 - x) for x in range(a1, min(K, n1) + 1)) / comb(N, n1) if N and n1 else 1.0
        print(f"H-WT2 (vorab): {urteil} | Zünd-Quote v2 WT-A {100 * (w['zuend_quote_v2'] or 0):.0f} % [{a1}/{n1}] gegen MIT "
              f"{100 * (m['zuend_quote_v2'] or 0):.0f} % [{a2}/{n2}] (Fisher einseitig p = {p_f:.4f}) | Präzision v2 WT-A "
              f"{100 * (w['praezision_v2'] or 0):.0f} % [{w['schnell_richtig_v2']}/{w['schnell_v2']}] gegen MIT "
              f"{100 * (m['praezision_v2'] or 0):.0f} % [{m['schnell_richtig_v2']}/{m['schnell_v2']}]")
        erg["H-WT2"] = {"urteil": urteil, "p_fisher_zuend": p_f}
        json.dump(erg, open(aus, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(f"gespeichert: {aus}")


if __name__ == "__main__":
    main()
