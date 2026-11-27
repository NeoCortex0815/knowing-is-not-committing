"""176: Arme für N58 (MLP nach Schichten) und N56 (Erziehungs-Regler nur in den MLP) – Leitvision, 23.11.2026.
Lesarten vorab in veroeffentlichung/TESTPLAN_LEITVISION.md (Abschnitte N58 und N56, Fassung 23.11.).
  N58  Grundmodell Sub-Base (Qwen3.5-0.8B), Spender Main-Base (Qwen3.5-0.8B-Base), nur Tensoren kopieren (byte-genau):
       r-mlp-frueh  model.language_model.layers.{0..11}.mlp.*   (36 Tensoren)
       r-mlp-spaet  model.language_model.layers.{12..23}.mlp.*  (36 Tensoren)
  N56  Grundmodell Main-Base; die 72 MLP-Tensoren (Schichten 0–23, nicht mtp) = Main + λ·(Sub − Main):
       m-mlp-l100 (λ = 1, byte-genau die Tensoren der Sub-Base), m-mlp-l050, m-mlp-l075, m-mlp-l025
       Rechnung in float32 (bf16 → f32 exakt), Rundung nach bf16 round-to-nearest-even (wsp_lib.bf16_bits).
Alles andere bleibt byte-gleich mit dem Grundmodell. Prüfung je Arm, Tensor für Tensor: gewählte Tensoren = Sollwert (Spender-Bytes bzw.
neu gerechnete Bytes), alle anderen = Grundmodell. Schreibt modelle/Qwen3.5-0.8B-<arm>/ mit wsp_patch.json (Liste, SHA-256, λ).
  python paket/176_mlp_arme.py --selbsttest          künstliche Safetensors mit bekannter Antwort
  python paket/176_mlp_arme.py --trocken             zählt nur (echte Modelle)
  python paket/176_mlp_arme.py --bauen <arm> [...]   baut und prüft (überschreibt nie)
  python paket/176_mlp_arme.py --gguf <arm>          prüft die GGUF: unveränderte Tensoren byte-gleich mit der GGUF des Grundmodells,
                                                    die gewählten (ffn_*) bei N58 byte-gleich mit der GGUF des Spenders
"""
import hashlib
import json
import os
import re
import shutil
import struct
import sys
import tempfile

import numpy as np

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(HIER)
sys.path.insert(0, HIER)
import wsp_lib as W  # noqa: E402

SUB_D = os.path.join(WURZEL, "modelle", "Qwen3.5-0.8B")
MAIN_D = os.path.join(WURZEL, "modelle", "Qwen3.5-0.8B-Base")
DATEI = "model.safetensors-00001-of-00001.safetensors"
SHA = {"sub": "04b1c301231dd422b8860db31311ab2721511346a32cb1e079c4c4e5f1fe4696"}
GGUF = {"sub": os.path.join(WURZEL, "gguf", "Qwen3.5-0.8B-q8_0.gguf"), "main": os.path.join(WURZEL, "gguf", "Qwen3.5-0.8B-Base-q8_0.gguf")}


def mlp_muster(schichten):
    return r"^model\.language_model\.layers\.(" + "|".join(str(i) for i in schichten) + r")\.mlp\."


# arm: (Grundmodell, Spender, Muster, λ)  – λ None = Bytes des Spenders kopieren
ARME = {
    "r-mlp-frueh": ("sub", "main", mlp_muster(range(0, 12)), None),
    "r-mlp-spaet": ("sub", "main", mlp_muster(range(12, 24)), None),
    "m-mlp-l100": ("main", "sub", mlp_muster(range(0, 24)), None),
    "m-mlp-l050": ("main", "sub", mlp_muster(range(0, 24)), 0.5),
    "m-mlp-l075": ("main", "sub", mlp_muster(range(0, 24)), 0.75),
    "m-mlp-l025": ("main", "sub", mlp_muster(range(0, 24)), 0.25),
}
# nur zum Prüfen der GGUF-Prüfung an einem bekannten Arm (N49, gebaut mit 167): muss bestehen
NUR_GGUF_PRUEFUNG = {"r-mlp": ("sub", "main", mlp_muster(range(0, 24)), None)}


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


