"""Berichtigte Lauf-Tabellen und Urteilsdateien für v0.4 (12.11.2026; Dave: „Ja, v0.4 entwerfen“). Schreibt NICHT ins Repo.
  - results/runs/<Ordner>.csv: nur die Spalte correct wird aus dem Spiegel nachrechnung_mv/ergebnisse/<Ordner>/ergebnisse.jsonl
    übernommen. Vorher geprüft: jede Zeile gehört zu einer Kennung des Ordners, gold und pred stimmen überein, und das Neu-Schreiben
    unveränderter Zeilen ergibt Byte für Byte die veröffentlichte Zeile (Rundweg).
  - results/verdicts/<Datei>.json: wenn die veröffentlichte Datei inhaltlich gleich dem Original in ergebnisse/ ist und der Spiegel
    abweicht, wird der Spiegel-Inhalt im veröffentlichten Format geschrieben (Format per Rundweg geprüft). Vorher Suche nach Pfaden
    und Rechnernamen im neuen Inhalt.
Ziel: veroeffentlichung/v0.4/staging/results/… (nur geänderte Dateien) und, für Skript 115, eine vollständige Kopie
nachrechnung_mv/release/wsp-qwen08b/results/runs/ (alle CSVs, berichtigt).
  python paket/136_v04_tabellen.py --trocken | --bauen
"""
# Release-Kopie (v0.4): gegenüber der Arbeitsfassung ein privater Rechnername und ein lokaler Ordnername im Suchmuster entfernt; keine Änderung der Logik.
import argparse
import csv
import io
import json
import os
import re
import shutil
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(HIER)
REL = os.path.join(WURZEL, "release", "wsp-qwen08b", "results")
SP = os.path.join(WURZEL, "nachrechnung_mv")
STAGE = os.path.join(WURZEL, "veroeffentlichung", "v0.4", "staging", "results")
VERBOTEN = re.compile(r"[A-Za-z]:\\\\|[A-Za-z]:/|/mnt/|/home/|Users|nachrechnung_mv|192\.168\.", re.I)


def zeile_csv(felder, ende="\n"):
    b = io.StringIO()
    csv.writer(b, lineterminator=ende).writerow(felder)
    return b.getvalue()


def laufe(ordner):
    R = {}
    for z in open(os.path.join(SP, "ergebnisse", ordner, "ergebnisse.jsonl"), encoding="utf-8"):
        if z.strip():
            r = json.loads(z)
            if "gold" in r and "korrekt" in r:
                R[r["id"]] = r
    return R


def csvs(schreiben):
    quelle = os.path.join(REL, "runs")
    ziel_voll = os.path.join(SP, "release", "wsp-qwen08b", "results", "runs")
    bericht, zellen = {}, 0
    for f in sorted(os.listdir(quelle)):
        if not f.endswith(".csv"):
            continue
        roh = open(os.path.join(quelle, f), encoding="utf-8", newline="").read()
        zeilen = roh.splitlines(keepends=True)
        ende = "\r\n" if zeilen[0].endswith("\r\n") else "\n"
        kopf = next(csv.reader([zeilen[0]]))
        assert kopf[:4] == ["id", "gold", "pred", "correct"], (f, kopf)
        ordner = f[:-4]
        p = os.path.join(SP, "ergebnisse", ordner, "ergebnisse.jsonl")
        R = laufe(ordner) if os.path.exists(p) else {}
        ids = [next(csv.reader([z]))[0] for z in zeilen[1:]]
        if not R or any(i not in R for i in ids):
            bericht[f] = "kein passender Ordner im Spiegel – unverändert"
            neu = roh
        else:
            neu_z, n = [zeilen[0]], []
            for z in zeilen[1:]:
                fe = next(csv.reader([z]))
                assert zeile_csv(fe, ende) == z, f"Rundweg scheitert: {f}"
                r = R[fe[0]]
                assert fe[1] == str(r["gold"]) and fe[2] == ("" if r.get("pred") is None else str(r["pred"])), f"gold/pred: {f} {fe[0]}"
                c = "1" if r["korrekt"] else "0"
                if c != fe[3]:
                    assert fe[3] == "0" and c == "1", f"richtig → falsch? {f} {fe[0]}"
                    fe[3] = c
                    n.append(fe[0])
                    neu_z.append(zeile_csv(fe, ende))
                else:
                    neu_z.append(z)
            neu = "".join(neu_z)
            if n:
                bericht[f] = n
                zellen += len(n)
                if schreiben:
                    os.makedirs(os.path.join(STAGE, "runs"), exist_ok=True)
                    open(os.path.join(STAGE, "runs", f), "w", encoding="utf-8", newline="").write(neu)
        if schreiben:
            os.makedirs(ziel_voll, exist_ok=True)
            open(os.path.join(ziel_voll, f), "w", encoding="utf-8", newline="").write(neu)
    geaendert = {k: v for k, v in bericht.items() if isinstance(v, list)}
    print(f"CSVs: {len(geaendert)} Dateien, {zellen} Zellen 0 → 1; ohne Spiegel-Ordner: "
          f"{[k for k, v in bericht.items() if isinstance(v, str)]}")
    return geaendert, zellen


