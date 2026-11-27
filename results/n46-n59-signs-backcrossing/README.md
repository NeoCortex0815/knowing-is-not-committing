# Per-item rows: signposts, the door and back-crossing (Qwen3.5-0.8B)

Report v0.6, Sections 3.15–3.17: tests A1, A2, N33b and N57 (Section 3.15), N46, N54, N34, N52 and N35 (Section 3.16), N49, N59,
N58, N56 and N55 (Section 3.17). Section 3.18 (N47, N47b, N36) consists of offline development checks on replayed states; it has
no per-item rows here. Every table below is computed by the build script from the rows in this folder (or, for the probe
measures, copied from the analysis outputs into `summaries.json`).

Naming as in the report. *Unedited* is the post-trained Qwen3.5-0.8B. *Pre-trained base* is Qwen3.5-0.8B-Base, with the same chat
template and thinking prompt. *MIT's edit* is the edit of MIT CSAIL ("Sparks of Weight-Space Programming"). WT-A is our own edit
(Section 3.6); *our own loop direction* (IFEval only) is the model of Section 3.5. SGNE-CC is a weight edit by **Igor M. Zhuk**
(`Nondual-Observer/Qwen3.5-0.8B-SGNE-CC`, Apache-2.0); S-GDN and S-MLP are its GatedDeltaNet part and its MLP part alone
(`../n41-ablations`). The method of SGNE-CC is his; these rows are our measurements.

## How the back-crossed arms were built (no training)

Every arm is assembled only by copying or mixing tensors of the two released models, Qwen3.5-0.8B (post-trained) and
Qwen3.5-0.8B-Base (pre-trained). Everything else (embedding, norms, output head, chat template) stays. For every arm we checked
tensor by tensor that exactly the chosen tensors differ, and that all other tensors of the q8_0 GGUF are byte-equal to the source
model. The arms were chosen by type or position before any run, not by results.

- **N49**, the unedited model with tensors of the pre-trained base:
  - `R-GDN`: all 18 GatedDeltaNet layers (162 tensors, 138 of them differ between the two models);
  - `R-GDN-out`: only `out_proj` of these 18 layers (18 tensors);
  - `R-MLP`: all 24 MLP blocks (72 tensors);
  - `R-ATT`: the 6 attention layers (36 tensors).
- **N58**, split by depth: `R-MLP-early` = the base's MLP blocks in layers 0–11 (36 tensors); `R-MLP-late` = layers 12–23
  (36 tensors).
- **N56**, the reverse as a dial: the pre-trained base with MLP = base + λ·(unedited − base), λ ∈ {1, 0.75, 0.5, 0.25}, 72 tensors.
  λ = 1 is the base with the unedited model's MLP blocks (byte-exact, the mirror image of R-MLP); the others are computed in
  float32 and rounded to bf16.

## Problems and prompts

- **The 50:** the 50 fresh MATH training problems of `../n40-sgne-cc` and `../n41-ablations` (Section 3.13).
- **Set B:** 60 MATH problems, a development set in earlier versions; new runs for N57 (pre-trained base, unedited) and N59 (R-MLP).
- **150 and 100:** the 150 problems of N30/N44 and the 100 of N45 (Sections 3.11 and 3.14); existing runs, used here only for the
  text measures of A1 (`signs_150_100.csv`).
- **IFEval:** 120 prompts, strict prompt level, official rules.

## Setup

- llama.cpp server, q8_0 GGUF, vLLM-style sampling: temperature 0.6, top_p 0.95, top_k 20, presence penalty 1.5
  (penalties → temperature → top_k → top_p), at most 32,768 new tokens. Tokenizer and chat template of `Qwen/Qwen3.5-0.8B`,
  for every arm, thinking on. Seed 0 unless a row says otherwise.
- Early stop of clear loops: from 4,096 tokens on, a run stops when the duplicate-8-gram share over the last 400 words exceeds 0.9.
- **Machines.** N49 and N58 ran on the second machine (12 slots); all other runs on the first machine (6 slots). In an earlier check
  of this project with the unedited model, machine and slot count acted like a change of seed. N59 repeats R-MLP on the first
  machine, next to the pre-trained base and the unedited model of N57.
