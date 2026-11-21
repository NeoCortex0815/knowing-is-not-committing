# Per-item rows: the council (B+H) with a committing back room (Qwen3.5-0.8B)

Report v0.5, Section 3.14, tests N42–N45. **B+H** is our council rule (Section 3.11): three answer-mode runs (intuitions) answer
first; if at least two agree (math-verify in both directions), that answer is delivered, otherwise one thinking run, the back room,
decides. *Lean*: only the intuitions with seeds 0 and 1; if they agree, deliver, otherwise the back room. Here the back room is
SGNE-CC, a weight edit by **Igor M. Zhuk** (`Nondual-Observer/Qwen3.5-0.8B-SGNE-CC`, Apache-2.0), or one of the other arms. The
rule is ours; SGNE-CC is his. Tokens per correct answer count every intuition plus the back room where it is used.

## Sets

- **N42/N43:** the 50 fresh MATH training problems of `../n40-sgne-cc`, existing runs only. Intuitions of the unedited model
  (`unedited`) and of our own-direction model (`own`), seeds 0–2; back rooms with thinking, seed 0.
- **N44:** the 150 problems of N30 (Section 3.11) with the own-direction intuitions, MIT's edit and WT-A from N30; new is only SGNE-CC
  with thinking (seed 0). The problems are new to SGNE-CC, but not to the other arms.
- **N45:** 100 fresh MATH training problems (level mix of MATH-500, 8 / 18 / 21 / 26 / 27, seed 202611201), with the unedited model's
  intuitions (seeds 0–2), SGNE-CC and MIT's edit with thinking (seed 0), all new.

## Setup (the same for every run)

- llama.cpp server, q8_0 GGUF, 6 parallel slots, vLLM-style sampling: temperature 0.6, top_p 0.95, top_k 20, presence penalty 1.5
  (penalties → temperature → top_k → top_p), at most 32,768 new tokens. Tokenizer and chat template of `Qwen/Qwen3.5-0.8B`.
- Thinking runs: chat template with thinking on. Answer-mode runs: the prompt ends with the official non-thinking pattern
  `<think>\n\n</think>\n\n` (enable_thinking = false); everything else unchanged.
- Early stop of clear loops: from 4,096 tokens on, a run stops when the duplicate-8-gram share over the last 400 words exceeds 0.9.
- Grading with math-verify in the main thread, against the `gold` answer (re-graded copy of every run before any count).

## Summary, 50 problems (cells: correct of 50 · tokens per correct answer)

| back room (thinking) | alone | full B+H, unedited intuitions | lean B+H, unedited intuitions | full B+H, own-direction intuitions |
|---|---|---|---|---|
| unedited | 5 · 144,909 | 21 · 74,048 | 19 · 60,874 | 25 · 63,575 |
| WT-A (ours) | 19 · 56,523 | 25 · 72,980 | 23 · 65,470 | 25 · 74,053 |
| MIT's edit | 20 · 57,246 | 24 · 77,643 | 23 · 67,186 | 25 · 72,397 |
| SGNE-CC | 22 · 14,961 | 24 · 57,587 | 24 · 40,786 | 26 · 57,406 |
| S-GDN (SGNE-CC's GatedDeltaNet part) | 26 · 35,687 | 28 · 63,401 | 27 · 53,940 | 30 · 58,687 |

## Summary, N44 and N45

| | N44 (150) | N45 (100) |
|---|---|---|
| MIT's edit alone | 67 · 49,089 | 49 · 44,715 |
| SGNE-CC alone | 62 · 14,882 | 52 · 11,736 |
| intuitions alone, seeds 0 / 1 / 2 | 69 / 72 / 65 | 58 / 48 / 46 |
| full B+H with SGNE-CC | 78 · 57,654 | 61 · 37,985 |
| lean B+H with SGNE-CC | 70 · 47,676 | 59 · 31,342 |
| H1 lean vs MIT (only B+H : only MIT, one-sided p) | 14 : 11, p = 0.345 | 18 : 8, p = 0.0378 |

Readings fixed in advance (dated log, 20 Nov 2026): H1 "level" / "similar" (N44), "beats MIT" /
"similar" (N45); H2 "B+H adds" / "costs tokens" (N44), "B+H adds" / "costs tokens" (N45);
H3 "open" (N44), "open" (N45). (The log states them in German; translations as in the report.)
Both sets together, descriptive: lean B+H with SGNE-CC 129 vs MIT 116 of 250.

## Files

- `per_item_50.csv`: every run on the 50 problems that N42/N43 use (answer mode and thinking): `run`, `seed`, `id`, `gold`, `pred`,
  `correct`, `end`, `tokens`.
- `per_item_n44_n45.csv`: one row per problem of N44 and N45: `set`, `id`, `level`, `gold`; for each of `intuition_s0`, `intuition_s1`,
  `intuition_s2`, `sgne_cc`, `mit`: `_pred`, `_correct`, `_tokens`; then `bh_full_correct`, `bh_full_from_back_room`, `bh_lean_correct`,
  `bh_lean_from_back_room` (1 if the back room decided).
