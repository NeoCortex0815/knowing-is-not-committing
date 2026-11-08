"""Nachbewertung von 03_eval-Ergebnissen mit math-verify – im HAUPTTHREAD.

Hintergrund (05.11.2026): 03_eval.py bewertet in Threads. math-verify nutzt unter Linux signal.alarm() für seine
Zeitbegrenzung, das geht nur im Hauptthread -> ValueError -> 03_eval fällt still auf einen Textvergleich zurück.
Gleichwertige Schreibweisen (11\\sqrt2 = 11\\sqrt{2}, 1/2 = 0.5) zählten deshalb als falsch. Unter Windows scheitert die
Zeitbegrenzung ganz (Unterprozesse); dort wird ohne Zeitbegrenzung bewertet.

  python 11_nachbewerten.py ergebnisse/basis ergebnisse/mit ... [--aus nachbewertung.json]
Liest nur ergebnisse.jsonl (verändert nichts) und gibt alte/neue Trefferquote je Lauf aus, dazu jede geänderte Aufgabe.
"""
import argparse
import json
import os

from math_verify import parse, verify

KW_P = {"parsing_timeout": None} if os.name == "nt" else {}
KW_V = {"timeout_seconds": None} if os.name == "nt" else {}


def mv(pred, gold):
    if pred is None:
        return False
    try:
        return bool(verify(parse("\\boxed{" + gold + "}", **KW_P), parse("\\boxed{" + pred + "}", **KW_P), **KW_V))
    except Exception:
        return None  # nicht bewertbar (Zeitbegrenzung / Parserfehler) -> alter Wert bleibt


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("laeufe", nargs="+")
    ap.add_argument("--aus")
    a = ap.parse_args()
    out = {}
    print("| Lauf | n | korrekt alt (Textvergleich) | korrekt neu (math-verify) | geändert | nicht bewertbar |")
    print("|---|---|---|---|---|---|")
    for d in a.laeufe:
        rs = [json.loads(z) for z in open(os.path.join(d, "ergebnisse.jsonl"), encoding="utf-8")]
        alt = sum(bool(r["korrekt"]) for r in rs)
        neu, geaendert, offen = 0, [], 0
        for r in rs:
            k = mv(r.get("pred"), r["gold"])
            if k is None:
                offen += 1
                k = bool(r["korrekt"])
            neu += k
            if k != bool(r["korrekt"]):
                geaendert.append({"id": r["id"], "gold": r["gold"], "pred": (r.get("pred") or "")[:120], "neu": k})
        name = os.path.basename(os.path.normpath(d))
        out[name] = {"n": len(rs), "korrekt_alt": round(alt / len(rs), 4), "korrekt_neu": round(neu / len(rs), 4),
                     "geaendert": geaendert, "nicht_bewertbar": offen}
        print(f"| {name} | {len(rs)} | {alt}/{len(rs)} = {alt / len(rs):.1%} | {neu}/{len(rs)} = {neu / len(rs):.1%} "
              f"| {len(geaendert)} | {offen} |")
    for name, v in out.items():
        for g in v["geaendert"]:
            print(f"  {name}: {g['id']}  gold {g['gold']!r}  pred {g['pred']!r}  -> {'richtig' if g['neu'] else 'falsch'}")
    if a.aus:
        json.dump(out, open(a.aus, "w", encoding="utf-8"), indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