- **Grading.** Math: math-verify in the main thread, against the `gold` answer. The second machine graded with a bug; every run from
  it was re-graded on the first machine before any count, and all counts here use the re-graded copy. IFEval: strict prompt level,
  official rules; the answer is the text after the last `</think>`, so a run that never closes its thinking fails. The IFEval
  answers of N49 and N58 were generated on the second machine and scored on the first.

## Measures (text only, counted in the thinking block, the same tools for every arm)

- *Signpost:* the model's own phrase "(so / thus / therefore / hence) (the) (final) answer is / should be / would be" or
  "final answer" (case-insensitive).
- *Door:* the first `</think>`.
- *Signpost before the door:* the last signpost ends at most 800 characters (about 200 tokens) before the door.
- *Reopened:* another `</think>` follows the first one.
- *Value of a signpost:* the first candidate value that ends within 200 characters after the signpost, graded against `gold` with
  math-verify (time limit 120 s per check; a value that cannot be checked counts as wrong). No candidate: "no value".
- *Door after a signpost* (per signpost, A2): the door begins at most 800 characters after the end of the signpost.
- *Door at* (per run, N33b): the kind of the last signpost that the door follows within 800 characters (correct value, wrong value,
  no value), or "no signpost".
- *Closes at a correct signpost* (per run): of the runs with at least one signpost that carries a correct value, those whose door
  is at such a signpost.

Percentages below are rounded half up from the exact counts.

## Signposts before the door on the 50 problems (A1, A2, N33b; Section 3.15)

[descriptive; found after the runs existed, no reading fixed in advance]

| arm | correct (of 50) | doors | signpost before the door | reopened | correct-value signposts: door follows | wrong-value signposts: door follows | runs with a correct-value signpost: close there | runs with signposts, none with a correct value: close anyway | correct: doors with / without a signpost |
|---|---|---|---|---|---|---|---|---|---|
| pre-trained base | 27 | 41 | 33 of 41 (80 %) | 0 of 41 (0 %) | 39 of 50 (78 %) | 24 of 298 (8 %) | 19 of 21 | 15 of 19 | 22 of 33 / 5 of 8 |
| unedited | 5 | 6 | 2 of 6 (33 %) | 0 of 6 (0 %) | 3 of 80 (4 %) | 0 of 316 (0 %) | 1 of 11 | 1 of 9 | 1 of 2 / 4 of 4 |
| MIT's edit | 20 | 34 | 12 of 34 (35 %) | 7 of 34 (21 %) | 7 of 69 (10 %) | 4 of 148 (3 %) | 4 of 15 | 11 of 15 | 9 of 12 / 11 of 22 |
| WT-A | 19 | 38 | 10 of 38 (26 %) | 29 of 38 (76 %) | 5 of 15 (33 %) | 5 of 219 (2 %) | 4 of 6 | 12 of 14 | 8 of 10 / 11 of 28 |
| SGNE-CC | 22 | 50 | 15 of 50 (30 %) | 18 of 50 (36 %) | 4 of 5 (80 %) | 4 of 12 (33 %) | 3 of 5 | 16 of 16 | 11 of 15 / 11 of 35 |
| SGNE-CC (seed 1) | 20 | 50 | 10 of 50 (20 %) | 21 of 50 (42 %) | 2 of 2 (100 %) | 4 of 16 (25 %) | 1 of 1 | 16 of 16 | 6 of 10 / 14 of 40 |
| S-GDN | 26 | 35 | 24 of 35 (69 %) | 0 of 35 (0 %) | 7 of 60 (12 %) | 11 of 319 (3 %) | 6 of 20 | 15 of 26 | 18 of 24 / 8 of 11 |
| S-GDN (seed 1) | 29 | 37 | 28 of 37 (76 %) | 2 of 37 (5 %) | 9 of 82 (11 %) | 15 of 310 (5 %) | 8 of 21 | 17 of 25 | 22 of 28 / 7 of 9 |
| S-MLP | 13 | 49 | 8 of 49 (16 %) | 17 of 49 (35 %) | 0 of 0 | 3 of 19 (16 %) | 0 of 0 | 13 of 13 | 5 of 8 / 8 of 41 |

