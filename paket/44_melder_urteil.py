"""Urteil zum eingefrorenen Wahrheitsmelder auf den Test-Endantworten (vorab festgelegt in ANNAHMEN, 06.11. ~13:50).
Liest die Ausgabe von `42_wahrheitsmelder.py anwenden` und wertet NUR aus (keine Schwellen-Änderung).
Hauptkriterium je Modell (Nutzer: „darf keine richtigen Antworten beeinflussen“): höchstens 5 % der RICHTIGEN Endantworten
als „unsicher“ markiert. Nebenkriterium: ≥ 40 % der FALSCHEN Endantworten markiert = brauchbar, ≥ 60 % = stark.
Beschreibend (nicht vorab als Kriterium festgelegt): AUC auf den Test-Endantworten, Tor-Bilanz („Tor an“: markierte Antwort wird
zu „Ich weiß es nicht sicher“), Wilson-Intervalle.
  python 44_melder_urteil.py --ein ergebnisse/wahrheitsmelder_test.json --aus ergebnisse/wahrheitsmelder_test_urteil.json
"""
import argparse
import json
from math import sqrt


def wilson(k, n, z=1.96):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    m = (p + z * z / (2 * n)) / (1 + z * z / n)
    h = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return (max(0.0, m - h), min(1.0, m + h))


def auc(pos, neg):
    """Wahrscheinlichkeit, dass eine richtige Endantwort einen höheren Wert hat als eine falsche (Gleichstand = 1/2)."""
    if not pos or not neg:
        return float("nan")
    s = sum((p > q) + 0.5 * (p == q) for p in pos for q in neg)
    return s / (len(pos) * len(neg))


def bewerte(E, name):
    g = [e for e in E if e["endantwort"]]
    r_ = [e for e in g if e["korrekt"]]
    f_ = [e for e in g if not e["korrekt"]]
    ohne = [e for e in E if not e["endantwort"]]
    kr, kf = sum(e["unsicher"] for e in r_), sum(e["unsicher"] for e in f_)
    qr = kr / len(r_) if r_ else float("nan")
    qf = kf / len(f_) if f_ else float("nan")
    haupt = bool(r_) and qr <= 0.05
    neben = "stark" if f_ and qf >= 0.60 else ("brauchbar" if f_ and qf >= 0.40 else "nicht erfüllt")
    d = {"modell": name, "laeufe": len(E), "endantworten": len(g), "ohne_endantwort": len(ohne),
         "richtig_end": len(r_), "falsch_end": len(f_),
         "richtige_markiert": kr, "quote_richtige_markiert": round(qr, 4), "wilson_richtige": [round(x, 3) for x in wilson(kr, len(r_))],
         "falsche_markiert": kf, "quote_falsche_markiert": round(qf, 4), "wilson_falsche": [round(x, 3) for x in wilson(kf, len(f_))],
         "hauptkriterium_erfuellt": haupt, "nebenkriterium": neben,
         "auc_test_endantworten": round(auc([e["wert"] for e in r_], [e["wert"] for e in f_]), 3),
         "cpu_notausgang": sum(e.get("geraet") == "cpu" for e in g),
         "tor_an": {"richtig_abgegeben": len(r_) - kr, "richtige_verloren": kr, "falsch_abgegeben": len(f_) - kf,
                    "falsche_abgefangen": kf, "ohne_endantwort_unveraendert": len(ohne)},
         "falsche_werte": sorted(e["wert"] for e in f_), "richtige_tiefste5": sorted(e["wert"] for e in r_)[:5]}
    return d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ein", required=True)
    ap.add_argument("--aus", required=True)
    a = ap.parse_args()
    E = json.load(open(a.ein, encoding="utf-8"))
    namen = sorted({e["modell"] for e in E})
    erg = [bewerte([e for e in E if e["modell"] == n], n) for n in namen] + [bewerte(E, "+".join(namen))]
    for d in erg:
        wr, wf = d["wilson_richtige"], d["wilson_falsche"]
        print(f"== {d['modell']}: Endantworten {d['endantworten']} (richtig {d['richtig_end']}, falsch {d['falsch_end']}; "
              f"ohne Endantwort {d['ohne_endantwort']}; CPU-Notausgang {d['cpu_notausgang']})")
        print(f"   richtige als unsicher markiert {d['richtige_markiert']}/{d['richtig_end']} = {100 * d['quote_richtige_markiert']:.1f} % "
              f"[95 %: {100 * wr[0]:.1f}–{100 * wr[1]:.1f}] → Hauptkriterium (≤ 5 %): {'ERFÜLLT' if d['hauptkriterium_erfuellt'] else 'NICHT erfüllt'}")
        print(f"   falsche als unsicher markiert {d['falsche_markiert']}/{d['falsch_end']} = {100 * d['quote_falsche_markiert']:.1f} % "
              f"[95 %: {100 * wf[0]:.1f}–{100 * wf[1]:.1f}] → Nebenkriterium: {d['nebenkriterium'].upper()}")
        t = d["tor_an"]
        print(f"   Tor an: {t['richtig_abgegeben']} richtig abgegeben, {t['richtige_verloren']} richtige verloren, "
              f"{t['falsche_abgefangen']} falsche abgefangen, {t['falsch_abgegeben']} falsche durchgerutscht | AUC (beschreibend) "
              f"{d['auc_test_endantworten']}")
        print(f"   Werte der falschen: {d['falsche_werte']} | tiefste richtige: {d['richtige_tiefste5']}")
    json.dump(erg, open(a.aus, "w", encoding="utf-8"), indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
