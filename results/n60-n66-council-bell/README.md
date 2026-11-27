# Per-item rows: R-MLP as back room, a bell at a deadline, and honest abstention (Qwen3.5-0.8B)

Report v0.6, Sections 3.19–3.21: tests N60 and N60b (3.19), N61, N50, N62 and N65 (3.20), N63, N64 and N66 (3.21). One row per problem
(per run for N60b). Every arm and council was rebuilt from the runs with the unchanged analysis code. The build then recounted the report's numbers from these files and compared them with the report: all of them matched.

## Models and arms

- **R-MLP:** the unedited (post-trained) Qwen3.5-0.8B with all 72 MLP tensors of the pre-trained base, built without any training
  (Section 3.17). Thinking on, seed 0 (seed 1 in N65).
- **MIT's edit:** addition of one direction to 64 columns of `down_proj` in layers 15 and 19. Thinking on.
- **SGNE-CC:** a weight edit by **Igor M. Zhuk** (on Hugging Face: Nondual-Observer; `Nondual-Observer/Qwen3.5-0.8B-SGNE-CC`, Apache-2.0).
  The method is his; here it is the comparison back room of Section 3.14 on the N44 and N45 sets. Thinking on.
- **Intuitions:** answer-mode runs (thinking off), seeds 0, 1 and 2. On the N44 set those of our own-direction model, on all other sets
  those of the unedited model. The intuitions are the same in every council of a set.
- **Back-room arms of R-MLP** (Sections 3.20, 3.21), all built from the same R-MLP runs:
  - `r0`: R-MLP as it ran, no bell.
  - `r61` (N61): bell without truth. `r50` (N50): bell with truth (probe). `rn` (N64): bell at the model's own closing tendency.
  - `rsf` / `rsk` (N63): self-decision at the deadline, free / boxed. `rk` (N66): own closing tendency decides between the boxed
    self-answer and "I don't know".

## Sets

- **N44 set:** the 150 problems of N30 (Section 3.11). Known to all arms except R-MLP.
- **N45 set:** the 100 fresh MATH training problems of N45 (Section 3.14).
- **F2, F3, F4:** 100 fresh MATH training problems each, drawn before any model saw them, with every earlier problem excluded. Level mix as
  in N45 (levels 1–5: 8 / 18 / 21 / 26 / 27). F4 was untouched until N66. N63 and N64 reuse the runs on F2 and F3 (new arms, known
  problems).

## Setup

- Machines: every thinking run (R-MLP, MIT's edit, SGNE-CC) and every answer after a bell ran on the first machine (6 slots for the runs,
  3 slots for the answers after a bell). The intuitions ran on the second machine (12 slots) for F2, F3 and F4, on the second machine for
  the N44 set, and on the first machine for the N45 set.
- Every run: llama.cpp server, q8_0 GGUF, vLLM-style sampling:
  temperature 0.6, top_p 0.95, top_k 20, min_p 0.0, presence penalty 1.5 over the whole output, sampler order penalties → temperature → top_k → top_p → min_p, at most 32,768 new tokens.
  Early stop of clear loops: from 4,096 tokens on, a run stops when the duplicate-8-gram share over the last 400 words exceeds 0.9. Tokenizer and chat template of `Qwen/Qwen3.5-0.8B`. Answer mode:
  the prompt ends with the official non-thinking pattern `<think>\n\n</think>\n\n`. The script checked that all 27 runs used here
  have these settings; only the seed differs.
- Grading: math-verify against `gold`. Every run was re-graded on the first machine before any count (this corrects a grading bug of
  the second machine); every `_correct` value of a run comes from that re-grading. Answers after a bell or at the deadline were graded
  on the first machine right after they were written (on F4 in a separate process with a 120 s limit; not checkable counts as wrong).
- Agreement of two intuitions: math-verify in both directions, in a separate process with a 120 s limit; not checkable counts as not
  equal. In this rebuild that happened once (on F4), as in the original analysis.

## Councils (rules of Section 3.14)

