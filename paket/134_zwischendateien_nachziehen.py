"""Nachziehen der eingebackenen Bewertung in Zwischendateien des Spiegels nachrechnung_mv/ (12.11.2026; Dave: „Ja, nachziehen“).
133 hat nur <Ordner>/ergebnisse.jsonl neu bewertet. Einige Zwischendateien tragen das alte „korrekt“ fest in sich; ihre Felder
entstanden so (Quelltext der eingefrorenen Skripte, unverändert):
  - zucken_<Quelle>_<Modell>.jsonl (82): korrekt, wta_korrekt, mit_korrekt direkt aus den Quellordnern; gruppe daraus; art wechselt
    nur zwischen „geschlossen, falsche Antwort“ und „richtig“ (andere Arten hängen am Text).
  - int_sonde.jsonl (89 Teil A): korrekt direkt aus dem Lauf (lauf = Ordner/Kennung).
  - ehrlichkeit_schritt1.jsonl (71): korrekt_offiziell direkt; korrekt bei Art „antwort“ ebenso. Bei „keine“ ohne erzwungene
    Antwort könnte ein jetzt richtiger Lauf in den Zweig „denken“ fallen (bräuchte einen neuen Grafikkarten-Wert): wird gezählt
    und als Grenze gemeldet, nicht erfunden.
  - vorderzimmer/<Ordner>.npz (103): meta[*].korrekt direkt; X (Zustände) hängt nicht an korrekt und bleibt Byte für Byte.
Jede Datei wird nur im Spiegel geändert. Vorher wird geprüft, dass sie noch byte-gleich zum Original ist und dass jedes alte Feld
genau dem alten Wert der Quelle entspricht (sonst stimmt die Herleitung nicht → Abbruch). Nachher: außer den genannten Feldern
ändert sich nichts (geprüft). Manifest: nachrechnung_mv/MANIFEST_ZWISCHEN.json.
  python paket/134_zwischendateien_nachziehen.py --selbsttest | --trocken | --ziehen
"""
import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile

import numpy as np

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(HIER)
SP = os.path.join(WURZEL, "nachrechnung_mv")
QUELLEN = {"WT-A": ["s3-wta-161-210", "s3-wta-211-260", "s3-wta-261-300"], "MIT": ["s3-mit-161-260", "s3-mit-261-300"]}
ZUCKEN = ["zucken_WT-A_ergo-zigA.jsonl", "zucken_MIT_mit-wt.jsonl"]


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


class Bewertung:
    """korrekt je (Ordner, Kennung) aus <wurzel>/ergebnisse/<Ordner>/ergebnisse.jsonl; spätere Ordner überschreiben (wie 82)."""

    def __init__(self, wurzel):
        self.erg, self.c = os.path.join(wurzel, "ergebnisse"), {}

    def ordner(self, d):
        if d not in self.c:
            R = {}
            for z in open(os.path.join(self.erg, d, "ergebnisse.jsonl"), encoding="utf-8"):
                if z.strip():
                    r = json.loads(z)
                    if "korrekt" in r:
                        R[r["id"]] = bool(r["korrekt"])
            self.c[d] = R
        return self.c[d]

    def quelle(self, dirs):
        R = {}
        for d in dirs:
            R.update(self.ordner(d))
        return R


def ordner_aus_lauf(r):
    lauf, i = r["lauf"], r["id"]
    assert lauf.endswith("/" + i), lauf
    return lauf[: -len(i) - 1]


def gruppe(w, m):
    return "nur MIT richtig" if m and not w else ("nur WT-A richtig" if w and not m else "gleich")


