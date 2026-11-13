"""Eichung der Bewertung (12.11.2026, nach dem Bewertungsfehler; Regel: bevor ein Rechner misst, bewertet er dieselben gespeicherten
Antworten wie der andere). Prüft das reparierte Auswertungsprogramm (Fassung 0.4) gegen bekannte Antworten und gegen das alte:
  1. bekannte Paare (gleichwertige Schreibweisen) im Haupt-Thread richtig;
  2. Aufruf aus einem Arbeits-Thread: unter Linux muss er laut scheitern (RuntimeError), unter Windows gleich bewerten;
  3. der Ablauf wie in main(): Generierung in Threads, Bewertung im Haupt-Thread, gleiche Werte wie direkt;
  4. Eichliste: alle gespeicherten (pred, gold) der angegebenen Ordner, im Haupt-Thread mit altem und neuem Programm bewertet,
     müssen gleich sein; geschrieben wird eine Datei mit einem Fingerabdruck (SHA-256 über id und Bewertung), die man zwischen
     den Rechnern vergleicht.
Ändert keine Ergebnisdatei.
  python paket/137_bewertung_eichen.py --neu <Pfad zum reparierten 03_eval.py> [--alt eval/03_eval.py] --ordner A B … --aus eichung.json
"""
import argparse
import hashlib
import importlib.util
import json
import os
import sys
import threading
from concurrent.futures import ThreadPoolExecutor

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(HIER)
PAARE = [("\\frac{1}{2}", "\\dfrac{1}{2}", True), ("0.5", "\\frac12", True), ("3", "4", False), ("(1,2)", "(1, 2)", True),
         ("2\\sqrt{3}", "\\sqrt{12}", True), ("\\{1,2\\}", "\\{2,1\\}", True), (None, "1", False), ("10", "10\\text{ cm}", True)]


def lade(pfad, name):
    s = importlib.util.spec_from_file_location(name, pfad)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--neu", required=True)
    ap.add_argument("--alt", default=os.path.join(WURZEL, "eval", "03_eval.py"))
    ap.add_argument("--ergebnisse", default=os.path.join(WURZEL, "ergebnisse"))
    ap.add_argument("--ordner", nargs="*", default=[])
    ap.add_argument("--aus")
    a = ap.parse_args()
    neu, alt = lade(a.neu, "ev_neu"), lade(a.alt, "ev_alt")
    ok = True
    print("Plattform:", sys.platform, "| Zeitgrenze aktiv:", neu._MV == {})
    # 1
    for p, g, soll in PAARE:
        ist = neu.korrekt(p, g)
        ok &= ist == soll
        print(f"  {'ok ' if ist == soll else 'FEHLER'} {p!r} gegen {g!r}: {ist}")
    # 2
    erg = {}

    def im_thread():
        try:
            erg["w"] = neu.korrekt("0.5", "\\frac12")
        except RuntimeError as e:
            erg["e"] = str(e)
    t = threading.Thread(target=im_thread)
    t.start()
    t.join()
    if neu._MV == {}:
        ok &= "e" in erg
        print("  Arbeits-Thread mit Zeitgrenze:", "scheitert laut (richtig)" if "e" in erg else f"FEHLER, lieferte {erg.get('w')}")
    else:
        ok &= erg.get("w") is True
        print("  Arbeits-Thread ohne Zeitgrenze:", "bewertet gleich (richtig)" if erg.get("w") is True else f"FEHLER {erg}")
    # 3
    with ThreadPoolExecutor(4) as ex:
        roh = list(ex.map(lambda x: x, PAARE))  # „Generierung“ in Threads
    gleich = all(neu.korrekt(p, g) == soll for p, g, soll in roh)  # Bewertung im Haupt-Thread
    ok &= gleich
    print("  Ablauf Threads → Haupt-Thread:", "gleich" if gleich else "FEHLER")
    # 4
    eich, abw, n = [], 0, 0
    for o in a.ordner:
        for z in open(os.path.join(a.ergebnisse, o, "ergebnisse.jsonl"), encoding="utf-8"):
            if not z.strip():
                continue
            r = json.loads(z)
            if "gold" not in r:
                continue
            kn, st = neu.korrekt_mit_status(r.get("pred"), r["gold"])
            ka = alt.korrekt(r.get("pred"), r["gold"])
            n += 1
            abw += kn != ka
            eich.append(f"{o}/{r['id']}={int(kn)}{'' if st == 'math-verify' else '!'}")
    fp = hashlib.sha256("\n".join(sorted(eich)).encode()).hexdigest()
    ok &= abw == 0 and not neu.RUECKFAELLE
    print(f"  Eichliste: {n} Abgaben aus {len(a.ordner)} Ordnern, alt ≠ neu: {abw}, Text-Rückfälle: {len(neu.RUECKFAELLE)}, "
          f"Fingerabdruck {fp[:16]}")
    if a.aus:
        json.dump({"plattform": sys.platform, "n": n, "abweichungen": abw, "rueckfaelle": neu.RUECKFAELLE, "fingerabdruck": fp,
                   "ordner": a.ordner}, open(a.aus, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("EICHUNG", "bestanden" if ok else "NICHT bestanden")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