FORMATE = [(ind, ea, nl, ende) for ind in (1, 2, None) for ea in (False, True) for nl in ("\n", "\r\n") for ende in (True, False)]


def format_json(x, fmt):
    ind, ea, nl, ende = fmt
    t = json.dumps(x, ensure_ascii=ea, indent=ind).replace("\n", nl)
    return t + (nl if ende else "")


def format_finden(x, roh):
    for fmt in FORMATE:
        if format_json(x, fmt) == roh:
            return fmt
    return None


def urteile(schreiben):
    quelle = os.path.join(REL, "verdicts")
    geaendert, ohne, pfad = [], [], []
    for f in sorted(os.listdir(quelle)):
        if not f.endswith(".json"):
            continue
        roh = open(os.path.join(quelle, f), encoding="utf-8", newline="").read()
        alt_p, neu_p = os.path.join(WURZEL, "ergebnisse", f), os.path.join(SP, "ergebnisse", f)
        if not (os.path.exists(alt_p) and os.path.exists(neu_p)):
            ohne.append(f)
            continue
        V, A, N = json.loads(roh), json.load(open(alt_p, encoding="utf-8")), json.load(open(neu_p, encoding="utf-8"))
        if V != A:
            ohne.append(f + " (veröffentlicht ≠ Original)")
            continue
        if A == N:
            continue
        fmt = format_finden(V, roh)
        assert fmt is not None, f"Format-Rundweg scheitert: {f}"
        t = format_json(N, fmt)
        if VERBOTEN.search(t):
            pfad.append(f)
            continue
        geaendert.append(f)
        if schreiben:
            os.makedirs(os.path.join(STAGE, "verdicts"), exist_ok=True)
            open(os.path.join(STAGE, "verdicts", f), "w", encoding="utf-8", newline="").write(t)
    print(f"Urteilsdateien geändert: {len(geaendert)}: {geaendert}")
    print(f"ohne Vergleich: {ohne}")
    print(f"ZURÜCKGEHALTEN wegen Pfad/Rechnername im neuen Inhalt: {pfad}")
    return geaendert, pfad


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--trocken", action="store_true")
    g.add_argument("--bauen", action="store_true")
    a = ap.parse_args()
    if a.bauen and os.path.exists(STAGE):
        sys.exit(f"{STAGE} gibt es schon – nicht überschreiben")
    c, z = csvs(a.bauen)
    u, p = urteile(a.bauen)
    if a.bauen:
        json.dump({"csv": c, "zellen": z, "urteile": u, "zurueckgehalten": p},
                  open(os.path.join(STAGE, "..", "STAGING_MANIFEST.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
