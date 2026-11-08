"""(N20/N22) Zweifach-Intuition: „die Intuition zweimal fragen“ (08.11.; Lesarten vorab in ANNAHMEN 13:12 und 13:25).
Gleich = beide Seeds liefern ein \\boxed{} und die Antworten sind gleichwertig (math_verify in beide Richtungen, wie 03_eval).
Signal Δ = P(Seed 0 richtig | gleich) − P(Seed 0 richtig | verschieden):
  „trägt“ bei Δ ≥ 30 Punkte UND P(richtig | gleich) ≥ 70 %; „widerlegt“ bei Δ ≤ 15 Punkte; sonst „offen“.
Weiche (nur N20): gleich → INT-Antwort, sonst Hinterzimmer (WT-A Seed 0): „lohnt“ bei ≥ max(INT, WT-A) + 3, „lohnt nicht“ bei
≤ max; sonst „offen“. Beschreibend: MIT/ERGORE als Hinterzimmer, Tokens, gedeckelte schnelle Intuition (2.000 / 4.000 Tokens).
  python 104_zweifach_intuition.py
"""
import importlib.util
import json
import os
import sys

WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ERG = os.path.join(WURZEL, "ergebnisse")
SAETZE = {
    "N20 161–260 (Hauptauswertung)": (["s3-int-eigen-161-210", "s3-int-eigen-211-260"],
                                      ["s3-int-eigen-161-185-s1", "s3-int-eigen-186-210-s1", "s3-int-eigen-211-260-s1"], 100),
    "261–300 (schon gesehen, nur beschreibend)": (["s3-int-eigen-261-300"], ["s3-int-eigen-261-300-s1"], 40),
    "N22 neue Trainingsaufgaben": (["neu40-int-eigen-s0"], ["neu40-int-eigen-s1"], 40),
}
HINTER = {"WT-A": ["s3-wta-161-210", "s3-wta-211-260", "s3-wta-261-300"], "MIT": ["s3-mit-161-260", "s3-mit-261-300"],
          "ERGORE": ["s3-ergore-161-260", "s3-ergore-261-300"]}


def laufe(dirs):
    R = {}
    for d in dirs:
        p = os.path.join(ERG, d, "ergebnisse.jsonl")
        if os.path.exists(p):
            for z in open(p, encoding="utf-8"):
                r = json.loads(z)
                R[r["id"]] = r
    return R


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    s = importlib.util.spec_from_file_location("ev", os.path.join(WURZEL, "eval", "03_eval.py"))
    ev = importlib.util.module_from_spec(s)
    s.loader.exec_module(ev)
    H = {k: laufe(v) for k, v in HINTER.items()}
    B = {}
    for name, (d0, d1, soll) in SAETZE.items():
        A, C = laufe(d0), laufe(d1)
        ids = sorted(set(A) & set(C))
        print(f"\n== {name}: {len(ids)} Paare von {soll}")
        if len(ids) < soll:
            print("   noch nicht vollständig – kein Urteil")
            continue

        def gleich(i, deckel=None):
            a, c = A[i], C[i]
            if deckel and (a["tokens"] > deckel or c["tokens"] > deckel):
                return False
            pa, pc = a["pred"], c["pred"]
            return pa is not None and pc is not None and (ev.korrekt(pa, pc) or ev.korrekt(pc, pa))
        for deckel in (None, 4000, 2000):
            G = [i for i in ids if gleich(i, deckel)]
            V = [i for i in ids if i not in G]
            pg = 100 * sum(A[i]["korrekt"] for i in G) / max(1, len(G))
            pv = 100 * sum(A[i]["korrekt"] for i in V) / max(1, len(V))
            d = pg - pv
            kopf = "ohne Deckel" if deckel is None else f"Deckel {deckel}"
            print(f"   {kopf:12s}: gleich {len(G):3d} (richtig {pg:3.0f} %) | verschieden {len(V):3d} (Seed 0 richtig {pv:3.0f} %) | "
                  f"Δ {d:+.0f} Punkte")
            if deckel is None:
                urteil = "trägt" if (d >= 30 and pg >= 70) else ("widerlegt" if d <= 15 else "offen")
                B[name] = {"gleich": len(G), "p_gleich": pg, "p_versch": pv, "delta": d, "urteil": urteil}
                print(f"   URTEIL Signal (vorab): {urteil}")
            # Weiche: gleich → INT, sonst Hinterzimmer
            if not name.startswith("N22"):
                ri = sum(A[i]["korrekt"] for i in ids)
                for hn, Hd in H.items():
                    if not all(i in Hd for i in ids):
                        continue
                    rw = sum(A[i]["korrekt"] for i in G) + sum(Hd[i]["korrekt"] for i in V)
                    rh = sum(Hd[i]["korrekt"] for i in ids)
                    tok_i = sum(min(A[i]["tokens"], deckel or 10 ** 9) + min(C[i]["tokens"], deckel or 10 ** 9) for i in ids)
                    tok_w = tok_i + sum(Hd[i]["tokens"] for i in V)
                    zeile = (f"      Weiche → {hn:6s}: richtig {rw:3d} (INT allein {ri}, {hn} allein {rh}) | Tokens {tok_w / 1000:.0f}k "
                             f"gegen {hn} allein {sum(Hd[i]['tokens'] for i in ids) / 1000:.0f}k")
                    if hn == "WT-A" and deckel is None and name.startswith("N20"):
                        m = max(ri, rh)
                        uw = "lohnt" if rw >= m + 3 else ("lohnt nicht" if rw <= m else "offen")
                        zeile += f"  → URTEIL Weiche (vorab): {uw}"
                        B[name]["weiche"] = {"richtig": rw, "int": ri, "wta": rh, "urteil": uw}
                    print(zeile)
    json.dump(B, open(os.path.join(ERG, "zweifach_intuition.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