The same text measures on the 150 and 100 problems (A1 only) [descriptive]:

| set | arm | correct | doors | signpost before the door | reopened | correct: doors with / without a signpost |
|---|---|---|---|---|---|---|
| 150 | SGNE-CC | 62 of 150 | 149 | 27 of 149 (18 %) | 55 of 149 (37 %) | 22 of 27 / 40 of 122 |
| 150 | MIT's edit | 67 of 150 | 112 | 51 of 112 (46 %) | 9 of 112 (8 %) | 33 of 51 / 34 of 61 |
| 150 | WT-A | 59 of 150 | 100 | 10 of 100 (10 %) | 78 of 100 (78 %) | 7 of 10 / 52 of 90 |
| 100 | SGNE-CC | 52 of 100 | 100 | 24 of 100 (24 %) | 36 of 100 (36 %) | 17 of 24 / 35 of 76 |
| 100 | MIT's edit | 49 of 100 | 72 | 32 of 72 (44 %) | 6 of 72 (8 %) | 23 of 32 / 26 of 40 |

## Back-crossing and the comparison arms (N49, N58, N56, N57, N59; Section 3.17)

| arm | machine | correct | signpost before the door | reopened | closes at a correct signpost | IFEval (of 120) | tokens per correct answer |
|---|---|---|---|---|---|---|---|
| *the 50 problems* | | | | | | | |
| unedited | first | 5 | 2 of 6 (33.3 %) | 0 of 6 (0.0 %) | 1 of 11 (9 %) | 18 | 144,909 |
| pre-trained base | first | 27 | 33 of 41 (80.5 %) | 0 of 41 (0.0 %) | 19 of 21 (90 %) | 44 | 20,265 |
| MIT's edit | first | 20 | 12 of 34 (35.3 %) | 7 of 34 (20.6 %) | 4 of 15 (27 %) | 87 | 57,246 |
| R-GDN | second | 16 | 14 of 16 (87.5 %) | 0 of 16 (0.0 %) | 3 of 9 (33 %) | 56 | 36,017 |
| R-GDN-out | second | 11 | 5 of 11 (45.5 %) | 0 of 11 (0.0 %) | 4 of 12 (33 %) | 58 | 70,661 |
| R-ATT | second | 13 | 9 of 13 (69.2 %) | 0 of 13 (0.0 %) | 3 of 16 (19 %) | 54 | 58,034 |
| R-MLP | second | 23 | 27 of 27 (100.0 %) | 0 of 27 (0.0 %) | 21 of 24 (88 %) | 44 | 32,544 |
| R-MLP-early | second | 11 | 9 of 12 (75.0 %) | 0 of 12 (0.0 %) | 2 of 13 (15 %) | 34 | 78,033 |
| R-MLP-late | second | 13 | 11 of 13 (84.6 %) | 0 of 13 (0.0 %) | 3 of 18 (17 %) | 53 | 64,953 |
| base + unedited MLP λ = 1 | first | 20 | 21 of 25 (84.0 %) | 0 of 25 (0.0 %) | 5 of 15 (33 %) | 54 | 38,588 |
| base + unedited MLP λ = 0.75 | first | 25 | 26 of 26 (100.0 %) | 0 of 26 (0.0 %) | 16 of 21 (76 %) | 50 | 29,260 |
| base + unedited MLP λ = 0.5 | first | 25 | 29 of 34 (85.3 %) | 1 of 34 (2.9 %) | 12 of 21 (57 %) | 53 | 22,524 |
| base + unedited MLP λ = 0.25 | first | 27 | 31 of 38 (81.6 %) | 0 of 38 (0.0 %) | 17 of 23 (74 %) | 46 | 19,479 |
| *Set B (60 problems)* | | | | | | | |
| unedited | first | 9 | 4 of 8 (50.0 %) | 0 of 8 (0.0 %) | 2 of 15 (13 %) | – | 101,865 |
| pre-trained base | first | 36 | 40 of 50 (80.0 %) | 0 of 50 (0.0 %) | 21 of 27 (78 %) | – | 12,654 |
| R-MLP | first | 35 | 38 of 39 (97.4 %) | 0 of 39 (0.0 %) | 26 of 36 (72 %) | – | 17,878 |

