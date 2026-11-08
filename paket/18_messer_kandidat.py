"""Messerschneiden zusammenführen und über einen Kandidaten entscheiden (für kette_messer.sh).

  mischen:  python 18_messer_kandidat.py mischen --diagnose ergebnisse/diagnose-vL/ergebnisse.jsonl \
                --berichte ergebnisse/messer_bericht.json ergebnisse/messer_b_bericht.json --aus ergebnisse/messer_alle.jsonl
            Messerschneide = Punkt mit >= 1 Schleifen- und >= 1 Produktiv-Ast; je Klasse höchstens --je-ast Äste,
            markiert werden ALLE Tokens des Asts (klasse_a = Schleife, klasse_b = produktiv) -> Eingabe für 04s --kontrast

  waehle:   python 18_messer_kandidat.py waehle --modell modelle/Qwen3.5-0.8B --messer ergebnisse/richtung-messer3.npz \
                --alt ergebnisse/richtung-vL-alle.npz --mit minipc/mit_richtung.npz --aus ergebnisse/messer_kandidat.npz
            Kandidaten: "messer" (Richtung + Spalten aus den Messerschneiden) und "mischung" (normierte Summe aus alter und
            Messer-Richtung; Spalten nach unserer Regel da*w mit da aus den alten 48 Transkripten).
            Bestehen nur, wenn in JEDER Schicht cos(u, MIT-u) >= --min-cos UND Treffer mit MIT-Spalten >= Treffer der alten
            Richtung (bisher 41/30). Die MIT-Richtung dient nur als MASSSTAB zur Auswahl, nicht als Zutat.
            Letzte Zeile: "KANDIDAT: <name>" oder "KEIN KANDIDAT".
"""
import argparse
import importlib.util
import json
import os

import numpy as np

HIER = os.path.dirname(os.path.abspath(__file__))


def mischen(a):
    diag = {json.loads(z)["id"]: json.loads(z) for z in open(a.diagnose, encoding="utf-8") if z.strip()}
    zeilen, n, gesehen = [], 0, set()
    for pfad in a.berichte:
        for p in json.load(open(pfad, encoding="utf-8"))["punkte"]:
            key = (p["id"], p["cut"])
            if key in gesehen:
                continue
            gesehen.add(key)
            sch = [f for f in p.get("aeste", []) if f["klasse"] == "schleife"]
            pro = [f for f in p.get("aeste", []) if f["klasse"] == "produktiv"]
            if not sch or not pro:
                continue
            n += 1
            m = min(len(sch), len(pro), a.je_ast)
            r = diag[p["id"]]
            praefix = r["gen_ids"][:p["cut"]]
            for klasse, aeste in (("schleife", sch[:m]), ("produktiv", pro[:m])):
                for f in aeste:
                    idx = list(range(p["cut"], p["cut"] + len(f["ids"])))
                    zeilen.append({"id": f"{p['id']}@{p['cut']}#{f['seed']}", "prompt_ids": r["prompt_ids"],
                                   "gen_ids": praefix + f["ids"], "klasse_a": idx if klasse == "schleife" else [],
                                   "klasse_b": idx if klasse == "produktiv" else []})
    with open(a.aus, "w", encoding="utf-8") as fh:
        for z in zeilen:
            fh.write(json.dumps(z) + "\n")
    print(f"MESSERSCHNEIDEN gesamt: {n}, Zeilen für 04s: {len(zeilen)} (aus {len(a.berichte)} Berichten)")


def waehle(a):
    spec = importlib.util.spec_from_file_location("av", os.path.join(HIER, "16_auswahl_vergleich.py"))
    av = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(av)
    K, A, M = dict(np.load(a.messer)), dict(np.load(a.alt)), dict(np.load(a.mit))
    schichten = [int(x) for x in a.schichten.split(",")]
    cos = lambda x, y: float(abs(x @ y) / np.linalg.norm(x) / np.linalg.norm(y))
    kand = {"messer": {}, "mischung": {}}
    alt_treffer = {}
    for L in schichten:
        Wd = av.lade_wd(a.modell, L, a.muster)
        um, ua, uk = (d[f"u_{L}"].astype(np.float64) for d in (M, A, K))
        mit = set(M[f"spalten_{L}"].tolist())
        wa = ua @ Wd
        da_alt = np.where(np.abs(wa) > 1e-12, A[f"score_{L}"] / np.where(np.abs(wa) > 1e-12, wa, 1), 0.0)
        alt_treffer[L] = len(set(np.argsort(-(da_alt * wa))[:a.k].tolist()) & mit)
        sp_k = K[f"spalten_{L}"]
        kand["messer"][L] = {"u": uk / np.linalg.norm(uk), "spalten": np.sort(sp_k)}
        ux = ua / np.linalg.norm(ua) + uk / np.linalg.norm(uk)
        ux /= np.linalg.norm(ux)
        sp_x = np.sort(np.argsort(-(da_alt * (ux @ Wd)))[:a.k])
        kand["mischung"][L] = {"u": ux, "spalten": sp_x}
        for name in kand:
            c = kand[name][L]
            c["cos"] = cos(c["u"], um)
            c["treffer"] = len(set(c["spalten"].tolist()) & mit)
    print(f"Maßstab alte Richtung: Treffer {', '.join(f'L{L} {alt_treffer[L]}' for L in schichten)}")
    bestanden = []
    for name, c in kand.items():
        ok = all(c[L]["cos"] >= a.min_cos and c[L]["treffer"] >= alt_treffer[L] for L in schichten)
        print(f"{name:9s}: " + " | ".join(f"L{L} cos {c[L]['cos']:.3f} Treffer {c[L]['treffer']}" for L in schichten)
              + f"  -> {'BESTANDEN' if ok else 'nicht bestanden'}")
        if ok:
            bestanden.append((np.mean([c[L]["cos"] for L in schichten]), name))
    if not bestanden:
        print("KEIN KANDIDAT")
        return
    name = max(bestanden)[1]
    out = {}
    for L in schichten:
        out[f"u_{L}"] = kand[name][L]["u"].astype(np.float32)
        out[f"spalten_{L}"] = kand[name][L]["spalten"].astype(np.int64)
    np.savez(a.aus, **out)
    json.dump({"kandidat": name, **{f"L{L}": {"cos_mit": round(kand[name][L]["cos"], 4),
                                              "treffer_mit": kand[name][L]["treffer"]} for L in schichten}},
              open(os.path.splitext(a.aus)[0] + ".json", "w"), indent=1)
    print(f"KANDIDAT: {name}")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("mischen")
    m.add_argument("--diagnose", required=True)
    m.add_argument("--berichte", nargs="+", required=True)
    m.add_argument("--je-ast", type=int, default=3)
    m.add_argument("--aus", required=True)
    w = sub.add_parser("waehle")
    w.add_argument("--modell", required=True)
    w.add_argument("--messer", required=True)
    w.add_argument("--alt", required=True)
    w.add_argument("--mit", required=True)
    w.add_argument("--schichten", default="15,19")
    w.add_argument("--k", type=int, default=64)
    w.add_argument("--min-cos", type=float, default=0.80)
    w.add_argument("--muster", default="model.language_model.layers.{L}.mlp.down_proj.weight")
    w.add_argument("--aus", required=True)
    a = ap.parse_args()
    mischen(a) if a.cmd == "mischen" else waehle(a)


if __name__ == "__main__":
    main()