def zucken_neu(r, alt, neu):
    """alt/neu: Bewertung. Gibt (neuer Datensatz, Grenze?)."""
    Qa, Wa, Ma = alt.quelle(QUELLEN[r["quelle"]]), alt.quelle(QUELLEN["WT-A"]), alt.quelle(QUELLEN["MIT"])
    Qn, Wn, Mn = neu.quelle(QUELLEN[r["quelle"]]), neu.quelle(QUELLEN["WT-A"]), neu.quelle(QUELLEN["MIT"])
    i = r["id"]
    assert (r["korrekt"], r["wta_korrekt"], r["mit_korrekt"]) == (Qa[i], Wa[i], Ma[i]), f"Herleitung stimmt nicht: {i}"
    assert r["gruppe"] == gruppe(Wa[i], Ma[i]), f"gruppe stimmt nicht: {i}"
    if r["art"] in ("geschlossen, falsche Antwort", "richtig"):
        assert (r["art"] == "richtig") == r["korrekt"], f"art stimmt nicht: {i}"
    x = dict(r)
    x["korrekt"], x["wta_korrekt"], x["mit_korrekt"] = Qn[i], Wn[i], Mn[i]
    x["gruppe"] = gruppe(Wn[i], Mn[i])
    if r["art"] in ("geschlossen, falsche Antwort", "richtig"):
        x["art"] = "richtig" if Qn[i] else "geschlossen, falsche Antwort"
    return x, False


def sonde_neu(r, alt, neu):
    d, i = ordner_aus_lauf(r), r["id"]
    assert r["korrekt"] == alt.ordner(d)[i], f"Herleitung stimmt nicht: {r['lauf']}"
    x = dict(r)
    x["korrekt"] = neu.ordner(d)[i]
    return x, False


def ehrlich_neu(r, alt, neu, zwang):
    """zwang: Menge (Ordner, Kennung) mit erzwungener Antwort (Variante „ende“)."""
    d, i = ordner_aus_lauf(r), r["id"]
    assert r["korrekt_offiziell"] == alt.ordner(d)[i], f"Herleitung stimmt nicht: {r['lauf']}"
    x, grenze = dict(r), False
    x["korrekt_offiziell"] = neu.ordner(d)[i]
    if r["art"] == "antwort":
        assert r["korrekt"] == r["korrekt_offiziell"], r["lauf"]
        x["korrekt"] = x["korrekt_offiziell"]
    elif r["art"] == "denken":
        assert r["korrekt"] is True and x["korrekt_offiziell"] is True, r["lauf"]
    elif r["art"] == "keine" and x["korrekt_offiziell"] and not r["korrekt_offiziell"] and (d, i) not in zwang:
        grenze = True  # hätte mit \boxed im Denken den Zweig „denken“ genommen → neuer Wert nötig
    return x, grenze


def dump_art(zeilen):
    """Findet die json.dumps-Einstellung, mit der die Datei geschrieben wurde (Rundweg Zeile für Zeile)."""
    for ea in (False, True):
        if all(json.dumps(json.loads(z), ensure_ascii=ea) == z.rstrip("\r\n") for z in zeilen if z.strip()):
            return ea
    raise AssertionError("Rundweg der Zeilen nicht möglich")


def felder_diff(a, b):
    return sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k))


def jsonl_ziehen(p_sp, p_orig, f, schreiben):
    assert sha(p_sp) == sha(p_orig), f"{p_sp} ist nicht mehr byte-gleich zum Original (schon nachgezogen?)"
    zeilen = open(p_sp, encoding="utf-8", newline="").readlines()
    ea = dump_art(zeilen)
    neu_z, geaendert, grenzen, felder = [], [], [], {}
    for z in zeilen:
        if not z.strip():
            neu_z.append(z)
            continue
        r = json.loads(z)
        x, g = f(r)
        if g:
            grenzen.append(r.get("lauf", r["id"]))
        fd = felder_diff(r, x)
        if fd:
            geaendert.append(r.get("lauf", r["id"]))
            for k in fd:
                felder[k] = felder.get(k, 0) + 1
            neu_z.append(json.dumps(x, ensure_ascii=ea) + z[len(z.rstrip("\r\n")):])
        else:
            neu_z.append(z)
    info = {"zeilen": sum(1 for z in zeilen if z.strip()), "geaendert": len(geaendert), "felder": felder, "kennungen": geaendert,
            "grenzen": grenzen, "sha_original": sha(p_orig)}
    if schreiben and geaendert:
        with open(p_sp, "w", encoding="utf-8", newline="") as fo:
            fo.writelines(neu_z)
        info["sha_neu"] = sha(p_sp)
    return info