[descriptive, except the verdicts below]. Tokens per correct answer = all generated tokens of the arm / correct answers.
Set B, mean tokens per run (R-MLP / pre-trained base / unedited): 10,429 / 7,592 / 15,280; runs with loop stop or 32K cap: 21 / 11 / 52.

## Readings fixed in advance (recomputed from the rows) [pre-registered]

The readings were fixed in the dated log on 22 and 23 Nov 2026, before each run (N57: before any run; N54: before any N49 data were
read). *Closes at the signpost:* signpost before the door ≥ 60 % AND reopened ≤ 10 %. *Truth-led:* in addition, ≥ 60 % of the runs
with a correct-value signpost close there. IFEval ≥ 74 "kept" / "manners there", ≤ 50 "lost" / "manners missing", otherwise "open".
Full wording of every reading: report v0.6, Sections 3.15 and 3.17.

- **N57** (Set B): H57a (signpost before the door) "open"; H57c (closes at a correct signpost) "confirmed".
- **N49:**
  - R-MLP: closes at the signpost; truth: truth-led; IFEval 44 → "lost"
  - R-GDN: closes at the signpost; truth: not truth-led; IFEval 56 → "open"
  - R-ATT: closes at the signpost; truth: not truth-led; IFEval 54 → "open"
  - R-GDN-out: not reached; truth: –; IFEval 58 → "open"
- **N59** (R-MLP on Set B): H59a "confirmed"; H59b "confirmed".
- **N58:**
  - R-MLP-early: closes at the signpost; truth: not truth-led; IFEval 34 → "lost"
  - R-MLP-late: closes at the signpost; truth: not truth-led; IFEval 53 → "open"
  - H58: "the door needs both halves".
- **N56:**
  - λ = 1: "door lost" (5 of 15); IFEval 54 → "open"
  - λ = 0.75: "door stays" (16 of 21); IFEval 50 → "manners missing"
  - λ = 0.5: "door lost" (12 of 21); IFEval 53 → "open"
  - λ = 0.25: "door stays" (17 of 23); IFEval 46 → "manners missing"
  - H56: "manners not in the MLP alone".

## IFEval per arm (N49, N58, N56, N55; Section 3.17)

| arm | machine | correct, strict prompt level (of 120) | single instructions met | clean end | 32K cap | loop stop | thinking closed | mean tokens |
|---|---|---|---|---|---|---|---|---|
| unedited | first | 18 (15.0 %) | 25 of 195 (12.8 %) | 23 | 32 | 65 | 25 | 11,948 |
| pre-trained base | first | 44 (36.7 %) | 92 of 195 (47.2 %) | 115 | 3 | 2 | 116 | 1,645 |
| MIT's edit | first | 87 (72.5 %) | 151 of 195 (77.4 %) | 117 | 1 | 2 | 119 | 3,753 |
| WT-A | first | 70 (58.3 %) | 129 of 195 (66.2 %) | 112 | 3 | 5 | 114 | 5,279 |
| our own loop direction | first | 74 (61.7 %) | 136 of 195 (69.7 %) | 112 | 2 | 6 | 117 | 5,348 |
| R-GDN | second | 56 (46.7 %) | 97 of 195 (49.7 %) | 89 | 14 | 17 | 90 | 6,167 |
| R-GDN-out | second | 58 (48.3 %) | 96 of 195 (49.2 %) | 79 | 14 | 27 | 81 | 7,087 |
| R-ATT | second | 54 (45.0 %) | 78 of 195 (40.0 %) | 60 | 21 | 39 | 66 | 9,011 |
| R-MLP | second | 44 (36.7 %) | 91 of 195 (46.7 %) | 100 | 16 | 4 | 102 | 5,955 |
| R-MLP-early | second | 34 (28.3 %) | 41 of 195 (21.0 %) | 43 | 28 | 49 | 43 | 10,465 |
| R-MLP-late | second | 53 (44.2 %) | 87 of 195 (44.6 %) | 82 | 23 | 15 | 83 | 8,037 |
| base + unedited MLP λ = 1 | first | 54 (45.0 %) | 95 of 195 (48.7 %) | 99 | 6 | 15 | 99 | 3,961 |
| base + unedited MLP λ = 0.75 | first | 50 (41.7 %) | 105 of 195 (53.8 %) | 118 | 1 | 1 | 118 | 1,250 |
| base + unedited MLP λ = 0.5 | first | 53 (44.2 %) | 109 of 195 (55.9 %) | 117 | 1 | 2 | 119 | 1,163 |
| base + unedited MLP λ = 0.25 | first | 46 (38.3 %) | 103 of 195 (52.8 %) | 116 | 0 | 4 | 118 | 936 |

