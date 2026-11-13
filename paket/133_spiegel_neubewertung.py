"""Spiegel für die Nachrechnung nach dem Bewertungsfehler auf dem MiniPC (12.11.2026; Dave: „Das sollte unbedingt untersucht und
behoben werden“). Legt nachrechnung_mv/ als eigenes Projektverzeichnis an:
  - paket/, eval/, daten/: Kopien, byte-gleich (Prüfsummen im Manifest);
  - modelle/: Verzeichnis-Verknüpfung (Junction) auf das Original, nur gelesen (Tokenizer);
  - ergebnisse/: Kopie; in jeder ergebnisse.jsonl mit den Feldern gold und korrekt wird korrekt neu gesetzt, mit derselben
    Funktion wie in 03_eval.py, aber im Haupt-Thread auf dem Laptop (math-verify ohne Zeitgrenze). Sonst ändert sich kein Byte
    einer Zeile außer dem Wert von korrekt.
Die eingefrorenen Skripte laufen danach unverändert aus nachrechnung_mv/paket/ (ihr WURZEL ist dann der Spiegel). Die Original-
Ergebnisse werden nicht angefasst. Manifest: nachrechnung_mv/MANIFEST.json (Prüfsummen, je Ordner geänderte Kennungen).
  python paket/133_spiegel_neubewertung.py --selbsttest | --bauen
"""
# Release-Kopie (v0.4): gegenüber der Arbeitsfassung die Liste ungelesener Ordner einer anderen Arbeit entfernt; keine Änderung der Logik.
import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(HIER)
ZIEL = os.path.join(WURZEL, "nachrechnung_mv")
UNGELESEN = ()
_s = importlib.util.spec_from_file_location("ev", os.path.join(WURZEL, "eval", "03_eval.py"))
ev = importlib.util.module_from_spec(_s)
_s.loader.exec_module(ev)


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def zeile_neu(z):
    """Gibt (neue Zeile, geändert, Kennung) zurück; ersetzt nur den Wert von korrekt, alles andere bleibt Byte für Byte."""
    r = json.loads(z)
    if "gold" not in r or "korrekt" not in r:
        return z, False, None
    neu = bool(ev.korrekt(r.get("pred"), r["gold"]))
    if neu == bool(r["korrekt"]):
        return z, False, r.get("id")
    alt_t, neu_t = '"korrekt": ' + json.dumps(r["korrekt"]), '"korrekt": ' + json.dumps(neu)
    assert z.count(alt_t) == 1, f"Feld korrekt nicht eindeutig in Zeile {r.get('id')}"
    z2 = z.replace(alt_t, neu_t)
    r2 = json.loads(z2)
    assert r2["korrekt"] == neu and {k: v for k, v in r2.items() if k != "korrekt"} == {k: v for k, v in r.items() if k != "korrekt"}
    return z2, True, r.get("id")


def selbsttest():
    ok = True
    z = json.dumps({"id": "a", "gold": "\\frac12", "pred": "0.5", "korrekt": False, "text": "x"}, ensure_ascii=False) + "\n"
    z2, g, _ = zeile_neu(z)
    ok &= g and json.loads(z2)["korrekt"] is True and z2.replace("true", "false") == z
    z = json.dumps({"id": "b", "gold": "3", "pred": "4", "korrekt": False}) + "\n"
    ok &= zeile_neu(z) == (z, False, "b")
    z = json.dumps({"id": "c", "text": "ohne Bewertung"}) + "\n"
    ok &= zeile_neu(z)[1] is False
    print("SELBSTTEST", "bestanden" if ok else "NICHT bestanden")
    return ok


def bauen():
    if os.path.exists(ZIEL):
        sys.exit(f"{ZIEL} gibt es schon – nicht überschreiben")
    man = {"kopien": {}, "geaendert": {}}
    for d in ("paket", "eval", "daten"):
        shutil.copytree(os.path.join(WURZEL, d), os.path.join(ZIEL, d), ignore=shutil.ignore_patterns("__pycache__"))
    for d in ("paket", "eval"):
        for f in sorted(os.listdir(os.path.join(WURZEL, d))):
            p = os.path.join(WURZEL, d, f)
            if os.path.isfile(p):
                a, b = sha(p), sha(os.path.join(ZIEL, d, f))
                assert a == b, f"Kopie weicht ab: {d}/{f}"
                man["kopien"][f"{d}/{f}"] = a
    os.makedirs(os.path.join(ZIEL, "logs"))
    subprocess.run(["cmd", "/c", "mklink", "/J", os.path.join(ZIEL, "modelle"), os.path.join(WURZEL, "modelle")], check=True,
                   capture_output=True)
    quelle = os.path.join(WURZEL, "ergebnisse")
    shutil.copytree(quelle, os.path.join(ZIEL, "ergebnisse"), ignore=shutil.ignore_patterns("__pycache__"))
    for o in sorted(os.listdir(quelle)):
        p = os.path.join(quelle, o, "ergebnisse.jsonl")
        if not os.path.isfile(p):
            continue
        zeilen, ids = [], []
        with open(p, encoding="utf-8", newline="") as f:
            for z in f:
                if not z.strip():
                    zeilen.append(z)
                    continue
                z2, g, i = zeile_neu(z)
                zeilen.append(z2)
                if g:
                    ids.append(i)
        if ids:
            with open(os.path.join(ZIEL, "ergebnisse", o, "ergebnisse.jsonl"), "w", encoding="utf-8", newline="") as f:
                f.writelines(zeilen)
            man["geaendert"][o] = {"anzahl": len(ids), "ids": ids, "sha_original": sha(p),
                                   "sha_neu": sha(os.path.join(ZIEL, "ergebnisse", o, "ergebnisse.jsonl"))}
    json.dump(man, open(os.path.join(ZIEL, "MANIFEST.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    gelesen = {o: v["anzahl"] for o, v in man["geaendert"].items() if not o.startswith(UNGELESEN)}
    print(f"Spiegel gebaut: {len(man['kopien'])} Skripte byte-gleich; {len(man['geaendert'])} Ordner neu bewertet "
          f"({len(gelesen)} gelesene, {sum(gelesen.values())} Abgaben falsch → richtig; ungelesene nicht ausgegeben)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--selbsttest", action="store_true")
    ap.add_argument("--bauen", action="store_true")
    a = ap.parse_args()
    if a.selbsttest:
        sys.exit(0 if selbsttest() else 1)
    if a.bauen:
        bauen()
