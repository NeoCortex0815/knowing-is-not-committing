# Per-item rows: long-horizon 16K protocol, six cells (Qwen3.5-0.8B)

These are the per-item outcomes behind the table we posted on 10 Nov 2026 in the Hugging Face discussion
"Independent evaluation of the released edit (16K thinking-on protocol)" (RikiyaT/Qwen3.5-0.8B-weight-space-programming, #2).
One CSV, 300 rows: six cells × MATH-500 rows 0–49.

## Setup

- MATH-500 rows 0–49 in file order, chat template with thinking on, prompt "Please reason step by step, and put your final
  answer within \boxed{}."
- temperature 0.6, top_p 0.95, top_k 20, no repetition or presence penalty (except `post_pp1.5`: presence penalty 1.5), at most
  16,384 new tokens, no early stopping, seed 0.
- llama.cpp server, q8_0 GGUF of each model, 6 parallel slots. Parallel slots act like a different seed, so a re-run should
  match the rates within noise, but not every item.
- Four server restarts during the night (GPU memory): the runs in flight at the time were redrawn with the same seed.

## Cells

| cell | model |
|---|---|
| `base` | Qwen3.5-0.8B-Base (pre-trained) |
| `post` | Qwen3.5-0.8B (post-trained release), unedited |
| `astra` | the released edit (RikiyaT/Qwen3.5-0.8B-weight-space-programming) |
| `wt_a` | `own_direction` plus a truth-gated trigger: 16 rarely active MLP neurons in layer 15 rewritten (gate: truth probe above a threshold; up: candidate-end detector; down: closing gradient) |
| `own_direction` | our own loop direction, built with the released edit's recipe: rank-1 edit of `mlp.down_proj` in layers 15 and 19, top-64 columns, α = 6; cosine 0.76/0.77 to the released direction |
| `post_pp1.5` | `post` with presence penalty 1.5 |

## Columns

| column | meaning |
|---|---|
| `cell`, `row`, `id` | cell, MATH-500 row (file order), MATH-500 `unique_id` |
| `gold`, `pred` | reference answer; content of the last `\boxed{}` (empty if none) |
| `correct_mathverify` | 1 if `pred` matches `gold` under math-verify |
| `correct_string` | 1 if the normalized strings match (closer to the scoring in note #1) |
| `end`, `tokens`, `think_closed` | `eos` or `limit` (16,384-token cap); generated tokens; 1 if the thinking block was closed |
| `cap` | 1 if `end` is `limit` |
| `dup8_token` | share of duplicate 8-grams over the whole generation, counted over model tokens: 1 − distinct/all |
| `dup8_word` | the same, counted over words of the decoded text (`text.split()`) |
| `loop_token`, `loop_word` | 1 if the share in that unit is above 0.3 |
| `strict_token`, `strict_word` | loop flag and cap |

## Summary (percent of 50)

| cell | correct (math-verify) | correct (string) | cap | loop (token) | loop (word) | strict (token) | strict (word) |
|---|---|---|---|---|---|---|---|
| base | 52 | 48 | 30 | 30 | 20 | 22 | 16 |
| post | 2 | 2 | 100 | 100 | 100 | 100 | 100 |
| astra | 36 | 28 | 64 | 90 | 62 | 64 | 48 |
| wt_a | 40 | 34 | 58 | 78 | 50 | 58 | 46 |
| own_direction | 24 | 24 | 76 | 96 | 74 | 74 | 60 |
| post_pp1.5 | 8 | 6 | 92 | 96 | 88 | 92 | 88 |

One seed per cell, n = 50, one model pair.