- *lean*: seeds 0 and 1; if they agree, deliver seed 0's answer, otherwise the back room decides.
- *full*: three intuitions; a majority of two delivers, otherwise the back room decides.
- *staged*: seeds 0 and 1; if they agree, deliver; otherwise ask seed 2; if it agrees with seed 0 (or else with seed 1), deliver that
  answer; otherwise the back room decides. Same answers as *full*, fewer tokens. All councils in 3.20 and 3.21 are staged.
- Tokens per correct answer: all tokens the council spent (each intuition it asked, plus the back room where it was asked), divided by
  its correct answers. An abstention is not a correct answer, but its tokens count.
- Council names in the files: `bh0` (back room `r0`, always answers); `bh50` (back room `r50`; if it says "I don't know", the council gives
  seed 0's answer; N61 H3); `bhe` (back room `r50`; its "I don't know" becomes the council's abstention; N62); `bhn` (`rn`, abstaining;
  N64); `bhsk` (`rsk`, abstaining; N63); `bhk` (`rk`, abstaining; N66).

## The bell (Section 3.20)

- **Deadline:** 8,192 thinking tokens, fixed in advance. A run whose first `</think>` (the door) comes before token 8,192 stays as it
  is (`deadline_reached` = 0). Otherwise the bell rings.
- **Cut and answer prefix:** the run is cut after a value and closed with `\n</think>\n\nThe final answer is $\boxed{`; R-MLP fills
  in its answer (up to 256 tokens, same sampling, seed 0). The first `\boxed{…}` counts. (Addendum fixed before any fresh result: a free
  answer after the cut often re-solved the problem and changed its mind; the prefix avoids that.)
