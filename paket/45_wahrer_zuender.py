"""Wahrer Zünder (Nutzer-Idee „Sicherheit ERGO gib jetzt ab“; 06.11. ~14:15). Der eingefrorene Wahrheitsmelder (Schicht 13,
ergebnisse/wahrheitsmelder_eingefroren.npz) liest die Antwort-Kandidaten eines Laufs in Text-Reihenfolge; beim ERSTEN Kandidaten
mit Wert ≥ T_hoch wird abgebrochen und GENAU DIESER Kandidat abgegeben. Feuert der Zünder nie, bleibt der Lauf, wie er war.
Die Nachrechnung auf vorhandenen Läufen ist exakt: Das Tor schneidet nur ab, der Text bis dahin ist genau der erzeugte.
Schicht 13 liegt vor allen Eingriffen (Schicht 15/19) → derselbe Melder gilt für ERGORE, MIT und eigen.
Laufzeit-Tor, KEIN reiner Gewichtseingriff.

uebung: NUR Übungsdaten (wahrheit_sammlung.npz). Zurückgehaltene Werte wie beim Einfrieren (5-fach nach Aufgabe gruppiert).
        VORAB FESTGELEGTE Wahl von T_hoch: unter allen Schwellen, bei denen höchstens 2,5 % der richtig beendeten Übungsläufe
        verloren gehen (richtig → falsch), die mit dem größten Netto-Gewinn (gewonnen − verloren); bei Gleichstand die höhere.
        Kontrolle „gemischte Etiketten“: dieselbe Sonde und Wahl mit zufällig vertauschten Etiketten (Literatur-Hinweis).
test:   eingefrorene Sonde + T_hoch auf die Kandidaten der Testläufe (Sammlung: 42 sammeln --schichten 13 auf den Testläufen).
        Vergleichs-Regeln ohne Melder: B1 „erster Kandidat“, B2 „erster wiederholter Kandidat“ (gleich nach _norm).
  python 45_wahrer_zuender.py uebung --sammlung ergebnisse/wahrheit_sammlung.npz --aus ergebnisse/wahrer_zuender_uebung
  python 45_wahrer_zuender.py test --sammlung ergebnisse/zuender_test_sammlung.npz --uebung ergebnisse/wahrer_zuender_uebung.npz \
         --aus ergebnisse/wahrer_zuender_test.json
"""
import argparse
import importlib.util
import json
import os
from math import comb

import numpy as np

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(HIER)
ERG = os.path.join(WURZEL, "ergebnisse")
MODELLE = {"ERGORE": ["tag2-test40-kw75", "kw75-b"], "MIT": ["mit-vstil-L", "mit-vstil-L-b"], "eigen": ["eigen-vL", "eigen-vL-b"]}


def lade(name, pfad):
    s = importlib.util.spec_from_file_location(name, pfad)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


wm = lade("wm", os.path.join(HIER, "42_wahrheitsmelder.py"))
ev = lade("ev", os.path.join(WURZEL, "eval", "03_eval.py"))


def falten(aufgabe):
    eind = sorted(set(aufgabe))
    rng = np.random.default_rng(0)
    rng.shuffle(eind)
    f = {t: i % 5 for i, t in enumerate(eind)}
    return np.array([f[t] for t in aufgabe])


def oof_werte(X, y, f, lam):
    oof = np.zeros(len(y))
    for k in range(5):
        tr, te = f != k, f == k
        mu, sd = X[tr].mean(0), X[tr].std(0) + 1e-6
        w, b = wm.logreg((X[tr] - mu) / sd, y[tr].astype(float), lam)
        oof[te] = ((X[te] - mu) / sd) @ w + b
    return oof


def laeufe_laden(tags):
    """Alle Läufe der Tags, auch die ohne Kandidaten: 'tag/id' → korrekt, Tokens."""
    R = {}
    for t in tags:
        for z in open(os.path.join(ERG, t, "ergebnisse.jsonl"), encoding="utf-8"):
            r = json.loads(z)
            R[f"{t}/{r['id']}"] = {"korrekt": bool(r["korrekt"]), "tokens": int(r.get("tokens") or len(r["gen_ids"])), "id": r["id"]}
    return R


def je_lauf(lauf):
    d = {}
    for i, l in enumerate(lauf):
        d.setdefault(str(l), []).append(i)
    return d


