"""Zustand „Klingel gehört“ (Idee 06.11.: innere Uhr; Fallstrick Wortspuren nach Argon -> Minimalpaar mit Kontrollsatz).

Denktexte werden an Schnittpunkten abgeschnitten; angehängt wird entweder der trainierte Qwen-Budget-Satz (Klingel) oder ein
Kontrollsatz gleicher Token-Länge, der sich nur an 3 Stellen unterscheidet (time→detail, give→check, directly→carefully).
Danach ein gleiches Füll-Token, damit die Position NACH dem Satz gemessen werden kann (04s misst Token g an Position g−1).
klasse_a = letzte --fenster Positionen im Klingel-Satz, klasse_b = dieselben Positionen im Kontroll-Satz.
Paare abwechselnd angeordnet (Klingel/Kontrolle, Kontrolle/Klingel …), damit 04s die Stabilität (Hälften) berechnen kann.
  python 24_klingel_zustand.py --ergebnisse ergebnisse/entschluss-uebung-eigen/ergebnisse.jsonl ergebnisse/diagnose-vL/ergebnisse.jsonl \
      --tokenizer modelle/Qwen3.5-0.8B --schnitte 1536,3072 --aus ergebnisse/klingel_zustand.jsonl
"""
import argparse
import json

KLINGEL = "\n\nConsidering the limited time by the user, I have to give the solution based on the thinking directly now.\n"
KONTROLLE = "\n\nConsidering the limited detail by the user, I have to check the solution based on the thinking carefully now.\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ergebnisse", nargs="+", required=True)
    ap.add_argument("--tokenizer", required=True)
    ap.add_argument("--schnitte", default="1536,3072")
    ap.add_argument("--fenster", type=int, default=4)
    ap.add_argument("--max-je-datei", type=int, default=40)
    ap.add_argument("--aus", required=True)
    a = ap.parse_args()
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(a.tokenizer)
    k_ids, c_ids = tok.encode(KLINGEL, add_special_tokens=False), tok.encode(KONTROLLE, add_special_tokens=False)
    assert len(k_ids) == len(c_ids), (len(k_ids), len(c_ids))
    zu = tok.convert_tokens_to_ids("</think>")
    fueller = tok.encode("\n", add_special_tokens=False)[0]
    n_satz = len(k_ids)
    zeilen, paar = [], 0
    for pfad in a.ergebnisse:
        for z in list(open(pfad, encoding="utf-8"))[:a.max_je_datei]:
            r = json.loads(z)
            gen = r["gen_ids"]
            for s in map(int, a.schnitte.split(",")):
                if len(gen) <= s or zu in gen[:s]:
                    continue
                idx = list(range(s + n_satz - a.fenster + 1, s + n_satz + 1))  # Token-Indizes -> gemessen an Position g−1
                rec = {}
                for name, satz in (("klingel", k_ids), ("kontrolle", c_ids)):
                    rec[name] = {"id": f"{r['id']}@{s}:{name}", "prompt_ids": r["prompt_ids"],
                                 "gen_ids": gen[:s] + satz + [fueller],
                                 "klasse_a": idx if name == "klingel" else [], "klasse_b": idx if name == "kontrolle" else []}
                reihenfolge = ("klingel", "kontrolle") if paar % 2 == 0 else ("kontrolle", "klingel")
                zeilen += [rec[n] for n in reihenfolge]
                paar += 1
    with open(a.aus, "w", encoding="utf-8") as fh:
        for z in zeilen:
            fh.write(json.dumps(z) + "\n")
    print(f"KLINGEL-ZUSTAND: {paar} Satzpaare ({len(zeilen)} Zeilen), Satzlänge {n_satz} Tokens, Fenster {a.fenster} -> {a.aus}")


if __name__ == "__main__":
    main()
