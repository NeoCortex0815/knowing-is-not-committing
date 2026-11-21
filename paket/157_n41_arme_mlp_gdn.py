"""157: N41 – baut die Arme S-MLP und S-GDN als HF-Ordner (18.11.2026; Dave: „ja dann schnüre den Plan dafür“).
  S-MLP: Original Qwen3.5-0.8B, alle 15 geänderten mlp.down_proj aus SGNE-CC (Schichten 3, 7, 11–23), sonst Original.
  S-GDN: Original, die 9 geänderten linear_attn.out_proj und linear_attn.in_proj_a der Schicht 16 (Gate-Zeile) aus SGNE-CC, sonst Original.
Nur vorhandene Tensoren, kein Training, kein fremder Code. Prüft je Arm: gegenüber dem Original genau die getauschten Tensoren anders, und diese
byte-gleich mit SGNE-CC; zusammen ergeben S-MLP und S-GDN genau die 25 Tensoren von SGNE-CC.
  python paket/157_n41_arme_mlp_gdn.py
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


def main():
    if hashlib.sha256(open(SGNE, "rb").read()).hexdigest() != SHA_SGNE:
        sys.exit("SGNE-CC: Prüfsumme weicht ab")
    a, b = safe_open(ORIG, "pt"), safe_open(SGNE, "pt")
    anders = sorted(n for n in a.keys() if not torch.equal(a.get_tensor(n), b.get_tensor(n)))
    mlp = [n for n in anders if n.endswith("mlp.down_proj.weight")]
    gdn = [n for n in anders if n.endswith("linear_attn.out_proj.weight") or n.endswith("linear_attn.in_proj_a.weight")]
    print(f"SGNE-CC gegen Original: {len(anders)} Tensoren, davon down_proj {len(mlp)}, GatedDeltaNet {len(gdn)}")
    if len(anders) != 25 or len(mlp) != 15 or len(gdn) != 10 or sorted(mlp + gdn) != anders:
        sys.exit("Aufteilung stimmt nicht")
    for name, tausch in (("s-mlp", mlp), ("s-gdn", gdn)):
        ziel = os.path.join(WURZEL, "modelle", f"Qwen3.5-0.8B-{name}-hf")
        if os.path.exists(ziel):
            sys.exit(f"{ziel} gibt es schon – nichts überschrieben")
        T = {n: a.get_tensor(n) for n in a.keys()}
        for n in tausch:
            T[n] = b.get_tensor(n).clone()
        os.makedirs(ziel)
        for f in sorted(os.listdir(ORIG_D)):
            if not f.endswith(".safetensors"):
                shutil.copy2(os.path.join(ORIG_D, f), os.path.join(ziel, f))
        aus = os.path.join(ziel, "model.safetensors-00001-of-00001.safetensors")
        save_file(T, aus, metadata={"format": "pt"})
        open(os.path.join(ziel, "HERKUNFT.txt"), "w", encoding="utf-8").write(
            f"N41 Arm {name.upper()} (18.11.2026, Skript paket/157_n41_arme_mlp_gdn.py): Qwen/Qwen3.5-0.8B, darin {len(tausch)} Tensoren ersetzt\n"
            "durch die aus Nondual-Observer/Qwen3.5-0.8B-SGNE-CC (Revision a0f617d4…, model.safetensors d0b745ce…):\n  " + "\n  ".join(tausch) +
            "\nLizenz: Apache-2.0 (Qwen3.5-0.8B; SGNE-CC laut seiner NOTICE). Alle übrigen Tensoren wie im Original.\n")
        c = safe_open(aus, "pt")
        neu_anders = sorted(n for n in a.keys() if not torch.equal(a.get_tensor(n), c.get_tensor(n)))
        gleich = all(torch.equal(b.get_tensor(n), c.get_tensor(n)) for n in tausch)
        sha = hashlib.sha256(open(aus, "rb").read()).hexdigest()
        print(f"{name}: anders gegenüber Original {len(neu_anders)} (soll {len(tausch)}), gleich SGNE-CC {gleich}, SHA-256 {sha}")
        if neu_anders != sorted(tausch) or not gleich:
            sys.exit(f"{name}: PRÜFUNG NICHT BESTANDEN")
    print("PRÜFUNG BESTANDEN")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
