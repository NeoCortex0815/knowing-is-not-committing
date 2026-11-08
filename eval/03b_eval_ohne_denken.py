"""03_eval.py ohne Denken (Denk-Weiche, Nutzer-Go 07.11. kurz nach 15:00; Argons Prüfprotokoll): Der Prompt endet mit dem
offiziellen Qwen3.5-Nicht-Denk-Muster `<think>\\n\\n</think>\\n\\n` (chat_template.jinja, enable_thinking = false) statt mit
`<think>\\n`. Alles andere – Sampling, Budget, Loop-Abbruch, Bewertung, Ausgabeformat – ist unverändert 03_eval.py; diese Datei
ändert 03_eval.py NICHT (laufende Ketten benutzen es weiter).
  python eval/03b_eval_ohne_denken.py <gleiche Argumente wie 03_eval.py>
"""
import importlib.util
import json
import os
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
_s = importlib.util.spec_from_file_location("ev", os.path.join(HIER, "03_eval.py"))
ev = importlib.util.module_from_spec(_s)
_s.loader.exec_module(ev)
assert ev.SUFFIX.endswith("<think>\n"), "unerwartetes Prompt-Ende in 03_eval.py"
ev.SUFFIX = ev.SUFFIX + "\n</think>\n\n"

if __name__ == "__main__":
    ev.main()
    aus = sys.argv[sys.argv.index("--aus") + 1]
    p = os.path.join(aus, "zusammenfassung.json")
    if os.path.exists(p):
        z = json.load(open(p, encoding="utf-8"))
        z["ohne_denken"] = True
        z["prompt_ende"] = "<think>\\n\\n</think>\\n\\n"
        json.dump(z, open(p, "w"), indent=1)
