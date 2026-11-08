"""Angst-Marker (Idee Nutzer 06.11.): Wie oft zweifelt das Modell, NACHDEM die richtige Lösung schon im Denken steht?

τy = erste Stelle im Denktext, an der die richtige Lösung steht („= Lösung“, „\\boxed{Lösung}“, „answer is Lösung“).
Je Transkript mit τy: Zweifel-Marker (Wait, Hmm, double-check, verify, Alternatively, re-read, Actually, But …) je
1.000 Wörter VOR und NACH τy, Wörter von τy bis </think> (oder Ende), abgeschlossen ja/nein.
Nur beschreibende Auswertung vorhandener Läufe (keine Edits daraus).
  python 22_angstmarker.py --tokenizer modelle/Qwen3.5-0.8B --laeufe ergebnisse/eigen-vL ergebnisse/mit-vstil-L ...
"""
import argparse
import json
import os
import re
import statistics as st

MARKER = re.compile(r"\b(wait|hmm+|double[- ]check\w*|re-?check\w*|verify\w*|alternatively|re-?read\w*|actually|"
                    r"let me (?:check|make sure|confirm|reconsider)|but let me|is that right|did i)\b", re.I)


def norm(s):
    s = (s or "").replace("\\dfrac", "\\frac").replace("\\tfrac", "\\frac").replace("\\left", "").replace("\\right", "")
    return re.sub(r"\s+", "", s).strip("$.")


def tau(text, gold):
    g = norm(gold)
    if not g:
        return None
    t = norm(text)
    muster = ["\\boxed{" + g + "}", "answeris" + g, "=" + g] if len(g) >= 2 or not g.isdigit() else ["\\boxed{" + g + "}", "answeris" + g]
    pos = [t.find(m) for m in muster if t.find(m) >= 0]
    if not pos:
        return None
    # Position im normierten Text -> grob auf Originaltext abbilden (Anteil)
    return int(min(pos) / max(len(t), 1) * len(text))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tokenizer", required=True)
    ap.add_argument("--laeufe", nargs="+", required=True)
    a = ap.parse_args()
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(a.tokenizer)
    for lauf in a.laeufe:
        rs = [json.loads(z) for z in open(os.path.join(lauf, "ergebnisse.jsonl"), encoding="utf-8")]
        zeilen = []
        for r in rs:
            text = tok.decode(r["gen_ids"])
            denk = text.split("</think>")[0]
            p = tau(denk, r.get("gold"))
            if p is None:
                continue
            vor, nach = denk[:p], denk[p:]
            wv, wn = max(len(vor.split()), 1), max(len(nach.split()), 1)
            zeilen.append({"zu": "</think>" in text, "ende": r["ende"], "korrekt": bool(r.get("korrekt")),
                           "vor": 1000 * len(MARKER.findall(vor)) / wv, "nach": 1000 * len(MARKER.findall(nach)) / wn,
                           "woerter_nach": len(nach.split()), "woerter_vor": len(vor.split())})
        n = len(rs)
        print(f"\n== {os.path.basename(lauf)}: {n} Aufgaben, richtige Lösung im Denken bei {len(zeilen)}")
        for name, gruppe in (("abgeschlossen", [z for z in zeilen if z["zu"]]), ("NICHT abgeschlossen", [z for z in zeilen if not z["zu"]])):
            if not gruppe:
                continue
            md = lambda k: st.median(z[k] for z in gruppe)
            print(f"   {name:20s} n={len(gruppe):2d} | Wörter bis Lösung (Median) {md('woerter_vor'):6.0f} | Wörter danach {md('woerter_nach'):6.0f}"
                  f" | Zweifel je 1.000 Wörter: vorher {md('vor'):5.1f}, danach {md('nach'):5.1f}")


if __name__ == "__main__":
    main()
