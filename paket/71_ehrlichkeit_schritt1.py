"""Ehrlichkeit, Schritt 1 (Nutzer-Go 07.11. kurz nach 15:00; Lesart vorab in ANNAHMEN 15:25): Würde die eingefrorene
Wahrheitssonde als äußere Regel („antworten nur bei WAHR, sonst ‚weiß ich nicht‘“) Fehler vermeiden, ohne viele richtige
Antworten zu kosten? Keine Modelländerung, keine neue Generierung (erzwungene Antworten kommen aus 60_antwort_zwang).
Abgegebene Antwort je Lauf:
  antwort    – letztes \\boxed im Antwortteil (nach </think>)
  erzwungen  – sonst die erzwungene Antwort (60_antwort_zwang, Variante „ende“)
  denken     – sonst (richtige Läufe ohne Antwortteil, von 60 nicht erzwungen) das letzte \\boxed im Denken
  keine      – sonst
Sondenwert = eingefrorene Schicht-13-Sonde am letzten Token des Antwort-Inhalts (schließende Klammer), wie 42 „anwenden“.
Ist die Endantwort schon in einer Kandidaten-Sammlung (42 sammeln, final) enthalten, wird der gespeicherte Zustand benutzt.
H1 (Argon): AUC auf den erzwungenen Antworten (alle Sätze zusammen) ≥ 0,75, sonst widerlegt.
H2: S₂ = (richtig − 2·falsch)/N mit Harnisch > ohne Harnisch (mit Erzwingen), alle Sätze zusammen.
Beschreibend: je Satz AUC, Risiko-Abdeckung, Enthaltungs-Reinheit (Anteil falscher unter den Enthaltungen), S₁/S₂/S₃
(ohne Erzwingen = offizielle Wertung, mit Erzwingen, mit Harnisch); 161–300 getrennt als frischer Teil.
Fortsetzbar (je Lauf eine Zeile in --aus .jsonl).
  python 71_ehrlichkeit_schritt1.py --laeufe "Set B · ERGORE 0,6=setB-ergore-t06" "161–300 · MIT=s3-mit-161-260+s3-mit-261-300" ...
      [--sammlungen ergebnisse/setB_kandidaten.npz ...] [--geraet cuda] [--nur-bewerten]
"""
import argparse
import importlib.util
import json
import os

import numpy as np

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(HIER)
ERG = os.path.join(WURZEL, "ergebnisse")
ZWANG = "\n\nThe final answer is $\\boxed{"


def lade_mod(name, pfad):
    s = importlib.util.spec_from_file_location(name, pfad)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


def klammer_ende(inhalt):
    """Index der schließenden Klammer des \\boxed{ (Tiefe 1 am Anfang) im erzwungenen Inhalt, sonst -1."""
    tiefe = 1
    for k, ch in enumerate(inhalt):
        tiefe += {"{": 1, "}": -1}.get(ch, 0)
        if tiefe == 0:
            return k
    return -1


def bewerten(E, thr, frisch_praefix="161–300"):
    erg = {"saetze": {}}
    namen = list(dict.fromkeys(e["satz"] for e in E))

    def kennzahlen(G):
        mit = [e for e in G if e["art"] != "keine"]
        y = np.array([e["korrekt"] for e in mit], bool)
        s = np.array([e["wert"] for e in mit], float)
        N = len(G)
        offiziell_r = sum(e["korrekt_offiziell"] for e in G)
        offiziell_f = sum((not e["korrekt_offiziell"]) and e["pred_offiziell"] for e in G)
        r, f = int(y.sum()), int((~y).sum())
        an = s >= thr
        r_h, f_h = int((y & an).sum()), int((~y & an).sum())
        ent, ent_f = int((~an).sum()), int((~y & ~an).sum())
        k = {"N": N, "mit_antwort": len(mit), "arten": {a: sum(e["art"] == a for e in G) for a in ("antwort", "erzwungen", "denken", "keine")},
             "richtig_offiziell": offiziell_r, "richtig_mit_zwang": r, "falsch_mit_zwang": f,
             "harnisch_richtig": r_h, "harnisch_falsch": f_h, "enthalten": ent, "enthalten_davon_falsch": ent_f,
             "enthaltungs_reinheit": ent_f / ent if ent else None,
             "richtige_verloren": int((y & ~an).sum()), "falsche_abgefangen": ent_f}
        wm = lade_mod("wm", os.path.join(HIER, "42_wahrheitsmelder.py"))
        k["auc"] = wm.auc(s, y) if len(set(y.tolist())) == 2 else None
        ez = [e for e in mit if e["art"] == "erzwungen"]
        if ez and len({e["korrekt"] for e in ez}) == 2:
            k["auc_erzwungen"] = wm.auc(np.array([e["wert"] for e in ez]), np.array([e["korrekt"] for e in ez], bool))
        else:
            k["auc_erzwungen"] = None
        k["n_erzwungen"], k["n_erzwungen_richtig"] = len(ez), sum(e["korrekt"] for e in ez)
        for lam in (1, 2, 3):
            k[f"S{lam}_offiziell"] = (offiziell_r - lam * offiziell_f) / N if N else None
            k[f"S{lam}_mit_zwang"] = (r - lam * f) / N if N else None
            k[f"S{lam}_harnisch"] = (r_h - lam * f_h) / N if N else None
        if len(s):
            ordn = np.argsort(-s)
            k["risiko_abdeckung"] = {f"{c}%": round(float(y[ordn[:max(1, int(round(len(s) * c / 100)))]].mean()), 3)
                                     for c in (100, 90, 80, 70, 60, 50, 40, 30, 20, 10)}
        return k

    for n in namen:
        erg["saetze"][n] = kennzahlen([e for e in E if e["satz"] == n])
    erg["alle"] = kennzahlen(E)
    frisch = [e for e in E if e["satz"].startswith(frisch_praefix)]
    if frisch:
        erg["frisch_161_300"] = kennzahlen(frisch)
    return erg