def npz_ziehen(p_sp, p_orig, d, alt, neu, schreiben):
    assert sha(p_sp) == sha(p_orig), f"{p_sp} ist nicht mehr byte-gleich zum Original (schon nachgezogen?)"
    with np.load(p_sp) as z:
        A = {k: z[k].copy() for k in z.files}
    s = str(A["meta"])
    meta = json.loads(s)
    assert json.dumps(meta) == s, "Rundweg meta nicht möglich"
    geaendert = []
    for m in meta:
        assert m["korrekt"] == alt.ordner(d)[m["id"]], f"Herleitung stimmt nicht: {d}/{m['id']}"
        k = neu.ordner(d)[m["id"]]
        if k != m["korrekt"]:
            m["korrekt"] = k
            geaendert.append(m["id"])
    info = {"zeilen": len(meta), "geaendert": len(geaendert), "felder": {"meta.korrekt": len(geaendert)} if geaendert else {},
            "kennungen": geaendert, "grenzen": [], "sha_original": sha(p_orig)}
    if schreiben and geaendert:
        fd, tmp = tempfile.mkstemp(suffix=".npz", dir=os.path.dirname(p_sp))
        os.close(fd)
        np.savez_compressed(tmp, **{k: (json.dumps(meta) if k == "meta" else v) for k, v in A.items()})
        with np.load(tmp) as z:
            assert set(z.files) == set(A)
            for k in A:
                if k != "meta":
                    assert z[k].dtype == A[k].dtype and np.array_equal(z[k], A[k]), f"{k} weicht ab"
            m2 = json.loads(str(z["meta"]))
            assert m2 == meta
        shutil.move(tmp, p_sp)
        info["sha_neu"] = sha(p_sp)
    return info


def zwang_menge(wurzel):
    S, o = set(), os.path.join(wurzel, "ergebnisse", "antwort_zwang")
    for f in os.listdir(o):
        if f.endswith(".jsonl"):
            for z in open(os.path.join(o, f), encoding="utf-8"):
                if z.strip():
                    e = json.loads(z)
                    if e.get("variante") == "ende":
                        S.add((f[:-6], e["id"]))
    return S