- **Where the cut is:** `r61` at the last sign with a value before the deadline (a sign is a phrase such as "so the answer is" or "final
  answer"; its value is the first value within 200 characters after it). `r50` at the last value statement before the deadline where the
  truth probe says "true". `rn` at the last value statement before the deadline where the own closing tendency F is above τ_F.
- **"I don't know":** if there is no such place, the back room says "I don't know" (`_idk` = 1, empty `_pred`).
- **Tokens of a bell arm:** thinking tokens up to the deadline (or up to the end of a run that stopped earlier in a loop), plus the
  answer tokens; for "I don't know" only the thinking tokens.
- **Truth probe** (`truth_probe_layer15.npz`): a linear probe on the hidden state after decoder layer 15 of R-MLP (0-based index,
  1,024 dimensions), read at the last token of a value statement: score = w · h + b; "true" if score > τ = -0.3366.
  Fitted on 41,798 value statements (1,635 correct) of 360 earlier R-MLP runs (the 50 problems, Set B,
  N44 set, N45 set). Layer chosen by held-out AUC among layers 9, 12, 15, 18, 21; layer 15: 0.862
  (at signs 0.909). τ follows the 2 % rule: the smallest threshold with at most 2 % of the wrong values strictly above
  it (803 of 40,163; 845 correct values lie above). [development]
- On the earlier runs the deadline kept almost all correct answers (71 / 48 instead of 73 / 49 on the N44 / N45 sets) at 35 % of the
  tokens. [development]

## Abstention and the honesty rule

- An abstaining council says "I don't know" when its back room does (`_abstain` = 1). An abstention is neither correct nor wrong.
- **Honesty rule** (HE, N62; again in N65, H63d, H64a, H66a), paired per problem against the council without bell (`bh0`):
  - *fewer wrong*: problems where `bh0` is wrong and the other council is not (correct or abstaining), against the reverse; one-sided
    exact McNemar p < 0.05 and more problems in the first case;
  - *fewer correct*: problems where `bh0` is correct and the other council is not, against the reverse; one-sided p < 0.05;
  - "confirmed" if fewer wrong and not fewer correct; "refuted" if not fewer wrong (difference ≤ 0) or fewer correct; else "open".
- **Equivalence rule** (H64b, H66b): "worse" if significantly more wrong or fewer correct answers; "better" if significantly fewer wrong
  or more correct and not worse; else "equivalent".
- Other thresholds as in Section 3.14: paired hits with a one-sided exact McNemar test, p < 0.05; tokens per correct answer ≤ 70 %
  "saves tokens", ≥ 130 % "costs tokens", else "similar". No correction for multiple readings.

## From within (Section 3.21)

- **`rsf` (N63, free):** a run without door before the deadline stops after the last line break before the deadline. The model reads,
  inside its thinking, “I have been thinking for a long time now, so I will stop here. If I am confident in my answer, I will state it. If I am not sure, I will honestly say "I don't know".”, then `</think>`. It writes freely (up to 1,024 tokens); its last `\boxed{}` is its answer, without
  one it counts as "I don't know". `rsf_kind`: `answer`, `idk` (wrote "I don't know" or similar) or `no_box` (no box within the limit).
- **`rsk` (N63, boxed):** same stop. The sentence is “I have been thinking for a long time now, so I will stop here. If I am confident in my answer, I will give it. If I am not sure, I will honestly write "I don't know" as my answer.”, then `</think>` and `The final answer is $\boxed{`; up to 64
  tokens. "I don't know" inside the box counts as "I don't know".
- Tokens of `rsf` / `rsk`: thinking tokens up to the stop plus the answer tokens (the added sentence is not counted).
- **`rn` (N64, own closing tendency):** at each value statement before the deadline, F = the model's own probability that the next token
  is `</think>`, maximum over the 13 positions from the value's last token to 12 tokens later. τ_F = 1.0675266821635887e-06 by the 2 % rule on
  the same 360 earlier runs (AUC 0.794 there; `closing_tendency_threshold.json`). Cut and prefix as for `r50`.
- **`rk` (N66):** a run with door before the deadline stays; otherwise, if F rose above τ_F at some value statement before the deadline,
  the boxed self-answer (`rsk`) counts; else "I don't know". On the earlier runs: 186 correct / 91 wrong / 83 "I don't know", against
  180 / 180 without bell. [development]

## Summary: Section 3.19 (N60, N60b)

Cells: correct · tokens per correct answer. [descriptive]

| | N44 set (150), intuitions of our own-direction model | N45 set (100), intuitions of the unedited model |
|---|---|---|
| MIT's edit alone | 67 · 49,089 | 49 · 44,715 |
| SGNE-CC alone | 62 · 14,882 | 52 · 11,736 |
| R-MLP alone | 73 · 28,351 | 49 · 27,554 |
| lean council, SGNE-CC / R-MLP | 70 / 78 | 59 / 54 |
| staged council, SGNE-CC / R-MLP | 78 / 83 | 61 / 59 |

[pre-registered] (only A : only B, one-sided p; tokens per correct answer)
- **H1** (lean council with R-MLP against MIT's edit alone): N44 set 78 vs 67, 21 : 10, p = 0.0354 → "beats MIT"; tokens 110 % → "similar"; N45 set 54 vs 49, 13 : 8, p = 0.1917 → "level"; tokens 104 % → "similar".
- **H2** (lean council, R-MLP against SGNE-CC as back room): N44 set 78 vs 70, 13 : 5, p = 0.0481 → "R-MLP carries more"; tokens 114 % → "similar"; N45 set 54 vs 59, 6 : 11, p = 0.9283 → "level"; tokens 148 % → "costs tokens".
- **H4** (staged council with R-MLP against MIT's edit alone): N44 set 83 vs 67, 24 : 8, p = 0.0035 → "beats MIT"; tokens 115 % → "similar"; N45 set 59 vs 49, 16 : 6, p = 0.0262 → "beats MIT"; tokens 103 % → "similar".
- **H3** (R-MLP alone leaves its thinking at a sign with the correct value, ≥ 60 % "confirmed"): N44 set 52 of 79 runs (65.8 %) → "confirmed"; N45 set 31 of 52 runs (59.6 %) → "open".
- [descriptive] Both sets together: staged council with R-MLP 142 against MIT's 116 (40 : 14); R-MLP against SGNE-CC as back room: lean 132 against 129, staged 142 against 139.

N60b [descriptive, post hoc]: R-MLP never closes in 59 of 150 and 40 of 100 runs; these take 81.5 % / 87.8 % of its tokens. 41 of 59 and 22 of 40 never contain the correct answer; in the others the first correct value comes after a median of 2,222 / 4,138 tokens, followed by 25,151 / 27,733 more. Oracle bell (stop every run without door at its first correct value): 90 / 65; bell at the first sign with a value: 78 / 50 (without bell 73 / 49). Runs that close are short: median length 1,238 / 1,194 generated tokens in total, the door itself at median token 977 / 812 (MIT's edit: length 19,180 / 18,917).

## Summary: Section 3.20 (N61, N50, N62, N65)

| | correct | wrong | "I don't know" / abstain | tokens per correct answer |
|---|---|---|---|---|
| F2, R-MLP without bell (`r0`) | 56 | 44 | 0 | 20,845 |
| F2, bell without truth (`r61`) | 58 | 22 | 20 | 6,918 |
| F2, bell with truth (`r50`) | 59 | 19 | 22 | 6,817 |
| F2, MIT's edit | 61 | 39 | 0 | 30,859 |
| F2, staged council without bell (`bh0`) | 67 | 33 | 0 | 38,632 |
| F2, staged council, truth bell, seed 0 on "I don't know" (`bh50`) | 70 | 30 | 0 | 29,909 |
| F2, staged council, truth bell, abstaining (`bhe`) | 69 | 16 | 15 | 30,343 |
| F3, R-MLP without bell (`r0`) | 45 | 55 | 0 | 28,243 |
| F3, bell with truth (`r50`) | 51 | 34 | 15 | 9,111 |
| F3, council without bell (`bh0`) | 54 | 46 | 0 | 51,218 |
| F3, council abstaining (`bhe`) | 56 | 32 | 12 | 40,052 |

N61 and N50 on F2 [pre-registered]:
- **H1** (bell without truth against no bell): 58 vs 56 (5 : 3) → "level"; tokens 33 % → "saves tokens".
- **H2** (bell with truth against no bell): 59 vs 56 (4 : 1) → "level"; tokens 33 % → "saves tokens".
- **H3** (staged council with the truth bell, seed 0's answer on "I don't know", against the council without bell): 70 vs 67 (3 : 0, p = 0.125) → "level"; tokens 77 % → "similar".
- **H4** (the same council against MIT's edit): 70 vs 61 (12 : 3, p = 0.0176) → "beats MIT"; tokens 97 % → "similar".
- [descriptive] The bell rang in 42 of 100 runs. Oracle ceiling (`oracle_correct`): 64. Stopping at the first probe hit, also in runs that would close by themselves (`first_probe_hit_correct`): 44. The council that may abstain: 69 correct, 16 wrong, 15 abstentions.

N62 on F3 [pre-registered]: **HE** wrong 46 → 32 (14 : 0, p < 0.0001), correct 54 → 56 (0 : 2) → "confirmed". **HT** back room 9,111 against 28,243 (32 %) → "saves tokens"; council 40,052 against 51,218 (78 %) → "similar". [descriptive] In none of the 12 abstentions would the council without bell have been right. Both fresh sets together (200): wrong 79 → 48 (31 : 0), correct 121 → 125 (0 : 4), 27 abstentions; share of correct answers among the answers given 60.5 % → 72.3 %. [descriptive, post hoc] Of the remaining wrong answers, 7 / 14 of 16 / 32 come from the intuitions' majority (back room not asked).

N65, seed 1 in the back room, F2 + F3 (200) [pre-registered]: **HE** wrong 76 → 42 (35 : 1, p < 0.0001), correct 124 → 126 (1 : 3) → "confirmed". **HT** back room 7,969 against 21,119 (38 %) → "saves tokens"; council 34,520 against 42,939 (80 %) → "similar". [descriptive] R-MLP seed 1 alone: 114 of 200 (seed 0: 101).

## Summary: Section 3.21 (N63, N64, N66)

| R-MLP alone, F2 + F3 (200) | correct | wrong | "I don't know" | tokens per correct answer |
|---|---|---|---|---|
| no bell (`r0`) | 101 | 99 | 0 | 24,141 |
| bell with truth probe (`r50`, N50) | 110 | 53 | 37 | 7,881 |
| self-decision, free (`rsf`, N63) | 112 | 49 | 39 | 7,801 |
| self-decision, boxed (`rsk`, N63) | 115 | 85 | 0 | 7,109 |
| own closing tendency (`rn`, N64) | 103 | 57 | 40 | 8,435 |

| staged council, F2 + F3 (200) | correct | wrong | abstain |
|---|---|---|---|
| without bell (`bh0`) | 121 | 79 | 0 |
| truth bell, abstaining (`bhe`) | 125 | 48 | 27 |
| own closing tendency, abstaining (`bhn`) | 122 | 51 | 27 |
| boxed self-decision (`bhsk`) | 127 | 73 | 0 |

[pre-registered] **H63a / H63b** (self-decision against no bell): free 112 vs 101 (13 : 2, p = 0.0037), boxed 115 vs 101 (14 : 0, p < 0.0001) → "self brings more" / "self brings more"; tokens 32 % / 29 % → "saves tokens" / "saves tokens". **H63c** (council with the boxed self-decision against the council without bell): 127 vs 121 (6 : 0, p = 0.0156) → "more". **H63d** (the same council, honesty rule): wrong 79 → 73, correct 121 → 127, 0 abstentions → formally "confirmed" (the fewer wrong answers became correct ones; the rule was written for abstention). **H64a** (own-tendency council, honesty rule): wrong 79 → 51 (29 : 1), correct 121 → 122 → "confirmed". **H64b** (against the council with the probe): wrong 51 vs 48, correct 122 vs 125 → "equivalent". [descriptive] Of the 85 runs stopped at the deadline, 0 wrote "I don't know" inside the box and 1 in the free answer; 38 free answers had no box when they reached the 1,024-token limit.

| F4 (100), N66 | correct | wrong | "I don't know" / abstain | tokens per correct answer |
|---|---|---|---|---|
| R-MLP without bell (`r0`) | 55 | 45 | 0 | 25,387 |
| boxed self-answer (`rsk`) | 58 | 42 | 0 | 8,980 |
| own tendency decides (`rk`) | 55 | 21 | 24 | 9,656 |
| bell with truth (`r50`) | 58 | 22 | 20 | 9,241 |
| council without bell (`bh0`) | 59 | 41 | 0 | 52,846 |
| council with `rk`, abstaining (`bhk`) | 59 | 24 | 17 | 41,939 |
| council with the probe, abstaining (`bhe`) | 60 | 26 | 14 | 41,306 |

[pre-registered on F4] **H66a**: wrong 41 → 24 (17 : 0, p < 0.0001), correct 59 → 59 → "confirmed"; in none of the 17 abstentions would the back room without bell have been right. **H66b** (against the council with the probe): wrong 24 vs 26, correct 59 vs 60 → "equivalent". **H66c** (boxed self-answer against no bell): 58 vs 55 (3 : 0, p = 0.125) → "level". **H66d**: back room 38 % of the tokens per correct answer → "saves tokens"; council 79 % → "similar". [descriptive] Over F2, F3 and F4 the boxed self-answer gains 17 problems against no bell and loses 0. [descriptive, after the fact] Score (correct − 2 · wrong) / N: -0.185 → +0.145 on F2 + F3 (`bh0` → `bhe`), -0.23 → +0.11 on F4 (`bh0` → `bhk`).

## Files

| file | rows | serves |
|---|---|---|
| `per_item_n60.csv` | 250 | Section 3.19, N60 (N44 set and N45 set) |
| `per_run_n60b.csv` | 750 | Section 3.19, N60b and N60 H3 |
| `per_item_fresh.csv` | 300 | Section 3.20 (N61, N50 on F2; N62 on F3) and Section 3.21 (N63, N64 on F2 + F3; N66 on F4) |
| `per_item_n65_seed1.csv` | 200 | Section 3.20, N65 (R-MLP seed 1 on F2 + F3; join with `per_item_fresh.csv` on `set` and `id`) |
| `truth_probe_layer15.npz` | – | the frozen truth probe of N50, N62, N65 and of the councils `bhe` in 3.21 |
| `closing_tendency_threshold.json` | – | τ_F and how it was derived (N64, N66) |

Common columns: `set`, `id` (MATH training id), `level` (1–5), `gold` (reference answer). For each run or arm: `_pred` (content of the last
`\boxed{}`; for an answer written after a cut or at the deadline the first, except `rsf`; empty if none or "I don't know"), `_correct` (1 if `_pred` matches `gold` under math-verify),
`_tokens` (tokens as counted in the report), `_end` (`eos`, `limit` = 32K cap, `loop_abbruch` = loop stop). Values are 0/1 unless stated;
an empty cell means the arm was not part of a test on that set.

`per_item_n60.csv`: `intuition_s0/s1/s2_*`, `r_mlp_*`, `sgne_cc_*`, `mit_*`; `seeds_0_1_disagree` (1 if seeds 0 and 1 disagree: the lean
council asks its back room, the staged council asks seed 2); `staged_answer_from` (`s0`, `s1` or `back_room`; the same for full and staged
councils and for both back rooms); `lean_rmlp_correct`, `lean_sgne_correct`, `staged_rmlp_correct`, `staged_sgne_correct` (full = staged).

`per_run_n60b.csv`: one row per run of R-MLP, MIT's edit and SGNE-CC on both sets. `door_token` (position of the first `</think>`, empty if
none); `class` (`T` with door; `O+` without door, correct value somewhere in the thinking; `O-` without door, never); `correct_value_in_thinking`;
`first_correct_value_token` and `tokens_after_first_correct_value` (to the end of the thinking); `signs`, `signs_with_value`,
`signs_with_correct_value`; `first_sign_value_correct`, `last_sign_value_correct` (empty without a sign with value). R-MLP rows only:
`door_kind` (the last sign that ends at most 800 characters before the door: `sign_correct_value`, `sign_wrong_value`, `sign_no_value`, `no_sign`, or
`no_door`) and `has_sign_with_correct_value` (H3 counts runs with 1 here and, of them, those with `door_kind` = `sign_correct_value`).

`per_item_fresh.csv`: `intuition_s0/s1/s2_*`; `seeds_0_1_disagree`, `staged_answer_from` (as above, the same for every council of the row);
`r0_*`, `door_token`, `deadline_reached` (1 if no door before token 8,192: the bell rings); for `r61`, `r50`, `rn`, `rsf`, `rsk`, `rk`:
`_pred`, `_correct`, `_idk`, `_tokens` (rows without bell repeat `r0`); `r61/r50/rn_cut_tokens_kept` (thinking tokens kept before `</think>`
was inserted; empty without a cut); `rsf_kind`, `rsf_end` (`eos` or `limit` of the free answer); F2 only: `first_probe_hit_correct`,
`oracle_correct` (no door before the deadline: 1 if some value statement before the deadline was correct; otherwise `r0_correct`), `mit_*`.
Councils: `bh0_correct`, `bh50_correct` (an abstention of `r50` replaced by seed 0's answer), and `_correct` / `_abstain` for `bhe`, `bhn`,
`bhsk`, `bhk`. Arms per set: F2 and F3 `r61`, `r50`, `rn`, `rsf`, `rsk`; F4 `r50`, `rn`, `rsk`, `rk`. Councils: F2 and F3 `bh0`, `bh50`, `bhe`, `bhn`,
`bhsk`; F4 `bh0`, `bhe`, `bhsk`, `bhk`.

`per_item_n65_seed1.csv`: `r0_s1_*`, `door_token_s1`, `deadline_reached_s1`, `r50_s1_*` (as `r50`), `staged_answer_from` (same intuitions,
same value as in `per_item_fresh.csv`), `bh0_s1_correct`, `bhe_s1_correct`, `bhe_s1_abstain`.

`truth_probe_layer15.npz` (NumPy, plain arrays; `numpy.load(path, allow_pickle=False)`): `w` (1,024 weights), `b` (bias), `tau` (threshold),
`schicht` (layer index, 15), `frist` (deadline, 8,192). SHA-256 d98e46170b6758adfdda288d3ee99f4bf2cc38f3ab7761969990106941d781b8.

`closing_tendency_threshold.json`: τ_F, the signal, the 2 % rule and the development counts (360 runs, per development set).

To recount a staged council from a row: tokens = `intuition_s0_tokens` + `intuition_s1_tokens` (+ `intuition_s2_tokens` if
`seeds_0_1_disagree`) (+ the back room's `_tokens` if `staged_answer_from` = `back_room`); the answer is that of `s0`, `s1` or the back room.

Limits: one seed per thinking arm (two for R-MLP on F2 + F3); the deadline, the probe and the sentence come from outside the model; the
intuitions and the thinking runs ran on different machines; only mathematics.