def politik(R, K, y, feuert):
    out = {}
    for l, r in R.items():
        j = feuert(K.get(l, [])) if feuert else None
        out[l] = {"korrekt": bool(y[j]) if j is not None else r["korrekt"], "stopp": j}
    return out


def zuender(s, T):
    return lambda idx: next((i for i in idx if s[i] >= T), None)


def erster(idx):
    return idx[0] if idx else None


def wiederholt(kand):
    def f(idx):
        gesehen = set()
        for i in idx:
            k = ev._norm(str(kand[i]))
            if k and k in gesehen:
                return i
            gesehen.add(k)
        return None
    return f


def bilanz(R, P):
    g = sum(1 for l in R if P[l]["korrekt"] and not R[l]["korrekt"])
    v = sum(1 for l in R if not P[l]["korrekt"] and R[l]["korrekt"])
    return g, v


def waehle(R, K, y, s, anteil=0.025):
    n_r = sum(r["korrekt"] for r in R.values())
    grenze = int(np.floor(anteil * n_r))
    kurve = []
    for T in list(np.unique(s)) + [np.inf]:
        P = politik(R, K, y, zuender(s, T))
        g, v = bilanz(R, P)
        kurve.append({"T": float(T), "gewonnen": g, "verloren": v, "netto": g - v,
                      "gefeuert": sum(P[l]["stopp"] is not None for l in R)})
    zul = [k for k in kurve if k["verloren"] <= grenze]
    best = max(zul, key=lambda k: (k["netto"], k["T"]))
    return best, kurve, grenze, n_r


