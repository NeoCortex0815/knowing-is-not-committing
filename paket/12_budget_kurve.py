"""Alltagsprofil aus vorhandenen 03_eval-Ergebnissen: Trefferquote bei begrenztem Denkbudget (ohne neue Läufe).

Jede Antwort wird nach N Tokens abgeschnitten; gewertet wird das letzte \\boxed{} im abgeschnittenen Text
(math-verify, Hauptthread). Das ist eine UNTERGRENZE für den Alltag: ein Server mit --reasoning-budget N zwingt das
Modell nach N Tokens zur Antwort, statt sie zu verwerfen - dabei kann noch eine richtige Antwort herauskommen.

  python 12_budget_kurve.py --tokenizer MODELLE/Qwen3.5-0.8B ergebnisse/basis ergebnisse/mit [--budgets 2048,4096,...]
"""
import argparse
import importlib.util
import json
import os

from math_verify import parse, verify

KW_P = {"parsing_timeout": None} if os.name == "nt" else {}
KW_V = {"timeout_seconds": None} if os.name == "nt" else {}


def letztes_boxed(text):
    i = text.rfind("\\boxed")
    while i != -1:
        j = text.find("{", i)
        if j == -1:
            return None
        tiefe, k = 0, j
        while k < len(text):
            if text[k] == "{":
                tiefe += 1
            elif text[k] == "}":
                tiefe -= 1
                if tiefe == 0:
                    return text[j + 1:k]
            k += 1
        i = text.rfind("\\boxed", 0, i)
    return None


def richtig(pred, gold):
    if pred is None:
        return False
    try:
        return bool(verify(parse("\\boxed{" + gold + "}", **KW_P), parse("\\boxed{" + pred + "}", **KW_P), **KW_V))
    except Exception:
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("laeufe", nargs="+", help="Ordner mit ergebnisse.jsonl oder .jsonl-Dateien")
    ap.add_argument("--tokenizer", required=True)
    ap.add_argument("--budgets", default="2048,4096,8192,16384,32768")
    a = ap.parse_args()
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(a.tokenizer)
    budgets = [int(x) for x in a.budgets.split(",")]
    print("| Lauf | n | " + " | ".join(f"≤{b // 1024}k" for b in budgets) + " |")
    print("|---|---|" + "---|" * len(budgets))
    for lauf in a.laeufe:
        pfad = lauf if lauf.endswith(".jsonl") else os.path.join(lauf, "ergebnisse.jsonl")
        rs = [json.loads(z) for z in open(pfad, encoding="utf-8")]
        treffer = [0] * len(budgets)
        for r in rs:
            enc = tok(r["text"], add_special_tokens=False, return_offsets_mapping=True)
            offs = enc["offset_mapping"]
            for bi, b in enumerate(budgets):
                ende = offs[min(b, len(offs)) - 1][1] if offs else 0
                treffer[bi] += richtig(letztes_boxed(r["text"][:ende]), r["gold"])
        name = os.path.basename(os.path.normpath(lauf)).replace("ergebnisse.jsonl", "")
        print(f"| {name} | {len(rs)} | " + " | ".join(f"{t / len(rs):.1%}" for t in treffer) + " |")


if __name__ == "__main__":
    main()
