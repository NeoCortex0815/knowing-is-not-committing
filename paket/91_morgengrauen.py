"""Morgengrauen: zweite Chance mit den eigenen Notizen (08.11.; Nutzer-Idee „den begonnenen Gedanken festhalten … zweite Chance“;
Lesart N10 in ANNAHMEN, festgelegt vor dem Lauf). Baut die Aufgaben-Dateien für Runde 2; der Lauf selbst geht über
eval/03b_eval_ohne_denken.py, also dasselbe Protokoll und dieselbe Bewertung wie INT.
Menge: WT-A-Läufe auf 161–300 (Seed 0) OHNE abgegebene Antwort, also Denken zu ohne \\boxed oder nie zu. Beobachtbar, ohne
Lösungswissen.
Notizen: die ≤ 3 Wert-Aussagen der ersten Runde mit dem höchsten Wahrheits-Tor zT_max (Zuck-Messung 82):
  - verschiedene Werte, zT_max ≥ −1;
  - je der Satz mit dem Wert und der Satz davor, höchstens ~400 Zeichen;
  - Auswahl nur nach dem eigenen Signal; gold wird nur zur Beschreibung danach gelesen.
Ausgabe: daten/morgengrauen_161-260.jsonl, daten/morgengrauen_261-300.jsonl (Felder wie math500.jsonl, „problem“ mit Notizen).
  python 91_morgengrauen.py
"""
import importlib.util
import json
import os
import re

import numpy as np

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(HIER)
ERG = os.path.join(WURZEL, "ergebnisse")
DIRS = ["s3-wta-161-210", "s3-wta-211-260", "s3-wta-261-300"]
KOPF = "\n\nNotes from an earlier attempt at this problem (unverified, may contain mistakes):\n"


def lade_mod(name, pfad):
    s = importlib.util.spec_from_file_location(name, pfad)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


def norm(w):
    return w.replace(" ", "").replace("$", "").replace("\\!", "").rstrip(".").lower()


def ausschnitt(text, c, maxlen=400):
    """Satz mit Zeichen c plus Satz davor."""
    ende = len(text)
    m = re.search(r"(?<=[.!?])\s|\n", text[c:])
    if m:
        ende = c + m.start()
    starts = [mm.end() for mm in re.finditer(r"[.!?]\s+|\n+", text[:c])]
    anfang = starts[-2] if len(starts) >= 2 else 0
    s = text[anfang:ende].strip()
    if len(s) > maxlen:
        s = "…" + s[-maxlen:]
    return re.sub(r"\s+", " ", s)


def main():
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(os.path.join(WURZEL, "modelle", "Qwen3.5-0.8B"))
    info = {}
    for z in open(os.path.join(WURZEL, "daten", "math500.jsonl"), encoding="utf-8"):
        d = json.loads(z)
        info[d["unique_id"]] = d
    runs = {}
    for d in DIRS:
        for z in open(os.path.join(ERG, d, "ergebnisse.jsonl"), encoding="utf-8"):
            r = json.loads(z)
            runs[r["id"]] = r
    Z = {}
    for z in open(os.path.join(ERG, "zucken_WT-A_ergo-zigA.jsonl"), encoding="utf-8"):
        r = json.loads(z)
        Z[r["id"]] = r
    reihen = {"161-260": [], "261-300": []}
    stat = {"stumm": 0, "mit_notizen": 0, "notiz_enthaelt_richtig": 0}
    memo = {(c, g): bool(v) for c, g, v in json.load(open(os.path.join(ERG, "wertcache.json"), encoding="utf-8"))}
    for i in sorted(runs, key=lambda x: list(info).index(x)):
        z = Z[i]
        if not (z["art"].startswith("geschlossen, keine Antwort") or z["art"].startswith("nie geschlossen")):
            continue
        stat["stumm"] += 1
        r = runs[i]
        st = [tok.decode([t]) for t in r["gen_ids"][:z["n_mess"]]]
        gr = np.cumsum([len(s) for s in st])
        text = "".join(st)
        kand = sorted([s for s in z["aussagen"] if s["zT_max"] >= -1.0], key=lambda s: -s["zT_max"])
        gewaehlt, gesehen = [], set()
        for s in kand:
            k = norm(s["wert"])
            if k in gesehen:
                continue
            gesehen.add(k)
            gewaehlt.append(s)
            if len(gewaehlt) == 3:
                break
        gewaehlt.sort(key=lambda s: s["t"])
        notizen = [ausschnitt(text, int(gr[min(s["t"], len(gr) - 1)]) - 1) for s in gewaehlt]
        d = dict(info[i])
        if notizen:
            d["problem"] = d["problem"] + KOPF + "".join(f"{k + 1}. {n}\n" for k, n in enumerate(notizen))
            stat["mit_notizen"] += 1
        d["notizen_n"] = len(notizen)
        d["notiz_werte"] = [s["wert"] for s in gewaehlt]
        d["wta_art"] = z["art"]
        richtig_in_notiz = any(memo.get((s["wert"], r["gold"]), False) for s in gewaehlt)
        stat["notiz_enthaelt_richtig"] += richtig_in_notiz
        d["notiz_enthaelt_richtig"] = richtig_in_notiz  # nur beschreibend, nicht zur Auswahl
        nr = int(i.split("/")[-1].split(".")[0]) if False else None  # noqa: F841
        idx = list(info).index(i)
        reihen["161-260" if idx < 260 else "261-300"].append(d)
    for k, R in reihen.items():
        p = os.path.join(WURZEL, "daten", f"morgengrauen_{k}.jsonl")
        with open(p, "w", encoding="utf-8") as f:
            for d in R:
                f.write(json.dumps(d, ensure_ascii=False) + "\n")
        print(f"{k}: {len(R)} stumme Läufe → {p}")
    print(f"gesamt stumm {stat['stumm']}, mit Notizen {stat['mit_notizen']}, Notiz enthält den richtigen Wert (nur beschreibend) "
          f"{stat['notiz_enthaelt_richtig']}")
    beispiel = next((d for d in reihen["161-260"] if d["notizen_n"]), None)
    if beispiel:
        print("\nBeispiel-Prompt (gekürzt):\n" + beispiel["problem"][-900:])


if __name__ == "__main__":
    main()
