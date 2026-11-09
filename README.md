# Knowing Is Not Committing: code and data for the report

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.24058693.svg)](https://doi.org/10.5281/zenodo.24058693)

Independent replication and extension of MIT CSAIL's *Sparks of Weight-Space Programming* on **Qwen3.5-0.8B**:
- rebuilding the loop-reversal edit;
- adding conditioned closing pushes;
- writing a truth-gated reflex into 16 MLP neurons;
- a series of pre-registered tests on how the model *finds*, *recognises* and *commits to* answers.

- **Report, version 0.3:** [`report/Knowing_Is_Not_Committing_v0.3.md`](report/Knowing_Is_Not_Committing_v0.3.md) or as
  [PDF](report/Knowing_Is_Not_Committing_v0.3.pdf). Not peer-reviewed. Version 0.3 concludes the report; further follow-up tests
  on the question in its title remain reserved.
- **German translation:** [`report/Wissen_ist_nicht_Festlegen_v0.3.md`](report/Wissen_ist_nicht_Festlegen_v0.3.md) or as
  [PDF](report/Wissen_ist_nicht_Festlegen_v0.3.pdf). The English version is authoritative.
- **New in version 0.3:**
  - the result of N30, the test pre-registered publicly in v0.2 (Section 3.11);
  - N31, a check of the title question on internal signals (Section 3.12);
  - the consequences of both, listed at the top of the report.
- **Earlier version:** the interim report v0.2 stays in `report/` (`INTERIM_REPORT_v0.2.md`, `INTERIM_REPORT_v0.2_de.md` and both
  PDFs).
- **Author:** Dave Uhlemann (NeoCortex), independent researcher. AI assistance is disclosed in Section 8 of the report.
- **Questions and corrections:** please open an [issue](https://github.com/NeoCortex0815/knowing-is-not-committing/issues).
- **License:** Apache License 2.0 (`LICENSE`, `NOTICE`).
- **Archive and citation:** Zenodo, DOI [10.5281/zenodo.24058693](https://doi.org/10.5281/zenodo.24058693) for all versions;
  [10.5281/zenodo.24082318](https://doi.org/10.5281/zenodo.24082318) for v0.3 and
  [10.5281/zenodo.24058694](https://doi.org/10.5281/zenodo.24058694) for v0.2.

## What is in this folder

| folder | contents |
|---|---|
| `report/` | the report (version 0.3, and the interim report v0.2) in English and a German translation, each as Markdown and PDF |
| `eval/` | evaluation client for a local `llama-server` (MIT's "think35" protocol, vLLM-style sampling), answer-mode and presence-penalty variants |
| `paket/` | every edit builder and every test or analysis script, numbered in the order they were written; each docstring names its question and its pre-registered reading |
| `prereg/` | the dated pre-registration and analysis log (German) up to 8 Nov 2026, 19:42, and an excerpt of the later entries on N30, N31 and version 0.3 (`ANNAHMEN_excerpt_v0.3_de.md`; passages on later work are cut and marked "[…]"). Machine names, paths and details of the author's private systems are redacted |
| `results/runs/` | one CSV per evaluation run: problem id, gold answer, extracted answer, correct, end reason, tokens, thinking closed |
| `results/verdicts/` | the JSON outputs of the verdict and analysis scripts |
| `data/` | id lists of the MATH training problems we used (Set B, 40 new problems, practice set, the 150 problems of N30). The problems themselves are not redistributed |

Not included:
- model weights (rebuild them with the code);
- the datasets (MATH, MATH-500, IFEval; please obtain them from their sources);
- the IFEval instruction checks (google-research `instruction_following_eval`, see `NOTICE`);
- the full transcripts of our runs (large; can be provided later);
- the per-statement data of the trigger audit behind Section 3.12 (large; can be provided later).

Code comments and docstrings are in German. They are the working notes of the project, including the questions that led to each
test.

## How the mechanics can be traced

**Without running anything**
- Every mechanism is written out in the report: the rank-1 loop reversal, the conditioned closing gate, and the 16-neuron reflex
  as "effector × (condition ∧ context)" with its calibration rules (Section 3.8).
- The builders in `paket/` implement exactly these formulas: `wsp_lib.py`, `05_patch.py`, `50_ergo_gatter.py`,
  `66_wt_fix_bauen.py`, `84_mit_wt_bauen.py`.
- Every decisive test has a reading fixed in advance in `prereg/`, with date and time, before the run existed. The results of each
  run are in `results/runs/`.

**With the original layout.** The scripts expect this layout:

```
paket/   eval/   daten/   ergebnisse/   modelle/   llama/
```

- `daten/` holds the problem sets as JSONL with `problem` and `answer` (and `unique_id` / `id`, `level`).
- `modelle/` holds the Hugging Face model folders (base model and the edited models you build).
- `ergebnisse/` is where the evaluation runs write their results.
- The analysis scripts read the full transcripts from `ergebnisse/`. To re-run them, re-create the runs with `eval/` first. A
  full 140-problem run takes a few hours on one consumer GPU.

**Requirements**
- Python 3.12 with `numpy`, `torch`, `transformers`, `safetensors`, `requests` and `math-verify`. math-verify is required: without
  it, the code silently falls back to comparing normalised text and finds fewer agreements between answers.
- A llama.cpp build with `llama-server`.
- Base model `Qwen/Qwen3.5-0.8B` at revision `2fc06364715b967f1860aea9cf38778875588b17`.

**Steps**
1. **Build an edit:**
   - `paket/04_richtung.py` (or the layer-wise `04s_…`) finds the loop direction;
   - `05_patch.py` applies the rank-1 patch;
   - `50_ergo_gatter.py` builds the conditioned closing gate (ERGORE);
   - `66_wt_fix_bauen.py` builds the truth-gated reflex WT-A, using the frozen truth probe from `42_wahrheitsmelder.py`;
   - `84_mit_wt_bauen.py` builds MIT + WT.
2. **Convert to GGUF** with llama.cpp's converter (q8_0 in the report) and start `llama-server`.
3. **Evaluate:**
   - thinking mode: `eval/03_eval.py --vllm-stil --temperatur 0.6 --max-tokens 32768 --seed 0 …`;
   - answer mode: `eval/03b_eval_ohne_denken.py`;
   - presence-penalty check: `eval/03c_eval_presence.py`.
4. **Run the analysis script** for the result you want to check. The table below maps report sections to scripts.

**Sampling matters.** The same edit scores 25 % or 55 % on the same 40 problems depending on llama.cpp sampling settings
(Section 3.1). Use `--vllm-stil`: `repeat_last_n` covers the whole answer, and the sampler order is penalties → temperature →
top-k → top-p → min-p.

## Report sections and scripts (`paket/` unless noted)

| report section | main scripts |
|---|---|
| 3.1 Sampling decides half of the effect | `eval/03_eval.py` (`--vllm-stil`), `11_nachbewerten.py`, `13_mit_abgleich.py` |
| 3.2 Our own loop direction | `04_richtung.py`, `04s_richtung_schichtweise.py`, `05_patch.py`, `wsp_lib.py`, `21_logit_lens.py` |
| 3.3 ERGORE | `50_ergo_gatter.py`, `46_urteil160.py`, `73_urteil300.py`, `79_ergore_verluste.py` |
| 3.4 Models know more than they act on | `42_wahrheitsmelder.py` (truth probe), `44_melder_urteil.py`, `60_antwort_zwang.py`, `63_wahrheit_behauptung.py` |
| 3.5 Blunt pressure has a price | `14_ifeval.py` with `ifeval_pruefung.py` |
| 3.6 WT, the truth-gated reflex | `66_wt_fix_bauen.py`, `62_v22_urteil.py`, `70_wta_urteil.py`, `64_`–`69_…`, `75_pruefstellen.py` |
| 3.7 Negative results | `72_denk_weiche.py`, `51_schritt2_urteil.py` |
| 3.8 A recipe for programmed reflexes | `50_ergo_gatter.py`, `66_wt_fix_bauen.py`, `78_wt_bremse.py`, `84_mit_wt_bauen.py`, `56_`–`59_…` |
| 3.9 Fresh problems 161–300 | `73_urteil300.py`, `81_format_check.py`, `82_zucken.py`, `83_ausschluss.py`, `85_seeds.py`, `88_flur.py`, `93_wirktiefe.py` |
| 3.10 Answer mode ("front room") | `89_int_kaskade.py`, `91_`/`92_morgengrauen…`, `94_int_frisch.py`, `95_`/`97_…` (state doors), `96_durchstreichen.py`, `98_`/`99_schilder…`, `100_schild_reflex.py`, `101_replay.py`, `102_mit_int.py`, `103_vorderzimmer_sonde.py`, `104_zweifach_intuition.py`, `105_schild_replay.py`, `107_halbtest.py`, `108_drei_intuitionen.py` |
| 3.11 N30: a council with our own back room (v0.3) | `109_nacht150.py` (verdicts), `114_n30_leiter.py` (breakdown by agreement) |
| 3.12 N31: does committing track knowing? (v0.3) | `111_kopplung.py`, on the trigger-audit data of `82_zucken.py` |

## Problem sets

- MATH-500 problems 1–160: development and test set.
- MATH-500 problems 161–300: confirmation set.
- MATH-500 problems 301–370: second, late confirmation.
- MATH-500 problems 371–500: untouched.
- MATH training problems: practice and development sets, and the 150 never-used problems of N30 (ids in `data/`).
- IFEval: 120 prompts, strict prompt-level scoring.

## License

Apache License 2.0 for our code; see `LICENSE` and `NOTICE`. No model weights are distributed. MIT's published logs, the IFEval
checks and the datasets are only cited and linked; they stay under their own licenses.