def mischen(b_grund, b_spender, lam):
    """Grund + λ·(Spender − Grund) für bf16-Bytes; Ergebnis bf16-Bytes."""
    g = W.bf16_to_f32(np.frombuffer(b_grund, dtype=np.uint16))
    s = W.bf16_to_f32(np.frombuffer(b_spender, dtype=np.uint16))
    m = (g + np.float32(lam) * (s - g)).astype(np.float32)
    return W.bf16_bits(m).tobytes()


def sollwert(arm_def, name, gew, pg, hg, og, ps, hs, os_):
    if name not in gew:
        return roh(pg, hg, og, name)
    lam = arm_def[3]
    if lam is None:
        return roh(ps, hs, os_, name)
    assert hg[name]["dtype"] == "BF16", name
    return mischen(roh(pg, hg, og, name), roh(ps, hs, os_, name), lam)


def bauen(arm, ordner, modelle_d, ziel_wurzel, pruef_sha=True):
    d = ARME[arm]
    pg, ps = os.path.join(ordner[d[0]], DATEI), os.path.join(ordner[d[1]], DATEI)
    hg, og = kopf(pg)
    hs, os_ = kopf(ps)
    assert set(hg) == set(hs), "Tensornamen verschieden"
    assert all(hg[k]["dtype"] == hs[k]["dtype"] and hg[k]["shape"] == hs[k]["shape"] for k in hg), "Form verschieden"
    if pruef_sha and d[0] == "sub" and hashlib.sha256(open(pg, "rb").read()).hexdigest() != SHA["sub"]:
        sys.exit("Sub-Base: Prüfsumme weicht ab")
    ziel_d = os.path.join(ziel_wurzel, f"Qwen3.5-0.8B-{arm}")
    if os.path.exists(ziel_d):
        sys.exit(f"{ziel_d} gibt es schon – nichts überschrieben")
    os.makedirs(ziel_d)
    for fn in os.listdir(ordner[d[0]]):
        q = os.path.join(ordner[d[0]], fn)
        if fn != DATEI and not fn.startswith(".") and fn != "wsp_patch.json" and os.path.isfile(q):
            shutil.copyfile(q, os.path.join(ziel_d, fn))
    ziel = os.path.join(ziel_d, DATEI)
    shutil.copyfile(pg, ziel)
    gew = set(k for k in hg if re.search(d[2], k))
    with open(ziel, "r+b") as f:
        for k in sorted(gew):
            a, b = hg[k]["data_offsets"]
            daten = sollwert(d, k, gew, pg, hg, og, ps, hs, os_)
            assert len(daten) == b - a
            f.seek(og + a)
            f.write(daten)
    # Prüfung Tensor für Tensor
    hz, oz = kopf(ziel)
    fehler = [k for k in hg if roh(ziel, hz, oz, k) != sollwert(d, k, gew, pg, hg, og, ps, hs, os_)]
    if fehler:
        sys.exit(f"{arm}: Prüfung fehlgeschlagen bei {len(fehler)} Tensoren, z. B. {fehler[:3]}")
    anders = sum(roh(ziel, hz, oz, k) != roh(pg, hg, og, k) for k in gew)
    info = {"arm": arm, "grundmodell": {"sub": "Qwen/Qwen3.5-0.8B (Sub-Base)", "main": "Qwen/Qwen3.5-0.8B-Base (Main-Base)"}[d[0]],
            "spender": {"sub": "Qwen/Qwen3.5-0.8B (Sub-Base)", "main": "Qwen/Qwen3.5-0.8B-Base (Main-Base)"}[d[1]], "muster": d[2],
            "lambda": d[3] if d[3] is not None else 1.0, "art": "Bytes des Spenders" if d[3] is None else "Grund + λ·(Spender − Grund), bf16 RNE",
            "getauscht": {k: hashlib.sha256(roh(ziel, hz, oz, k)).hexdigest() for k in sorted(gew)},
            "datei_sha256": hashlib.sha256(open(ziel, "rb").read()).hexdigest()}
    with open(os.path.join(ziel_d, "wsp_patch.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(info, f, indent=1)
    print(f"{arm:<12} gebaut und geprüft: {len(gew)} Tensoren gewählt, davon {anders} gegenüber dem Grundmodell verändert, "
          f"Datei {info['datei_sha256'][:16]}…")
    return info


def gguf_pruefen(arm):
    sys.path.insert(0, os.path.join(WURZEL, "llama", "gguf-py"))
    from gguf import GGUFReader
    d = {**ARME, **NUR_GGUF_PRUEFUNG}[arm]
    p = os.path.join(WURZEL, "gguf", f"Qwen3.5-0.8B-{arm}-q8_0.gguf")
    lies = lambda q: {t.name: bytes(np.asarray(t.data).tobytes()) for t in GGUFReader(q).tensors}  # noqa: E731
    A, G, S = lies(p), lies(GGUF[d[0]]), lies(GGUF[d[1]])
    schichten = [int(x) for x in re.search(r"\(([\d|]+)\)", d[2]).group(1).split("|")]
    gew = {k for k in A if k.startswith("blk.") and int(k.split(".")[1]) in schichten and k.split(".")[2].startswith("ffn_")}
    falsch_rest = [k for k in A if k not in gew and A[k] != G.get(k)]
    if d[3] is None:
        falsch_gew = [k for k in gew if A[k] != S.get(k)]
    else:
        falsch_gew = [k for k in gew if A[k] == G.get(k)]  # neu gerechnet: darf nicht gleich dem Grundmodell sein
    print(f"{arm}: GGUF {len(A)} Tensoren; gewählt (ffn_* in {len(schichten)} Schichten) {len(gew)}; "
          f"Rest ungleich Grundmodell {len(falsch_rest)} {falsch_rest[:3]}; gewählt falsch {len(falsch_gew)} {falsch_gew[:3]}")
    return not falsch_rest and not falsch_gew and len(gew) == 3 * len(schichten)


def selbsttest():
    ok = True
    tmp = tempfile.mkdtemp(prefix="t176_")
    rng = np.random.default_rng(0)

    def schreibe(d, tensoren):
        os.makedirs(d)
        h, daten, off = {}, b"", 0
        for k, a in tensoren.items():
            b = a.tobytes()
            h[k] = {"dtype": "BF16", "shape": list(a.shape), "data_offsets": [off, off + len(b)]}
            daten += b
            off += len(b)
        hb = json.dumps(h).encode()
        with open(os.path.join(d, DATEI), "wb") as f:
            f.write(struct.pack("<Q", len(hb)) + hb + daten)
        open(os.path.join(d, "config.json"), "w").write("{}")

    namen = [f"model.language_model.layers.{i}.mlp.{p}_proj.weight" for i in range(24) for p in ("gate", "up", "down")] + \
            [f"model.language_model.layers.{i}.linear_attn.out_proj.weight" for i in range(24)] + \
            ["mtp.layers.0.mlp.down_proj.weight", "model.language_model.embed_tokens.weight"]
    g32 = {k: rng.normal(0, 1, (4, 8)).astype(np.float32) for k in namen}
    s32 = {k: (g32[k] + rng.normal(0, 0.5, (4, 8))).astype(np.float32) for k in namen}
    sub = {k: W.bf16_bits(v) for k, v in g32.items()}
    main = {k: W.bf16_bits(v) for k, v in s32.items()}
    schreibe(os.path.join(tmp, "sub"), sub)
    schreibe(os.path.join(tmp, "main"), main)
    ordner = {"sub": os.path.join(tmp, "sub"), "main": os.path.join(tmp, "main")}
    aus = os.path.join(tmp, "aus")
    os.makedirs(aus)
    leer = os.devnull
    alt = sys.stdout
    try:
        sys.stdout = open(leer, "w")
        infos = {a: bauen(a, ordner, None, aus, pruef_sha=False) for a in ARME}
    finally:
        sys.stdout.close()
        sys.stdout = alt

    def lade(arm):
        p = os.path.join(aus, f"Qwen3.5-0.8B-{arm}", DATEI)
        h, o = kopf(p)
        return {k: np.frombuffer(roh(p, h, o, k), dtype=np.uint16) for k in h}

    A = {a: lade(a) for a in ARME}
    mlp = lambda i: [f"model.language_model.layers.{i}.mlp.{p}_proj.weight" for p in ("gate", "up", "down")]  # noqa: E731
    fr = sum((mlp(i) for i in range(12)), [])
    sp = sum((mlp(i) for i in range(12, 24)), [])
    gl = lambda x, y: np.array_equal(np.asarray(x).reshape(-1), np.asarray(y).reshape(-1))  # noqa: E731
    lam_ok = all(gl(A["m-mlp-l050"][k], W.bf16_bits(W.bf16_to_f32(main[k]) + 0.5 * (W.bf16_to_f32(sub[k]) - W.bf16_to_f32(main[k]))))
                 for k in fr + sp)
    faelle = [
        ("früh: Schichten 0–11 = Main", all(gl(A["r-mlp-frueh"][k], main[k]) for k in fr)),
        ("früh: Schichten 12–23 = Sub", all(gl(A["r-mlp-frueh"][k], sub[k]) for k in sp)),
        ("spät: Schichten 12–23 = Main, 0–11 = Sub", all(gl(A["r-mlp-spaet"][k], main[k]) for k in sp) and all(gl(A["r-mlp-spaet"][k], sub[k]) for k in fr)),
        ("mtp und andere bleiben Grundmodell", all(gl(A["r-mlp-frueh"][k], sub[k]) and gl(A["m-mlp-l100"][k], main[k]) for k in namen if k not in fr + sp)),
        ("λ = 1: MLP = Sub (byte-genau)", all(gl(A["m-mlp-l100"][k], sub[k]) for k in fr + sp)),
        ("λ = 0,5: Mitte, RNE", lam_ok),
        ("λ = 0,25 näher an Main als λ = 0,75", np.mean([np.abs(W.bf16_to_f32(A["m-mlp-l025"][k]) - W.bf16_to_f32(main[k]).reshape(-1)).mean() <
                                                        np.abs(W.bf16_to_f32(A["m-mlp-l075"][k]) - W.bf16_to_f32(main[k]).reshape(-1)).mean() for k in fr]) == 1.0),
        ("Zahl der gewählten Tensoren", [len(infos[a]["getauscht"]) for a in ARME] == [36, 36, 72, 72, 72, 72]),
        ("mischen: λ = 0 gibt Grund zurück", mischen(main[fr[0]].tobytes(), sub[fr[0]].tobytes(), 0.0) == main[fr[0]].tobytes()),
    ]
    try:
        bauen("r-mlp-frueh", ordner, None, aus, pruef_sha=False)
        faelle.append(("überschreibt nie", False))
    except SystemExit:
        faelle.append(("überschreibt nie", True))
    for name, g in faelle:
        ok &= bool(g)
        print(f"  {name:<44} {'OK' if g else 'FEHLER'}")
    shutil.rmtree(tmp, ignore_errors=True)
    print("SELBSTTEST 176 BESTANDEN" if ok else "SELBSTTEST 176 FEHLGESCHLAGEN")
    return ok


def trocken():
    ordner = {"sub": SUB_D, "main": MAIN_D}
    hs, _ = kopf(os.path.join(SUB_D, DATEI))
    for arm, d in ARME.items():
        gew = sorted(k for k in hs if re.search(d[2], k))
        lay = sorted({int(re.search(r"layers\.(\d+)\.", k).group(1)) for k in gew})
        print(f"{arm:<12} Grund {d[0]:<4} Spender {d[1]:<4} λ {d[3] if d[3] is not None else 'Bytes'}: {len(gew)} Tensoren, Schichten {lay[0]}–{lay[-1]}")
    print("TROCKEN 176: nichts gebaut", list(ordner))


if __name__ == "__main__":
    if "--selbsttest" in sys.argv:
        sys.exit(0 if selbsttest() else 1)
    if "--trocken" in sys.argv:
        trocken()
    elif "--bauen" in sys.argv:
        for a in sys.argv[sys.argv.index("--bauen") + 1:]:
            bauen(a, {"sub": SUB_D, "main": MAIN_D}, None, os.path.join(WURZEL, "modelle"))
    elif "--gguf" in sys.argv:
        sys.exit(0 if all([gguf_pruefen(a) for a in sys.argv[sys.argv.index("--gguf") + 1:]]) else 1)
