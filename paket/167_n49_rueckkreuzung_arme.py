"""167: N49 Rückkreuzung (Leitvision, 22.11.2026) – baut Arme aus der Sub-Base (Qwen3.5-0.8B, nachtrainiert) mit Tensoren der
Main-Base (Qwen3.5-0.8B-Base, vortrainiert). Nur vorhandene Tensoren, kein Training. Auswahl vorab nach Bauart (Testplan):
  R-GDN      alle Tensoren der 18 rekurrenten Schichten (language_model …linear_attn.*)
  R-GDN-out  nur linear_attn.out_proj der 18 rekurrenten Schichten
  R-MLP      alle MLP-Blöcke der 24 Schichten (language_model …mlp.*; nicht mtp)
  R-ATT      die 6 Aufmerksamkeits-Schichten (language_model …self_attn.*; nicht mtp)
Alles andere bleibt Sub-Base. Gebaut wird byte-genau: Kopie der Sub-Datei, an den Stellen der gewählten Tensoren die Bytes der Main-Base.
Prüfung je Arm: jeder gewählte Tensor byte-gleich mit der Main-Base, jeder andere byte-gleich mit der Sub-Base; Zahl der gewählten und der
davon wirklich veränderten Tensoren wird ausgegeben. Schreibt modelle/Qwen3.5-0.8B-r-<arm>/ mit wsp_patch.json (Liste und SHA-256).
  python paket/167_n49_rueckkreuzung_arme.py --trocken     zählt nur
  python paket/167_n49_rueckkreuzung_arme.py               baut und prüft alle vier Arme
"""
import hashlib
import json
import os
import re
import shutil
import struct
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(HIER)
SUB_D = os.path.join(WURZEL, "modelle", "Qwen3.5-0.8B")
MAIN_D = os.path.join(WURZEL, "modelle", "Qwen3.5-0.8B-Base")
DATEI = "model.safetensors-00001-of-00001.safetensors"
SHA_SUB = "04b1c301231dd422b8860db31311ab2721511346a32cb1e079c4c4e5f1fe4696"
ARME = {
    "r-gdn": r"^model\.language_model\.layers\.\d+\.linear_attn\.",
    "r-gdn-out": r"^model\.language_model\.layers\.\d+\.linear_attn\.out_proj\.",
    "r-mlp": r"^model\.language_model\.layers\.\d+\.mlp\.",
    "r-att": r"^model\.language_model\.layers\.\d+\.self_attn\.",
}


def kopf(p):
    with open(p, "rb") as f:
        n = struct.unpack("<Q", f.read(8))[0]
        h = json.loads(f.read(n))
    h.pop("__metadata__", None)
    return h, 8 + n


def roh(p, h, off, name):
    a, b = h[name]["data_offsets"]
    with open(p, "rb") as f:
        f.seek(off + a)
        return f.read(b - a)


def main():
    sub, main_ = os.path.join(SUB_D, DATEI), os.path.join(MAIN_D, DATEI)
    hs, os_ = kopf(sub)
    hm, om = kopf(main_)
    assert set(hs) == set(hm), "Tensornamen verschieden"
    assert all(hs[k]["dtype"] == hm[k]["dtype"] and hs[k]["shape"] == hm[k]["shape"] for k in hs), "Form verschieden"
    for arm, muster in ARME.items():
        gew = sorted(k for k in hs if re.search(muster, k))
        anders = [k for k in gew if roh(sub, hs, os_, k) != roh(main_, hm, om, k)]
        print(f"{arm:<10} gewählt {len(gew):>3}, davon zwischen Sub und Main verschieden {len(anders):>3}")
    if "--trocken" in sys.argv:
        print("TROCKEN 167: nichts gebaut")
        return
    if hashlib.sha256(open(sub, "rb").read()).hexdigest() != SHA_SUB:
        sys.exit("Sub-Base: Prüfsumme weicht ab")
    for arm, muster in ARME.items():
        ziel_d = os.path.join(WURZEL, "modelle", f"Qwen3.5-0.8B-{arm}")
        if os.path.exists(ziel_d):
            sys.exit(f"{ziel_d} gibt es schon – nichts überschrieben")
        os.makedirs(ziel_d)
        for fn in os.listdir(SUB_D):
            if fn != DATEI and not fn.startswith(".") and os.path.isfile(os.path.join(SUB_D, fn)):
                shutil.copyfile(os.path.join(SUB_D, fn), os.path.join(ziel_d, fn))
        ziel = os.path.join(ziel_d, DATEI)
        shutil.copyfile(sub, ziel)
        gew = sorted(k for k in hs if re.search(muster, k))
        with open(ziel, "r+b") as f:
            for k in gew:
                a, b = hs[k]["data_offsets"]
                daten = roh(main_, hm, om, k)
                assert len(daten) == b - a
                f.seek(os_ + a)
                f.write(daten)
        # Prüfung
        hz, oz = kopf(ziel)
        fehler = [k for k in hs if roh(ziel, hz, oz, k) != (roh(main_, hm, om, k) if k in set(gew) else roh(sub, hs, os_, k))]
        if fehler:
            sys.exit(f"{arm}: Prüfung fehlgeschlagen bei {len(fehler)} Tensoren, z. B. {fehler[:3]}")
        info = {"arm": arm, "basis": "Qwen/Qwen3.5-0.8B (Sub-Base)", "spender": "Qwen/Qwen3.5-0.8B-Base (Main-Base)", "muster": muster,
                "getauscht": {k: hashlib.sha256(roh(ziel, hz, oz, k)).hexdigest() for k in gew},
                "datei_sha256": hashlib.sha256(open(ziel, "rb").read()).hexdigest()}
        with open(os.path.join(ziel_d, "wsp_patch.json"), "w", encoding="utf-8", newline="\n") as f:
            json.dump(info, f, indent=1)
        print(f"{arm:<10} gebaut und geprüft: {len(gew)} Tensoren aus der Main-Base, Datei {info['datei_sha256'][:12]}…")


if __name__ == "__main__":
    main()
