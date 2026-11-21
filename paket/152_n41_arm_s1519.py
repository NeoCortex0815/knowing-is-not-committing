"""152: N41 – baut den Arm S-1519 (Original Qwen3.5-0.8B, nur mlp.down_proj der Schichten 15 und 19 aus SGNE-CC) als HF-Ordner.
Nur vorhandene Tensoren, kein Training, kein fremder Code. Prüft danach: gegenüber dem Original genau 2 Tensoren anders, und diese 2 sind
byte-gleich mit SGNE-CC.
  python paket/152_n41_arm_s1519.py
"""
import hashlib
import os
import shutil
import sys

import torch
from safetensors import safe_open
from safetensors.torch import save_file

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(HIER)
ORIG_D = os.path.join(WURZEL, "modelle", "Qwen3.5-0.8B")
ORIG = os.path.join(ORIG_D, "model.safetensors-00001-of-00001.safetensors")
SGNE = os.path.join(WURZEL, "modelle", "Qwen3.5-0.8B-sgne-cc", "model.safetensors")
SHA_SGNE = "d0b745ce6e48ff0b2b22f9dadf229ba246afabebd9ae8308f07a4cd1824d0324"
ZIEL_D = os.path.join(WURZEL, "modelle", "Qwen3.5-0.8B-s1519-hf")
TAUSCH = [f"model.language_model.layers.{L}.mlp.down_proj.weight" for L in (15, 19)]


def main():
    if os.path.exists(ZIEL_D):
        sys.exit(f"{ZIEL_D} gibt es schon – nichts überschrieben")
    if hashlib.sha256(open(SGNE, "rb").read()).hexdigest() != SHA_SGNE:
        sys.exit("SGNE-CC: Prüfsumme weicht ab")
    a, b = safe_open(ORIG, "pt"), safe_open(SGNE, "pt")
    T = {n: a.get_tensor(n) for n in a.keys()}
    for n in TAUSCH:
        T[n] = b.get_tensor(n).clone()
    os.makedirs(ZIEL_D)
    for f in sorted(os.listdir(ORIG_D)):
        if not f.endswith(".safetensors"):
            shutil.copy2(os.path.join(ORIG_D, f), os.path.join(ZIEL_D, f))
    aus = os.path.join(ZIEL_D, "model.safetensors-00001-of-00001.safetensors")
    save_file(T, aus, metadata={"format": "pt"})
    open(os.path.join(ZIEL_D, "HERKUNFT.txt"), "w", encoding="utf-8").write(
        "N41 Arm S-1519 (18.11.2026, Skript paket/152_n41_arm_s1519.py): Qwen/Qwen3.5-0.8B, darin nur mlp.down_proj der Schichten 15 und 19\n"
        "ersetzt durch die Tensoren aus Nondual-Observer/Qwen3.5-0.8B-SGNE-CC (Revision a0f617d4…, model.safetensors d0b745ce…).\n"
        "Lizenz: Apache-2.0 (Qwen3.5-0.8B; SGNE-CC laut seiner NOTICE). Geändert gegenüber SGNE-CC: alle übrigen 23 geänderten Tensoren\n"
        "zurück auf das Original gesetzt.\n")
    c = safe_open(aus, "pt")
    anders = [n for n in a.keys() if not torch.equal(a.get_tensor(n), c.get_tensor(n))]
    gleich_sgne = all(torch.equal(b.get_tensor(n), c.get_tensor(n)) for n in TAUSCH)
    print(f"gegenüber Original anders: {anders}")
    print(f"diese gleich mit SGNE-CC: {gleich_sgne}; Tensoren {len(list(c.keys()))}; SHA-256 {hashlib.sha256(open(aus, 'rb').read()).hexdigest()}")
    if sorted(anders) != sorted(TAUSCH) or not gleich_sgne:
        sys.exit("PRÜFUNG NICHT BESTANDEN")
    print("PRÜFUNG BESTANDEN")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
