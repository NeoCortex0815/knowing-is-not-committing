"""Ergebnisse mehrerer Eval-Läufe nebeneinander, gepaart gegen den ersten (Basis).

  python 06_vergleich.py ergebnisse/basis ergebnisse/mit ergebnisse/eigen ergebnisse/zufall
"""
import json
import os
import sys


def lade(d):
    return {json.loads(z)["id"]: json.loads(z) for z in open(os.path.join(d, "ergebnisse.jsonl"), encoding="utf-8")}


def main(dirs):
    runs = [(os.path.basename(d.rstrip("/")), lade(d)) for d in dirs]
    gemeinsam = set.intersection(*[set(r) for _, r in runs])
    basis = runs[0][1]
    print(f"Gemeinsame Aufgaben: {len(gemeinsam)}\n")
    print("| Lauf | korrekt | Loop/Limit | eos | </think> | Ø Tokens | Ø dup8 | gerettet | verloren |")
    print("|---|---|---|---|---|---|---|---|---|")
    for name, r in runs:
        xs = [r[i] for i in gemeinsam]
        n = len(xs)
        ger = sum(r[i]["korrekt"] and not basis[i]["korrekt"] for i in gemeinsam)
        verl = sum(basis[i]["korrekt"] and not r[i]["korrekt"] for i in gemeinsam)
        print(f"| {name} | {sum(x['korrekt'] for x in xs) / n:.1%} "
              f"| {sum(x['ende'] in ('limit', 'loop_abbruch') for x in xs) / n:.1%} "
              f"| {sum(x['ende'] == 'eos' for x in xs) / n:.1%} | {sum(x['think_zu'] for x in xs) / n:.1%} "
              f"| {sum(x['tokens'] for x in xs) / n:,.0f} | {sum(x['tail_dup8'] for x in xs) / n:.2f} "
              f"| {ger} | {verl} |")


if __name__ == "__main__":
    main(sys.argv[1:])
