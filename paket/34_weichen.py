"""Weichen-Statistik (Nutzer 06.11. ~04:10: Messerschneide = „Ende oder Warte“, „Wann ist Messerschneide?“).

Jedes Satzende im Denktext NACH τy (die richtige Lösung stand schon im Denken) ist eine Weiche. Was folgt?
  Ende   – das Denken schließt direkt danach (</think>)
  Warte  – der nächste Satz beginnt mit Zweifel/Prüfen (Wait, Hmm, But wait, Let me check/verify, Double-check, Actually, Hold on)
  Weiter – alles andere
Kennzahlen je Lauf-Gruppe: Anteile an allen Weichen, an der ERSTEN Weiche und an den ersten 20 Weichen nach τy (frühe
Entscheidungen, weniger Schleifen-Aufblähung) sowie die Zahl der Weichen, bis abgegeben wurde.
  python 34_weichen.py basis=ergebnisse/basis-vstil-L/ergebnisse.jsonl eigen=ergebnisse/eigen-vL/ergebnisse.jsonl \
      mit=ergebnisse/mit-vstil-L/ergebnisse.jsonl
"""
import importlib.util
import json
import os
import re
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
SATZENDE = re.compile(r"[.!?](?=\s)|\n\s*\n")
WARTE = re.compile(r"\s*(?:\*\*)?(?:wait|hmm+|but wait|let me (?:double[- ]?)?check|let me verify|let me re-?check|"
                   r"double[- ]check|actually|hold on)\b", re.I)


def lade_am():
    s = importlib.util.spec_from_file_location("am", os.path.join(HIER, "22_angstmarker.py"))
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


def weichen(denk, t, geschlossen):
    enden = [m.end() for m in SATZENDE.finditer(denk, t)]
    out = []
    for k, e in enumerate(enden):
        rest = denk[e:]
        if not rest.strip():
            out.append("Ende" if geschlossen else "offen")
        elif WARTE.match(rest):
            out.append("Warte")
        else:
            out.append("Weiter")
    if geschlossen and (not out or out[-1] != "Ende"):
        out.append("Ende")
    return [w for w in out if w != "offen"]


BINS = [(0, 20), (20, 100), (100, 300), (300, 600), (600, 10 ** 9)]


def verlauf(laeufe):
    """Nutzer 06.11. ~04:15: „Urknall, der sekündlich größer wird?“ – Abgabe-Chance und Warte-Anteil über die Weichen-Nr."""
    print("   Verlauf (Weichen-Nr. nach τy): Warte-Anteil | Abgaben je 1.000 Weichen | Läufe, die so weit kommen")
    for a, b in BINS:
        stueck = [w[a:b] for w in laeufe if len(w) > a]
        n = sum(len(s) for s in stueck)
        if not n:
            continue
        warte = sum(s.count("Warte") for s in stueck)
        ende = sum(s.count("Ende") for s in stueck)
        bis = str(b) if b < 10 ** 9 else "…"
        print(f"     {a + 1:>4d}–{bis:<5s} {100 * warte / n:5.1f} % | {1000 * ende / n:5.2f} | {len(stueck)}")


def anteile(liste):
    n = max(len(liste), 1)
    return {k: 100 * liste.count(k) / n for k in ("Ende", "Warte", "Weiter")}, len(liste)


def main():
    am = lade_am()
    for arg in sys.argv[1:]:
        name, pfad = arg.split("=", 1)
        rs = [json.loads(z) for z in open(pfad, encoding="utf-8")]
        alle, erste, frueh, bis_ende, laeufe = [], [], [], [], []
        for r in rs:
            text = r["text"]
            denk = text.split("</think>")[0]
            t = am.tau(denk, r.get("gold"))
            if t is None:
                continue
            w = weichen(denk, t, "</think>" in text)
            if not w:
                continue
            laeufe.append(w)
            alle += w
            erste.append(w[0])
            frueh += w[:20]
            if w[-1] == "Ende":
                bis_ende.append(len(w))
        print(f"\n== {name}: {sum(1 for _ in erste)} Läufe mit Lösung im Denken")
        for titel, liste in (("alle Weichen nach τy", alle), ("erste Weiche nach τy", erste), ("erste 20 Weichen", frueh)):
            a, n = anteile(liste)
            print(f"   {titel:22s} n={n:5d} | Ende {a['Ende']:5.1f} % · Warte {a['Warte']:5.1f} % · Weiter {a['Weiter']:5.1f} %")
        if bis_ende:
            s = sorted(bis_ende)
            print(f"   abgegeben: {len(s)} Läufe, Weichen bis zum Ende: Median {s[len(s) // 2]}, Spanne {s[0]}–{s[-1]}")
        verlauf(laeufe)


if __name__ == "__main__":
    main()
