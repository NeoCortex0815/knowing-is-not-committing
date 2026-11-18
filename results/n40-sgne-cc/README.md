# Per-item rows: SGNE-CC under our protocol (Qwen3.5-0.8B)

Cross-stack check of the SGNE-CC weight edit by Nondual-Observer, announced in the Hugging Face discussion
"Independent evaluation: weight edits and sensitivity to decoding settings (MATH-500 @ 32K)"
(RikiyaT/Qwen3.5-0.8B-weight-space-programming, #5). One CSV, 50 rows.

## Model

- Weights: `Nondual-Observer/Qwen3.5-0.8B-SGNE-CC`, revision `a0f617d4fee20033c24b86192120641e495aa297`, `model.safetensors`
  (SHA-256 `d0b745ce6e48ff0b2b22f9dadf229ba246afabebd9ae8308f07a4cd1824d0324`), Apache-2.0. Tokenizer, chat template and config
  from `Qwen/Qwen3.5-0.8B` (the tokenizer file is byte-identical to the one in the SGNE-CC repository).
- Converted to a q8_0 GGUF with llama.cpp's `convert_hf_to_gguf.py`. Against the q8_0 GGUF of the unedited model, exactly 25 of 335
  tensors differ (15 `ffn_down`, 9 `ssm_out`, 1 `ssm_alpha`), matching the patch.

## Setup (the same as for our base and post runs)

- 50 fresh MATH training problems, drawn without model contact, the same as in our base/post comparison in discussion #2.
- Chat template with thinking on, prompt "Please reason step by step, and put your final answer within \boxed{}."
- llama.cpp server, 6 parallel slots, vLLM-style sampling: temperature 0.6, top_p 0.95, top_k 20, presence penalty 1.5
  (penalties → temperature → top_k → top_p), at most 32,768 new tokens, seed 0.
- Early stop of clear loops: from 4,096 tokens on, a run stops when the duplicate-8-gram share over the last 400 words exceeds 0.9.
- Grading with math-verify (main thread), against the `gold` answer.

## Summary

| | post (unedited) | pre-trained base | SGNE-CC |
|---|---|---|---|
| correct (of 50) | 5 | 27 | **22** |
| stopped at the 32K cap or by the loop stop | 90% | 20% | **4%** |
| at the 32K cap (share of all runs) | 26% | 18% | **4%** |
| mean generated tokens | 14,491 | 10,943 | **6,583** |
| correct value appears in the thinking | 24 | 33 | **20** |
| of those, committed (final answer correct) | 5 (21%) | 27 (82%) | **16 (80%)** |
| generated tokens per correct answer | 144,909 | 20,265 | **14,961** |

- SGNE-CC against post, paired: 17 problems solved only by SGNE-CC, 0 only by post.
- 22 correct in total: in 6 of them our counter does not see the correct value in the thinking before the final answer.
- "Correct value appears in the thinking": any candidate value in the thinking block (boxed answers, "the answer is", and "= W / is W"
  statements), checked with math-verify. This is a broad counter, an upper bound on "found".
- One seed per model, n = 50. Differences of a few problems are within noise.

## Columns

| column | meaning |
|---|---|
| `id`, `gold`, `pred` | problem id, reference answer, content of the last `\boxed{}` (empty if none) |
| `correct` | 1 if `pred` matches `gold` under math-verify |
| `end`, `tokens`, `think_closed` | `eos`, `limit` (32K cap) or `loop_abbruch` (loop stop; none here); generated tokens; 1 if the thinking block was closed |
| `correct_value_in_thinking` | 1 if a candidate value in the thinking matches `gold` |
| `tokens_after_first_correct_value` | tokens from the first correct candidate to the end of the thinking (empty if none) |
| `fallback_correct_if_no_box` | rough approximation of a fallback read of runs without `\boxed{}` (last answer phrase, else last number); 0 for all rows |