[descriptive, except the verdicts above]. "Machine" is where the answers were generated; all were scored on the first machine.

## Probe and weight measures (`summaries.json`; Section 3.16)

These come from replaying the existing runs with teacher forcing (states and the model's own probabilities), or from the weights
(N35). They cannot be recomputed from the CSV rows; the values are those written by the analysis scripts.

**N46: does the closing readiness follow truth?** K = the frozen truth probe, F = the model's own probability of `</think>`, both the
highest value in the window [t, t+12] after a value statement; AUC for correct against wrong values; 95 % interval by cluster
bootstrap over runs (10,000 draws). Readings: AUC_K ≥ 0.70 precondition; AUC_F ≥ 0.70 "couples", < 0.60 "decoupled", otherwise "open".

| arm | AUC_K | AUC_F [95 %] | AUC_F at signposts (statements) | value statements | verdict |
|---|---|---|---|---|---|
| pre-trained base [pre-registered (H46a)] | 0.83 | 0.78 [0.68; 0.92] | 0.92 (593) | 13,375 (225 correct) | couples committing to truth |
| S-GDN [pre-registered (H46b)] | 0.86 | 0.76 [0.69; 0.83] | 0.67 (630) | 18,547 (722 correct) | couples committing to truth |
| SGNE-CC [pre-registered (H46c)] | 0.84 | 0.78 [0.69; 0.85] | 0.94 (28) | 2,451 (108 correct) | couples committing to truth |
| unedited [descriptive] | 0.73 | 0.62 [0.53; 0.72] | 0.41 (626) | 13,875 (1,233 correct) | open |
| MIT's edit [descriptive] | 0.80 | 0.68 [0.61; 0.76] | 0.67 (385) | 23,012 (1,180 correct) | open |
| WT-A, trigger silenced [descriptive] | 0.54 | 0.61 [0.47; 0.70] | 0.25 (294) | 15,093 (418 correct) | probe not transferable (F descriptive only) |

**Inner sign knowledge.** Logistic probe on the residual stream at value ends (5 folds by problem; signpost value ends against other
value ends, 1 : 6; seed 0). N54: AUC ≥ 0.80 "back", ≤ 0.70 "not back"; H57b: "confirmed" at base ≥ 0.80 and unedited ≤ 0.70,
"refuted" at a gap ≤ 0.05, otherwise "open".

| problems | model | AUC, layer 15 | layers 13 / 19 | signpost value ends | test | verdict |
|---|---|---|---|---|---|---|
| the 50 | R-GDN | 0.973 | 0.963 / 0.960 | 63 | N54 | back |
| the 50 | R-GDN-out | 0.835 | 0.868 / 0.815 | 1066 | N54 | back |
| the 50 | R-MLP | 0.909 | 0.907 / 0.881 | 473 | N54 | back |
| the 50 | R-ATT | 0.642 | 0.589 / 0.629 | 690 | N54 | not back |
| Set B | pre-trained base | 0.924 | 0.913 / 0.910 | 417 | N57 H57b | open |
| Set B | unedited | 0.839 | 0.801 / 0.845 | 294 | N57 H57b | open |
| the 50 | R-MLP-early | 0.626 | 0.675 / 0.913 | 710 | N58 | – |
| the 50 | R-MLP-late | 0.721 | 0.841 / 0.703 | 2111 | N58 | – |
| Set B | R-MLP | 0.855 | 0.861 / 0.854 | 872 | N59 | – |

Also in `summaries.json`: N34 (the door direction of the pre-trained base, build and test counts, test AUC, cosines, projections of
the other arms), N35 (writers of the door token, the signpost words and counter-words; correlation, overlap and writing strength,
base against unedited) and the N52 split "by itself" against "pushed".

**Not in this folder:** the per-statement probe values and states (large), the quick test of inner sign knowledge on the 50
problems, the N46 counter-check, the N52 traces (Figure 1 of the report), IFEval by instruction type, and Section 3.18. These
numbers are in the report only.

## Files and columns

- `per_item_50.csv`: one row per arm × problem on the 50 problems (950 rows, 19 arm-seed pairs).
- `per_item_setB.csv`: the same columns on Set B (180 rows: unedited, pre-trained base, R-MLP).
- `per_item_ifeval.csv`: one row per arm × prompt (1800 rows, 15 arms).
- `signs_150_100.csv`: A1 columns on the 150 and 100 problems (650 rows; SGNE-CC, MIT's edit, WT-A on 150; SGNE-CC, MIT's edit
  on 100).
- `summaries.json`: N46, N34, N35, N52 and inner sign knowledge (N54, N57 H57b, N58, N59).

| column | meaning |
|---|---|
| `arm`, `seed`, `machine` | arm as above; sampling seed; `first` (6 slots) or `second` (12 slots) |
| `set` | `150` or `100` (`signs_150_100.csv` only) |
| `id`, `gold`, `pred` | problem id, reference answer, content of the last `\boxed{}` (empty if none) |
| `correct` | 1 if `pred` matches `gold` under math-verify (re-graded copy) |
| `end`, `tokens` | `eos`, `limit` (32K cap) or `loop_abbruch` (loop stop); generated tokens |
| `door` | 1 if the thinking block was closed (a first `</think>` exists) |
| `signposts` | number of signposts in the thinking block |
| `signpost_before_door`, `reopened` | 1/0 as defined above; empty if there is no door |
| `signposts_correct_value`, `signposts_wrong_value`, `signposts_no_value` | signposts in the run by the kind of their value |
| `…_door` | of those, the signposts after which the door follows within 800 characters |
| `door_at` | `correct_value`, `wrong_value`, `no_value` or `no_signpost`; empty if there is no door |
| `has_correct_value_signpost` | 1 if at least one signpost of the run carries a correct value |
| `instructions` | IFEval instruction ids of the prompt, separated by `;` |
| `correct` (IFEval) | 1 if all instructions of the prompt are met (strict prompt level) |
| `instructions_met`, `instructions_total` | single instructions met / given |
| `think_closed` (IFEval) | 1 if the run closed its thinking |

How to read the per-run columns: *closes at a correct signpost* = `has_correct_value_signpost` = 1 and `door_at` = `correct_value`;
*close anyway* = `signposts` > 0, `has_correct_value_signpost` = 0 and `door` = 1.

## Caveats

- One seed, except S-GDN and SGNE-CC on the 50 problems (seed 1 as extra rows). 50 + 60 problems; the per-run counts rest on few
  runs per arm.
- A1, A2 and N33b were found after the runs existed [descriptive]. Fixed in advance were N46 (three arms), N54, N57, N49, N58, N56
  and N59 [pre-registered].
- The selection per signpost (A2) can partly come from the fact that wrong values are often intermediate steps.
- Our signpost pattern is narrow; the model has closing phrases it does not cover (Section 3.18).
- IFEval measures form, not truth or safety. Safety behaviour was not measured; the pre-trained base has no safety post-training,
  and R-MLP's MLP blocks come from it.
- N56 was extended by λ = 1 before the build (logged as a deviation).
