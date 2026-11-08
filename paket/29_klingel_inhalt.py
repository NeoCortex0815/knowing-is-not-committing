"""Klingel nach Inhalt (06.11., Folge aus „faire Klingel greift ins Leere“): Verhaspeln erkennen statt Impuls verstärken.
Regel (kennt die Lösung NICHT): Sobald ein Antwort-Kandidat im Denken steht (\boxed{…} / „answer is …“), zählen wir die
Zweifel-Marker DANACH (Wait, Hmm, double-check, verify, Alternatively, re-read, Actually …). Kommt kein ANDERER Kandidat dazu und
erreichen die Zweifel-Marker m, läutet die Klingel: Antwort = dieser Kandidat. Ein neuer, anderer Kandidat setzt den Zähler zurück.
  python 29_klingel_inhalt.py --tokenizer modelle/Qwen3.5-0.8B --m 3,5,10,20 --laeufe ergebnisse/entschluss-uebung-eigen
"""
import argparse, importlib.util, json, os
HIER = os.path.dirname(os.path.abspath(__file__))
def lade(n, d):
    s = importlib.util.spec_from_file_location(n, os.path.join(HIER, d)); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tokenizer", required=True); ap.add_argument("--laeufe", nargs="+", required=True); ap.add_argument("--m", default="3,5,10,20")
    a = ap.parse_args()
    ev = lade("ev", os.path.join("..", "eval", "03_eval.py")); kr = lade("kr", "23_klingel_regel.py"); am = lade("am", "22_angstmarker.py")
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(a.tokenizer)
    for lauf in a.laeufe:
        rs = [json.loads(z) for z in open(os.path.join(lauf, "ergebnisse.jsonl"), encoding="utf-8")]
        vor = []
        for r in rs:
            text = tok.decode(r["gen_ids"]); denk = text.split("</think>")[0]
            kand = [(p, kr.norm(c)) for p, c in kr.kandidaten(denk) if kr.norm(c)]
            zweifel = [m.start() for m in am.MARKER.finditer(denk)]
            vor.append((r, len(text), kand, zweifel))
        echt = sum(bool(r.get("korrekt")) for r, *_ in vor)
        print(f"\n== {os.path.basename(lauf)}: {len(rs)} Aufgaben, tatsächlich richtig {echt}")
        for m in map(int, a.m.split(",")):
            richtig = gel = falsch = gerettet = verloren = 0; gespart = []
            for r, L, kand, zweifel in vor:
                hit = None
                for i, (p, c) in enumerate(kand):
                    naechster_anderer = next((q for q, d in kand[i + 1:] if d != c), None)
                    nach = [z for z in zweifel if z > p and (naechster_anderer is None or z < naechster_anderer)]
                    if len(nach) >= m:
                        hit = (nach[m - 1], c); break
                ok_echt = bool(r.get("korrekt"))
                if hit:
                    gel += 1; ok = bool(ev.korrekt(hit[1], r.get("gold"))); richtig += ok; falsch += not ok
                    gerettet += ok and not ok_echt; verloren += ok_echt and not ok
                    gespart.append(len(r["gen_ids"]) - int(len(r["gen_ids"]) * hit[0] / max(L, 1)))
                else:
                    richtig += ok_echt
            print(f"  m={m:2d}: geläutet {gel:2d} | richtig gesamt {richtig:2d} (gerettet {gerettet}, verloren {verloren}) | "
                  f"falsch geläutet {falsch:2d} | gespart je Läuten {sum(gespart) / max(len(gespart), 1):,.0f} Tok")
if __name__ == "__main__":
    main()
