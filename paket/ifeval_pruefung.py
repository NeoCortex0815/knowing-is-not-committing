"""Hülle um die offiziellen IFEval-Prüfregeln (instruction_following_eval/, unverändert von google-research).

Einzige Anpassung zur Laufzeit: nltk >= 3.9 lädt keine Pickle-Dateien mehr. Die Satztrennung nutzt deshalb das sichere
Nachfolgeformat `punkt_tab` (gleiche Punkt-Parameter, englisch) statt `tokenizers/punkt/english.pickle`.

bewerte(prompt_row, text, denken=True) -> (alle_erfuellt, n_ok, n_gesamt)
  Wie im MIT-Code (exp8_math/code/evaluate.py, grade_other): Antwort = Text nach dem letzten </think>; mit Denkmodus
  und ohne </think> ist die Antwort leer -> nicht erfüllt. „strict prompt-level“: alle Anweisungen müssen stimmen.
"""
import os
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)

import nltk  # noqa: E402

_NLTK = os.path.join(os.path.dirname(sys.executable), "..", "nltk_data")
os.makedirs(_NLTK, exist_ok=True)
if _NLTK not in nltk.data.path:
    nltk.data.path.insert(0, _NLTK)
try:
    nltk.data.find("tokenizers/punkt_tab/english/")
except LookupError:
    nltk.download("punkt_tab", download_dir=_NLTK, quiet=True)

from instruction_following_eval import instructions_registry as IR  # noqa: E402
from instruction_following_eval import instructions_util as IU  # noqa: E402

_SATZ = nltk.tokenize.PunktTokenizer("english")
IU._get_sentence_tokenizer = lambda: _SATZ  # statt nltk.data.load(".../english.pickle")


def antwort_teil(text, denken=True):
    if "</think>" in text:
        return text.split("</think>")[-1].strip()
    return "" if denken else text.strip()


def bewerte(r, text, denken=True):
    resp = antwort_teil(text, denken)
    ok = []
    for iid, kw in zip(r["instruction_id_list"], r["kwargs"]):
        ins = IR.INSTRUCTION_DICT[iid](iid)
        ins.build_description(**{k: v for k, v in (kw or {}).items() if v is not None})
        args = ins.get_instruction_args()
        if args and "prompt" in args:
            ins.build_description(prompt=r["prompt"])
        ok.append(bool(resp) and bool(ins.check_following(resp)))
    return all(ok), sum(ok), len(ok)