def uebung(a):
    Z = np.load(a.sammlung)
    y = Z["y"].astype(bool)
    X = Z["X_13"].astype(np.float64)
    lauf, aufgabe, kand = Z["lauf"], Z["aufgabe"], Z["kand"]
    f = falten(aufgabe)
    oof = oof_werte(X, y, f, a.lam)
    print(f"zurückgehaltene AUC Schicht 13: {wm.auc(oof, y):.3f} (Einfrieren: 0,959)")
    tags = sorted({str(l).split("/")[0] for l in lauf})
    R = laeufe_laden(tags)
    K = je_lauf(lauf)
    best, kurve, grenze, n_r = waehle(R, K, y, oof)
    print(f"Übungsläufe {len(R)} ({n_r} richtig, {len(K)} mit Kandidaten); erlaubt verloren ≤ {grenze}")
    print(f"GEWÄHLT T_hoch = {best['T']:.3f}: gewonnen {best['gewonnen']}, verloren {best['verloren']}, netto {best['netto']:+d}, "
          f"gefeuert in {best['gefeuert']} Läufen")
    for q in (0.0, 0.5, 0.8, 0.9, 0.95, 0.99):
        T = float(np.quantile(oof, q))
        k = min(kurve, key=lambda k: abs(k["T"] - T))
        print(f"   Kurve T={k['T']:7.3f}: gewonnen {k['gewonnen']:3d} verloren {k['verloren']:3d} netto {k['netto']:+4d} gefeuert {k['gefeuert']}")
    ergb = {}
    for name, fn in (("B1 erster Kandidat", erster), ("B2 erster wiederholter", wiederholt(kand))):
        g, v = bilanz(R, politik(R, K, y, fn))
        ergb[name] = {"gewonnen": g, "verloren": v, "netto": g - v}
        print(f"   {name}: gewonnen {g}, verloren {v}, netto {g - v:+d}")
    # Kontrolle: gemischte Etiketten (gleiche Sonde, gleiche Wahl; Ergebnis mit den WAHREN Etiketten bewertet)
    y_sh = np.random.default_rng(1).permutation(y)
    oof_sh = oof_werte(X, y_sh, f, a.lam)
    best_sh, _, _, _ = waehle(R, K, y, oof_sh)
    print(f"Kontrolle gemischte Etiketten: AUC {wm.auc(oof_sh, y):.3f}; T = {best_sh['T']:.3f}: gewonnen {best_sh['gewonnen']}, "
          f"verloren {best_sh['verloren']}, netto {best_sh['netto']:+d}")
    mu, sd = X.mean(0), X.std(0) + 1e-6
    w_sh, b_sh = wm.logreg((X - mu) / sd, y_sh.astype(float), a.lam)
    np.savez(a.aus + ".npz", T_hoch=best["T"], T_sh=best_sh["T"], w_sh=w_sh, b_sh=b_sh, mu_sh=mu, sd_sh=sd)
    json.dump({"T_hoch": best, "grenze_verloren": grenze, "uebung_richtig": n_r, "laeufe": len(R), "baselines": ergb,
               "kontrolle_gemischt": best_sh, "auc_oof": wm.auc(oof, y), "kurve": kurve},
              open(a.aus + ".json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(f"gespeichert: {a.aus}.npz / .json")


def mcnemar(x, y_):
    n = x + y_
    return min(1.0, 2 * sum(comb(n, i) for i in range(0, min(x, y_) + 1)) / 2 ** n) if n else 1.0


def test(a):
    Z = np.load(a.sammlung)
    S = np.load(a.sonde)
    U = np.load(a.uebung)
    T, T_sh = float(U["T_hoch"]), float(U["T_sh"])
    X = Z["X_13"].astype(np.float64)
    y = Z["y"].astype(bool)
    lauf, kand, tpos = Z["lauf"], Z["kand"], Z["tpos"]
    s = ((X - S["mu"]) / S["sd"]) @ S["w"] + S["b"]
    s_sh = ((X - U["mu_sh"]) / U["sd_sh"]) @ U["w_sh"] + U["b_sh"]
    K = je_lauf(lauf)
    MOD = json.loads(a.modelle) if a.modelle else MODELLE
    regeln = {"ohne Tor": None, "Zünder": zuender(s, T), "B1 erster Kandidat": erster, "B2 erster wiederholter": wiederholt(kand),
              "Zünder gemischte Etiketten": zuender(s_sh, T_sh)}
    aus, je_id = {}, {}
    print(f"T_hoch = {T:.3f} (Kontrolle {T_sh:.3f}); Kandidaten-Stellen {len(y)}; CPU-Notausgang "
          f"{int((Z['geraet'] == 'cpu').sum()) if 'geraet' in Z.files else 0}")
    for m, tags in MOD.items():
        R = laeufe_laden(tags)
        aus[m] = {}
        for rn, fn in regeln.items():
            P = politik(R, K, y, fn)
            g, v = bilanz(R, P)
            tok = {l: (int(tpos[P[l]["stopp"]]) + 1 if P[l]["stopp"] is not None else R[l]["tokens"]) for l in R}
            je_id[(m, rn)] = {R[l]["id"]: (P[l]["korrekt"], tok[l]) for l in R}
            aus[m][rn] = {"richtig": sum(P[l]["korrekt"] for l in R), "laeufe": len(R), "gewonnen": g, "verloren": v,
                          "gefeuert": sum(P[l]["stopp"] is not None for l in R),
                          "tokens_mittel": round(float(np.mean(list(tok.values()))))}
            d = aus[m][rn]
            print(f"  {m:6s} {rn:28s} richtig {d['richtig']:2d}/{d['laeufe']} | gewonnen {g:2d} verloren {v:2d} | "
                  f"gefeuert {d['gefeuert']:2d} | Ø Tokens {d['tokens_mittel']}")

    def vergleich(k1, k2):
        A, B = je_id[k1], je_id[k2]
        ids = sorted(set(A) & set(B))
        x = sum(A[i][0] and not B[i][0] for i in ids)
        z = sum(B[i][0] and not A[i][0] for i in ids)
        return {"n": len(ids), "a": sum(A[i][0] for i in ids), "b": sum(B[i][0] for i in ids), "nur_a": x, "nur_b": z,
                "p": mcnemar(x, z)}
    vg = {}
    for k1, k2 in ((("ERGORE", "Zünder"), ("MIT", "ohne Tor")), (("MIT", "Zünder"), ("MIT", "ohne Tor")),
                   (("ERGORE", "Zünder"), ("MIT", "Zünder")), (("ERGORE", "Zünder"), ("ERGORE", "ohne Tor")),
                   (("ERGORE", "Zünder"), ("ERGORE", "B2 erster wiederholter")), (("ERGORE", "Zünder"), ("ERGORE", "B1 erster Kandidat")),
                   (("ERGORE", "Zünder"), ("ERGORE", "Zünder gemischte Etiketten")), (("eigen", "Zünder"), ("eigen", "ohne Tor"))):
        if (k1 not in je_id) or (k2 not in je_id):
            continue
        c = vergleich(k1, k2)
        vg[f"{k1[0]}+{k1[1]} gegen {k2[0]}+{k2[1]}"] = c
        print(f"  {k1[0]}+{k1[1]} gegen {k2[0]}+{k2[1]}: {c['a']} gegen {c['b']} von {c['n']} | nur links {c['nur_a']}, "
              f"nur rechts {c['nur_b']}, McNemar p = {c['p']:.4f}")
    # Tokens auf Aufgaben, die mit UND ohne Zünder richtig sind (je Modell)
    for m in MOD:
        A, B = je_id[(m, "Zünder")], je_id[(m, "ohne Tor")]
        ids = [i for i in A if i in B and A[i][0] and B[i][0]]
        if ids:
            print(f"  Tokens {m} (beide richtig, {len(ids)} Aufgaben): mit Zünder {np.mean([A[i][1] for i in ids]):.0f}, "
                  f"ohne {np.mean([B[i][1] for i in ids]):.0f}")
    # VORAB FESTGELEGTE Lesart
    sicher = {m: aus[m]["Zünder"]["verloren"] <= int(np.floor(0.05 * aus[m]["ohne Tor"]["richtig"])) for m in MOD}
    for m in MOD:
        print(f"URTEIL Sicherheit {m}: verloren {aus[m]['Zünder']['verloren']} (erlaubt ≤ "
              f"{int(np.floor(0.05 * aus[m]['ohne Tor']['richtig']))}) → {'ERFÜLLT' if sicher[m] else 'NICHT erfüllt'}")
    h = vg["ERGORE+Zünder gegen MIT+ohne Tor"]
    if h["a"] > h["b"] and h["p"] < 0.05:
        u = "ÜBER MIT (signifikant) – mit Laufzeit-Tor"
    elif h["a"] > h["b"]:
        u = "Tendenz über MIT (nicht signifikant) – mit Laufzeit-Tor"
    else:
        u = "NICHT über MIT"
    f_ = vg["ERGORE+Zünder gegen MIT+Zünder"]
    print(f"URTEIL Hauptvergleich: {u} [ERGORE+Zünder {h['a']} gegen MIT {h['b']}, p = {h['p']:.4f}]; "
          f"Fairness: MIT+Zünder {f_['b']} (ERGORE+Zünder gegen MIT+Zünder p = {f_['p']:.4f})")
    z, b2, sh = aus["ERGORE"]["Zünder"], aus["ERGORE"]["B2 erster wiederholter"], aus["ERGORE"]["Zünder gemischte Etiketten"]
    mehrwert = (z["gewonnen"] - z["verloren"]) > max(b2["gewonnen"] - b2["verloren"], sh["gewonnen"] - sh["verloren"],
                                                    aus["ERGORE"]["B1 erster Kandidat"]["gewonnen"] - aus["ERGORE"]["B1 erster Kandidat"]["verloren"])
    print(f"URTEIL Mehrwert des Melders (ERGORE, netto): Zünder {z['gewonnen'] - z['verloren']:+d} gegen B1/B2/gemischt → "
          f"{'JA' if mehrwert else 'NEIN'}")
    json.dump({"T_hoch": T, "T_sh": T_sh, "modelle": aus, "vergleiche": vg, "sicherheit": sicher, "hauptvergleich": u,
               "mehrwert": bool(mehrwert)}, open(a.aus, "w", encoding="utf-8"), indent=1, ensure_ascii=False)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    u = sub.add_parser("uebung")
    u.add_argument("--sammlung", required=True); u.add_argument("--lam", type=float, default=50.0); u.add_argument("--aus", required=True)
    t = sub.add_parser("test")
    t.add_argument("--sammlung", required=True); t.add_argument("--uebung", required=True)
    t.add_argument("--sonde", default=os.path.join(ERG, "wahrheitsmelder_eingefroren.npz")); t.add_argument("--aus", required=True)
    t.add_argument("--modelle", default=None, help='JSON, z. B. {"ERGORE": ["kw75-c"], "MIT": ["mit-vstil-L-c"]} (Standard: 1–80)')
    a = ap.parse_args()
    {"uebung": uebung, "test": test}[a.cmd](a)


if __name__ == "__main__":
    main()