def lauf(schreiben):
    alt, neu = Bewertung(WURZEL), Bewertung(SP)
    E_sp, E_or = os.path.join(SP, "ergebnisse"), os.path.join(WURZEL, "ergebnisse")
    zwang = zwang_menge(SP)
    man = {}
    for f in ZUCKEN:
        man[f] = jsonl_ziehen(os.path.join(E_sp, f), os.path.join(E_or, f), lambda r: zucken_neu(r, alt, neu), schreiben)
    man["int_sonde.jsonl"] = jsonl_ziehen(os.path.join(E_sp, "int_sonde.jsonl"), os.path.join(E_or, "int_sonde.jsonl"),
                                          lambda r: sonde_neu(r, alt, neu), schreiben)
    man["ehrlichkeit_schritt1.jsonl"] = jsonl_ziehen(os.path.join(E_sp, "ehrlichkeit_schritt1.jsonl"),
                                                     os.path.join(E_or, "ehrlichkeit_schritt1.jsonl"),
                                                     lambda r: ehrlich_neu(r, alt, neu, zwang), schreiben)
    for f in sorted(os.listdir(os.path.join(E_sp, "vorderzimmer"))):
        if f.endswith(".npz"):
            d = f[:-4]
            assert os.path.isfile(os.path.join(E_sp, d, "ergebnisse.jsonl")), f"kein Quellordner zu {f}"
            man["vorderzimmer/" + f] = npz_ziehen(os.path.join(E_sp, "vorderzimmer", f), os.path.join(E_or, "vorderzimmer", f), d,
                                                  alt, neu, schreiben)
    for k, v in man.items():
        if v["geaendert"] or v["grenzen"]:
            print(f"{k:45s} {v['zeilen']:5d} Zeilen, geändert {v['geaendert']:3d} {v['felder']}"
                  + (f"  GRENZE {len(v['grenzen'])}: {v['grenzen']}" if v["grenzen"] else ""))
    print(f"unverändert: {sum(1 for v in man.values() if not v['geaendert'])} Dateien; "
          f"Grenzfälle gesamt {sum(len(v['grenzen']) for v in man.values())}")
    if schreiben:
        json.dump(man, open(os.path.join(SP, "MANIFEST_ZWISCHEN.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("geschrieben; Manifest MANIFEST_ZWISCHEN.json")
    else:
        print("TROCKEN: nichts geschrieben")


def selbsttest():
    ok = True
    t = tempfile.mkdtemp(dir=os.environ.get("TEMP"))
    try:
        def bau(wurzel, werte):
            for d, R in werte.items():
                os.makedirs(os.path.join(wurzel, "ergebnisse", d), exist_ok=True)
                with open(os.path.join(wurzel, "ergebnisse", d, "ergebnisse.jsonl"), "w", encoding="utf-8") as f:
                    for i, k in R.items():
                        f.write(json.dumps({"id": i, "gold": "1", "korrekt": k}) + "\n")
        dirs = QUELLEN["WT-A"] + QUELLEN["MIT"]
        A = {d: {} for d in dirs}
        A["s3-wta-261-300"] = {"a/1": False, "a/2": False}
        A["s3-mit-261-300"] = {"a/1": True, "a/2": False}
        N = json.loads(json.dumps(A))
        N["s3-wta-261-300"]["a/1"] = True
        N["s3-wta-261-300"]["a/2"] = True
        bau(os.path.join(t, "alt"), A)
        bau(os.path.join(t, "neu"), N)
        alt, neu = Bewertung(os.path.join(t, "alt")), Bewertung(os.path.join(t, "neu"))
        r = {"id": "a/1", "gruppe": "nur MIT richtig", "quelle": "WT-A", "korrekt": False, "art": "geschlossen, falsche Antwort",
             "wta_korrekt": False, "mit_korrekt": True, "x": [1.5, {"korrekt": "innen"}]}
        x, _ = zucken_neu(r, alt, neu)
        ok &= x["korrekt"] and x["wta_korrekt"] and x["art"] == "richtig" and x["gruppe"] == "gleich" and x["x"] == r["x"]
        r2 = dict(r, id="a/2", gruppe="gleich", mit_korrekt=False, art="geschlossen, keine Antwort (limit)")
        x2, _ = zucken_neu(r2, alt, neu)
        ok &= x2["korrekt"] and x2["art"] == r2["art"] and x2["gruppe"] == "nur WT-A richtig"
        try:
            zucken_neu(dict(r, korrekt=True), alt, neu)
            ok = False
        except AssertionError:
            pass
        e = {"satz": "S · x", "lauf": "s3-wta-261-300/a/1", "id": "a/1", "korrekt_offiziell": False, "pred_offiziell": True,
             "art": "antwort", "korrekt": False, "wert": 0.25}
        y, g = ehrlich_neu(e, alt, neu, set())
        ok &= y["korrekt_offiziell"] and y["korrekt"] and not g and y["wert"] == 0.25
        e2 = {k: v for k, v in e.items() if k not in ("korrekt", "wert")}
        e2["art"] = "keine"
        ok &= ehrlich_neu(e2, alt, neu, set())[1] is True and ehrlich_neu(e2, alt, neu, {("s3-wta-261-300", "a/1")})[1] is False
        zl = [json.dumps(e, ensure_ascii=False) + "\n"]
        ok &= dump_art(zl) is False
        p = os.path.join(t, "v.npz")
        X = np.arange(24, dtype=np.float16).reshape(2, 3, 4)
        np.savez_compressed(p, X=X, meta=json.dumps([{"id": "a/1", "korrekt": False, "zeile": 0}, {"id": "a/2", "korrekt": False}]),
                            n_laeufe=2, schichten=np.array([4, 6, 8]))
        q = os.path.join(t, "v_orig.npz")
        shutil.copy(p, q)
        info = npz_ziehen(p, q, "s3-wta-261-300", alt, neu, True)
        with np.load(p) as z:
            ok &= info["geaendert"] == 2 and np.array_equal(z["X"], X) and z["X"].dtype == np.float16 and int(z["n_laeufe"]) == 2
            ok &= [m["korrekt"] for m in json.loads(str(z["meta"]))] == [True, True]
    finally:
        shutil.rmtree(t, ignore_errors=True)
    print("SELBSTTEST", "bestanden" if ok else "NICHT bestanden")
    return ok


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--selbsttest", action="store_true")
    g.add_argument("--trocken", action="store_true")
    g.add_argument("--ziehen", action="store_true")
    a = ap.parse_args()
    if a.selbsttest:
        sys.exit(0 if selbsttest() else 1)
    lauf(schreiben=a.ziehen)
