"""V2.2 = ERGORE (kw75) + „Zünder im Gewicht“ aus V2.1 (07.11. ~10:00, Nutzer-Go „Ja, umstellen“ für Bau und Offline-Prüfung).
Lehre aus Schritt 2: V2 und V2.1 haben ERGOREs Dauer-Druck (β-Term) weggelassen → das Modell bleibt im Denken hängen
(Gatter nie zu: 18/60 bei 0,6, 44/60 bei 1,0; ERGORE 0,6: 0). V2.2 behält ERGORE vollständig und setzt nur die 16 Gatter-
Neuronen aus V2.1 ein (gleiche gate/up-Zeilen = Wahrheit über hoher Schwelle × Kandidaten-Ende, down = κ_d·ĝ).
Bit-genaue Übertragung: ERGORE ändert nur down_proj 15/19 und dort nur die 64 Masken-Spalten (G liegt außerhalb) – geprüft.
  python 61_v22_bauen.py
"""
import json
import os
import sys

import numpy as np

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(HIER)
sys.path.insert(0, HIER)
import wsp_lib as W  # noqa: E402

BASIS = os.path.join(WURZEL, "modelle", "Qwen3.5-0.8B")
ERG = os.path.join(WURZEL, "modelle", "Qwen3.5-0.8B-kopplung-kw75")
ZIG = os.path.join(WURZEL, "modelle", "Qwen3.5-0.8B-ergo-zig")
AUS = os.path.join(WURZEL, "modelle", "Qwen3.5-0.8B-ergo-v22")
L = 15


def bits(m, name):
    return np.array(W.tensor_lesen(m, name)[1])


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--zuender", default=ZIG, help="Modell, aus dem die 16 WT-Neuronen übernommen werden (07.11.: auch ergo-zig4)")
    ap.add_argument("--aus", default=AUS)
    a = ap.parse_args()
    globals()["ZIG"], globals()["AUS"] = os.path.abspath(a.zuender), os.path.abspath(a.aus)
    mz = json.load(open(os.path.join(ZIG, "wsp_patch.json"), encoding="utf-8"))
    G = np.array(mz["neuronen"], dtype=np.int64)
    rest = np.setdiff1d(np.arange(10 ** 6), G)
    patches, pruef = {}, {}
    for k in ("gate", "up"):
        name = f"model.language_model.layers.{L}.mlp.{k}_proj.weight"
        e, z, b = bits(ERG, name), bits(ZIG, name), bits(BASIS, name)
        r = rest[rest < e.shape[0]]
        pruef[f"{k}_ergore_gleich_basis"] = bool((e == b).all())
        pruef[f"{k}_zig_ausserhalb_G_gleich_basis"] = bool((z[r] == b[r]).all())
        t = e.copy()
        t[G, :] = z[G, :]
        patches[name] = t
    name = f"model.language_model.layers.{L}.mlp.down_proj.weight"
    e, z, b = bits(ERG, name), bits(ZIG, name), bits(BASIS, name)
    pruef["down_ergore_G_spalten_gleich_basis"] = bool((e[:, G] == b[:, G]).all())
    pruef["down_ergore_geaenderte_spalten"] = int((e != b).any(0).sum())
    t = e.copy()
    t[:, G] = z[:, G]
    patches[name] = t
    print(json.dumps(pruef), flush=True)
    if not (pruef["gate_ergore_gleich_basis"] and pruef["up_ergore_gleich_basis"] and pruef["gate_zig_ausserhalb_G_gleich_basis"]
            and pruef["up_zig_ausserhalb_G_gleich_basis"] and pruef["down_ergore_G_spalten_gleich_basis"]):
        raise SystemExit("Annahme verletzt – Abbruch, nichts geschrieben")
    meta = {"art": "V2.2 = ERGORE (kw75) + Zünder im Gewicht aus V2.1 (16 Neuronen Schicht 15: gate = Wahrheit über τ_T, "
                   "up = Kandidaten-Ende, down = κ_d·ĝ)", "ergore": ERG, "zuender_aus": ZIG,
            **{k: mz[k] for k in ("neuronen", "tau_T", "tau_C", "kappa_g", "kappa_u", "kappa_d", "kappa", "gradient", "lern")},
            "pruefungen": pruef}
    W.modell_mit_patch(ERG, AUS, patches, meta)
    ok = json.load(open(os.path.join(ERG, "wsp_patch.json"), encoding="utf-8")).get("beta", {}).get("15") == 7.5
    print(f"Modell: {AUS} | ERGORE-Metadaten unverändert: {ok}", flush=True)


if __name__ == "__main__":
    main()