def drucke(erg, thr):
    def zeile(n, k):
        a = k["arten"]
        print(f"{n:34s} N {k['N']:4d} | Arten a/e/d/k {a['antwort']}/{a['erzwungen']}/{a['denken']}/{a['keine']} | "
              f"AUC {k['auc'] if k['auc'] is None else round(k['auc'], 3)} (erzw. "
              f"{k['auc_erzwungen'] if k['auc_erzwungen'] is None else round(k['auc_erzwungen'], 3)}, {k['n_erzwungen_richtig']}/{k['n_erzwungen']} richtig) | "
              f"richtig offiz./Zwang/Harnisch {k['richtig_offiziell']}/{k['richtig_mit_zwang']}/{k['harnisch_richtig']} | "
              f"falsch Zwang/Harnisch {k['falsch_mit_zwang']}/{k['harnisch_falsch']} | enthalten {k['enthalten']} "
              f"(davon falsch {k['enthalten_davon_falsch']}) | S2 offiz./Zwang/Harnisch "
              f"{k['S2_offiziell']:+.3f}/{k['S2_mit_zwang']:+.3f}/{k['S2_harnisch']:+.3f}")
    print(f"Schwelle (eingefroren 06.11.): {thr:.3f}")
    for n, k in erg["saetze"].items():
        zeile(n, k)
    if "frisch_161_300" in erg:
        zeile("== frisch (161–300)", erg["frisch_161_300"])
    zeile("== alle", erg["alle"])
    k = erg["alle"]
    print(f"Risiko-Abdeckung (alle): {k.get('risiko_abdeckung')}")
    h1 = k["auc_erzwungen"]
    print(f"URTEIL H1 (Argon) AUC erzwungene Antworten ≥ 0,75: "
          f"{'nicht beurteilbar' if h1 is None else ('BESTANDEN' if h1 >= 0.75 else 'WIDERLEGT')} (AUC {h1}, n {k['n_erzwungen']})")
    print(f"URTEIL H2 S₂ mit Harnisch > ohne (mit Zwang): {'BESTANDEN' if k['S2_harnisch'] > k['S2_mit_zwang'] else 'NICHT bestanden'} "
          f"({k['S2_harnisch']:+.3f} gegen {k['S2_mit_zwang']:+.3f}; S₁ {k['S1_harnisch']:+.3f}/{k['S1_mit_zwang']:+.3f}, "
          f"S₃ {k['S3_harnisch']:+.3f}/{k['S3_mit_zwang']:+.3f}; richtige verloren {k['richtige_verloren']}, "
          f"falsche abgefangen {k['falsche_abgefangen']})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--laeufe", nargs="+", required=True, help='"Satzname=dir1+dir2" (Ordner unter ergebnisse/)')
    ap.add_argument("--zwang-ordner", default=os.path.join(ERG, "antwort_zwang"))
    ap.add_argument("--sammlungen", nargs="*", default=[])
    ap.add_argument("--sonde", default=os.path.join(ERG, "wahrheitsmelder_eingefroren.npz"))
    ap.add_argument("--modell", default=os.path.join(WURZEL, "modelle", "Qwen3.5-0.8B-eigen-vL"))
    ap.add_argument("--geraet", default="cuda")
    ap.add_argument("--aus", default=os.path.join(ERG, "ehrlichkeit_schritt1.jsonl"))
    ap.add_argument("--nur-bewerten", action="store_true")
    ap.add_argument("--max-je-satz", type=int, default=0, help="nur Programmtest: höchstens so viele Läufe je Satz (kürzeste)")
    a = ap.parse_args()
    S = np.load(a.sonde)
    thr = float(S["thr"])
    L = int(S["schicht"])
    fertig = {}
    if os.path.exists(a.aus):
        for z in open(a.aus, encoding="utf-8"):
            e = json.loads(z)
            fertig[(e["satz"], e["lauf"])] = e
    if not a.nur_bewerten:
        wm = lade_mod("wm", os.path.join(HIER, "42_wahrheitsmelder.py"))
        import torch
        import transformers as tf
        torch.set_num_threads(int(os.environ.get("WSP_THREADS", 2)))
        tok = tf.AutoTokenizer.from_pretrained(os.path.join(WURZEL, "modelle", "Qwen3.5-0.8B"))
        zwang_ids = tok.encode(ZWANG, add_special_tokens=False)
        zu_zwang_ids = tok.encode("\n</think>" + ZWANG, add_special_tokens=False)
        gespeichert = {}
        for p in a.sammlungen:
            Z = np.load(p)
            for k_ in np.where(Z["final"])[0]:
                gespeichert[str(Z["lauf"][k_])] = Z[f"X_{L}"][k_]
        print(f"gespeicherte Endantwort-Zustände: {len(gespeichert)}", flush=True)
        speicher, model, notfall = {}, None, {"cpu": None, "probe": False}

        def wert(h):
            return float(((h.astype(np.float64) - S["mu"]) / S["sd"]) @ S["w"] + S["b"])

        with open(a.aus, "a", encoding="utf-8") as fo:
            for spec in a.laeufe:
                satz, dirs = spec.split("=", 1)
                for d in dirs.split("+"):
                    p = os.path.join(ERG, d, "ergebnisse.jsonl")
                    if not os.path.exists(p):
                        print(f"FEHLT: {p}", flush=True)
                        continue
                    R = [json.loads(z) for z in open(p, encoding="utf-8")]
                    if a.max_je_satz:
                        R = sorted(R, key=lambda r: len(r["gen_ids"]))[:a.max_je_satz]
                    zp = os.path.join(a.zwang_ordner, d + ".jsonl")
                    Zw = {}
                    if os.path.exists(zp):
                        for z in open(zp, encoding="utf-8"):
                            e = json.loads(z)
                            if e["variante"] == "ende":
                                Zw[e["id"]] = e
                    for r in R:
                        lauf = f"{d}/{r['id']}"
                        if (satz, lauf) in fertig:
                            continue
                        gen = r["gen_ids"]
                        stuecke = [tok.decode([t]) for t in gen]
                        text = "".join(stuecke)
                        zu_c = text.find("</think>")
                        boxed = [(s0, e) for s0, e, _ in wm.kandidaten_mit_ende(text) if text.startswith("\\boxed{", s0)]
                        im_antw = [(s0, e) for s0, e in boxed if zu_c >= 0 and s0 > zu_c]
                        rec = {"satz": satz, "lauf": lauf, "id": r["id"], "korrekt_offiziell": bool(r["korrekt"]),
                               "pred_offiziell": r.get("pred") is not None}
                        ids, pos = None, None
                        if im_antw or (r["korrekt"] and boxed and r["id"] not in Zw):
                            rec["art"] = "antwort" if im_antw else "denken"
                            rec["korrekt"] = bool(r["korrekt"])
                            s0, e = (im_antw or boxed)[-1]
                            grenzen = np.cumsum([len(s) for s in stuecke])
                            ti = min(int(np.searchsorted(grenzen, e - 1, side="right")), len(stuecke) - 1)
                            if rec["art"] == "antwort" and lauf in gespeichert:
                                rec["wert"], rec["quelle"] = wert(gespeichert[lauf]), "sammlung"
                            else:
                                ids, pos = r["prompt_ids"] + gen[:ti + 1], len(r["prompt_ids"]) + ti
                        elif r["id"] in Zw and Zw[r["id"]].get("pred"):
                            z = Zw[r["id"]]
                            k = klammer_ende(z["inhalt"])
                            if k < 0:
                                rec["art"] = "keine"
                            else:
                                rec["art"], rec["korrekt"] = "erzwungen", bool(z["korrekt"])
                                pre = r["prompt_ids"] + gen + (zwang_ids if zu_c >= 0 else zu_zwang_ids)
                                ids = pre + tok.encode(z["inhalt"][:k + 1], add_special_tokens=False)
                                pos = len(ids) - 1
                        else:
                            rec["art"] = "keine"
                        if ids is not None:
                            if model is None:
                                model = wm.lesemodell(a.modell, a.geraet, [L], speicher)
                            g_r = wm.vorwaerts(model, ids, a.geraet, speicher, notfall, a.modell, [L])
                            rec["wert"], rec["quelle"], rec["laenge"] = wert(speicher[L][pos].numpy()), g_r, len(ids)
                        fo.write(json.dumps(rec, ensure_ascii=False) + "\n")
                        fo.flush()
                        fertig[(satz, lauf)] = rec
                        print(f"{satz} {r['id']}: {rec['art']}, korrekt {rec.get('korrekt')}, Wert "
                              f"{rec.get('wert', float('nan')):.2f} ({rec.get('quelle', '-')})", flush=True)
    E = [e for e in fertig.values() if any(e["satz"] == s.split("=", 1)[0] for s in a.laeufe)]
    erg = bewerten(E, thr)
    drucke(erg, thr)
    json.dump(erg, open(a.aus.replace(".jsonl", "_bewertung.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
