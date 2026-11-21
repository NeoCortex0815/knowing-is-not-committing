# Per-item rows: ablations of SGNE-CC under our protocol (Qwen3.5-0.8B)

SGNE-CC is a weight edit by **Igor M. Zhuk** (on Hugging Face: Nondual-Observer; model `Nondual-Observer/Qwen3.5-0.8B-SGNE-CC`, Apache-2.0). The method
is his; these rows are our independent check of its parts (report v0.5, Section 3.13, tests N41 and the seed-1 repeat). Every arm is
assembled only from released tensors (the unedited Qwen3.5-0.8B, SGNE-CC and MIT's edit); for each we checked that exactly the swapped
tensors differ from the unedited model. The full SGNE-CC run with seed 0 is in `../n40-sgne-cc`.

## Arms

- `mit`: MIT's edit (addition of one direction to 64 columns of `down_proj` in layers 15 and 19).
- `s1519`: SGNE-CC's rotated columns in layers 15 and 19 only (MIT's place).
- `s_mlp`: SGNE-CC's 15 changed MLP `down_proj` layers only.
- `s_gdn`: SGNE-CC's GatedDeltaNet part only (9 `out_proj` layers and the gate row in layer 16).
- `sgne_cc`: full SGNE-CC (seed 1 here; seed 0 in `../n40-sgne-cc`).

## Problems

The same 50 fresh MATH training problems as in `../n40-sgne-cc`, drawn without model contact. Thinking on, seed as given.

## Setup (the same for every run)

- llama.cpp server, q8_0 GGUF, 6 parallel slots, vLLM-style sampling: temperature 0.6, top_p 0.95, top_k 20, presence penalty 1.5
  (penalties → temperature → top_k → top_p), at most 32,768 new tokens. Tokenizer and chat template of `Qwen/Qwen3.5-0.8B`.
- Thinking runs: chat template with thinking on. Answer-mode runs: the prompt ends with the official non-thinking pattern
  `<think>\n\n</think>\n\n` (enable_thinking = false); everything else unchanged.
- Early stop of clear loops: from 4,096 tokens on, a run stops when the duplicate-8-gram share over the last 400 words exceeds 0.9.
- Grading with math-verify in the main thread, against the `gold` answer (re-graded copy of every run before any count).

## Summary

| arm | seed | correct (of 50) | correct value in thinking | of those, committed | loop stop or 32K cap | tokens per correct answer |
|---|---|---|---|---|---|---|
| unedited (post-trained) | 0 | 5 | 24 | 21% | 90% | 144,909 |
| pre-trained base (reference) | 0 | 27 | 33 | 82% | 20% | 20,265 |
| WT-A (ours) | 0 | 19 | 26 | 65% | 50% | 56,523 |
| MIT's edit (addition, layers 15 and 19) | 0 | 20 | 29 | 69% | 46% | 57,246 |
| S-1519: SGNE-CC in layers 15 and 19 only | 0 | 15 | 32 | 47% | 58% | 75,159 |
| S-MLP: SGNE-CC's 15 MLP layers only | 0 | 13 | 18 | 61% | 20% | 19,098 |
| S-GDN: SGNE-CC's GatedDeltaNet part only | 0 | 26 | 35 | 71% | 34% | 35,687 |
| S-GDN | 1 | 29 | 37 | 78% | 30% | 29,488 |
| SGNE-CC, full | 0 | 22 | 20 | 80% | 4% | 14,961 |
| SGNE-CC, full | 1 | 20 | 16 | 81% | 8% | 17,373 |

Seed-1 reading, fixed in advance: "effect repeated" (S-GDN with seed 1: at least 20 of 50 and committed ≥ 0.60).
One or two seeds per arm, n = 50. Differences of a few problems are within noise.

## Columns (`per_item.csv`)

| column | meaning |
|---|---|
| `arm`, `seed` | arm as above; sampling seed |
| `id`, `gold`, `pred` | problem id, reference answer, content of the last `\boxed{}` (empty if none) |
| `correct` | 1 if `pred` matches `gold` under math-verify |
| `end`, `tokens`, `think_closed` | `eos`, `limit` (32K cap) or `loop_abbruch` (loop stop); generated tokens; 1 if the thinking block was closed |
| `correct_value_in_thinking` | 1 if a candidate value in the thinking matches `gold` (broad counter, an upper bound on "found") |
| `tokens_after_first_correct_value` | tokens from the first correct candidate to the end of the thinking (empty if none) |
