"""03_eval.py mit anderer presence_penalty (08.11.; WRENs Störfaktor-Test: Ist der INT-Vorteil ein Strafen-Artefakt?).
Optional ohne Denken (offizielle Nicht-Denk-Vorlage wie 03b). Ändert 03_eval.py NICHT.
  python eval/03c_eval_presence.py --presence 0.0 [--ohne-denken] <übrige Argumente wie 03_eval.py>
"""
import importlib.util
import json
import os
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
_s = importlib.util.spec_from_file_location("ev", os.path.join(HIER, "03_eval.py"))
ev = importlib.util.module_from_spec(_s)
_s.loader.exec_module(ev)

args = sys.argv[1:]
presence = 0.0
if "--presence" in args:
    k = args.index("--presence")
    presence = float(args[k + 1])
    del args[k:k + 2]
ohne = "--ohne-denken" in args
if ohne:
    args.remove("--ohne-denken")
    assert ev.SUFFIX.endswith("<think>\n"), "unerwartetes Prompt-Ende in 03_eval.py"
    ev.SUFFIX = ev.SUFFIX + "\n</think>\n\n"
ev.THINK35["presence_penalty"] = presence
sys.argv = [sys.argv[0]] + args

if __name__ == "__main__":
    ev.main()
    aus = args[args.index("--aus") + 1]
    p = os.path.join(aus, "zusammenfassung.json")
    if os.path.exists(p):
        z = json.load(open(p, encoding="utf-8"))
        z["ohne_denken"] = ohne
        z["presence_test"] = presence
        json.dump(z, open(p, "w"), indent=1)
