# Knowing Is Not Committing

### Replicating MIT's weight-space edit and programming a truth-gated reflex into a 0.8B reasoning model · report

**Dave Uhlemann (NeoCortex)** · independent researcher

Code, data and pre-registration log: [github.com/NeoCortex0815/knowing-is-not-committing](https://github.com/NeoCortex0815/knowing-is-not-committing) · questions and corrections are welcome as GitHub issues.

> *“Find out whether the model has the solution, and when, and let the inner push through, despite the pressure.”*
> — Dave Uhlemann, 6 Nov 2026

*Version 0.3 · 2026-11-09 · work period 4–9 November 2026 · not peer-reviewed · prepared with AI assistance (see Section 8); all measurements were run locally on the author's machines. Version 0.3 concludes this report; further follow-up tests on the question in its title remain reserved.*

> **Status of the evidence.** We mark every claim as one of three kinds:
> - **[pre-registered]**: tested with a reading fixed in a dated log before the run;
> - **[descriptive]**: measured, but not pre-registered;
> - **[interpretation]**: our reading of the data.
>
> All results come from a 0.8B model.
> - Most results rest on a single seed; second seeds exist for parts of the data.
> - Part of the data comes from a development set that we used several times.
> - MATH-500 problems 161–300 served as the confirmation set (Section 3.9).
> - Problems 301–370 were used once, late on 8 Nov, for a second confirmation of the answer-mode results, with readings fixed in
>   advance (Section 3.10). Problems 371–500 remain untouched.
> - 150 MATH training problems that had never been used served once, for the publicly pre-registered test N30 (Section 3.11).
> - Section 3.12 re-analyses existing transcripts of problems 161–300 with a reading fixed in advance; it uses no new problems.
>
> **What we mean by "knowing".** A frozen linear probe on the model's hidden states rates the correct value as true while it is in
> the context. This is a measurement, not a claim about certainty.

> **New in version 0.3** (everything else as in v0.2 of 8 Nov 2026):
> - Section 3.11: the result of N30, the test pre-registered publicly in v0.2, with a descriptive breakdown by the strength of
>   agreement.
> - Section 3.12: N31, a check of the title question on internal signals, with a reading fixed in advance in the dated log.
> - Also: a corrected interpretation in Section 3.9, updated agreement figures in Sections 3.10 and 5, the abstract, TL;DR items
>   10, 12 and 13, the next steps and two new references (Li et al., 2026; Farquhar et al., 2024).

**Abstract.** MIT's weight-space edit reduces reasoning loops in Qwen3.5-0.8B. We rebuilt that edit independently, wrote a truth-gated
reflex into 16 MLP neurons, and ran a series of pre-registered tests on fresh MATH-500 problems.
- Three findings carry the report:
  - (1) The model often *knows* a correct answer long before it *commits* to it. A linear probe reads the truth inside the
    reasoning. Our reflex closes the reasoning at the right moment, but a close imposed from outside is not a commitment: on
    fresh problems the model reopens its reasoning after 77 % of its closes.
  - (2) Without its thinking block (answer mode), our edited model is close to MIT's edit with thinking: 71 vs 80 of 140, at less
    than half the tokens per correct answer.
  - (3) When two independent answer-mode runs agree, 91 % of the answers are right (pooled over three sets). A fourth test,
    pre-registered publicly, gave 77 % on 150 fresh problems (Section 3.11).
- Sampling settings alone move MIT's own edit from 25 % to 55 %.
- New in version 0.3:
  - **N30** (pre-registered publicly in v0.2, 150 fresh problems): a council of three answer-mode runs, with our own thinking run
    as fallback, solves 74 problems, against 66 for answer mode alone ("holds") and 67 for MIT's edit with thinking ("at least
    level"; +7, one-sided McNemar p = 0.105). As a delivery gate, agreement was less precise than in earlier sets: 77 % for two
    runs ("open"), 66 % for a majority of three ("does not carry").
  - **N31** (reading fixed in advance): at the values the model writes while reasoning, its own tendency to stop reasoning does
    not track whether the value is correct (AUC 0.51), while the probe does (0.68). MIT's edit is no exception (0.43). This
    supports finding (1) at the level of internal signals.
- We report every refuted reading alongside the confirmed ones.

---

## TL;DR

1. **Sampling protocol decides half of the effect.** On the same 40 MATH-500 problems, MIT's published edit scores **55 %** with vLLM-style sampling and **25 %** with llama.cpp's default sampling. [descriptive]
   - The llama.cpp default differs in two ways: the repetition penalty only looks back over the last 64 tokens, and temperature is applied last.
2. **The loop direction is findable without a search agent.** Our own direction (cosine 0.76/0.77 to MIT's) lifts the base model from **10 % to 37.5 %** on those 40 problems [descriptive]. MIT's edit reaches 55 % there.
   - We used the same edit recipe and derived the direction from base-model transcripts.
3. **ERGORE ties MIT on problems 1–160, but not on fresh problems.** ERGORE is our own loop direction plus an explicit,
   conditioned *closing* push. [pre-registered]
   - 1–160: **79 vs 77** (p = 0.85). ERGORE uses 13 % fewer tokens.
   - **Fresh problems 161–300: 65 vs 80 of 140** (7 : 22, p = 0.008; −10.7 points, 95 % CI −18.0 to −3.4). The reading fixed in
     advance is "MIT level not reached".
   - A second seed on one block (261–300) shrinks that block's gap from 14 : 22 to 16 : 16. [descriptive] The gap is real, but
     probably smaller than seed 0 suggests.
4. **Models know more than they act on.** [pre-registered / descriptive]
   - A linear truth probe at layer 13, upstream of every edit, separates correct from wrong candidate answers inside the reasoning (AUC 0.96 on practice data). In the field it is conservative: on the test's final answers it flags 1 of 86 correct answers as unsure and catches 8 of 16 wrong ones.
   - The model keeps thinking for a median of **~2,000 tokens (T = 0.6) to ~6,000 tokens (T = 1.0) after it first writes the correct answer**.
   - Forcing a final answer at the end of the budget lifts every model: one base-like variant goes from 11 to 28 of 60. It also shrinks the differences between edits to non-significance.
5. **Blunt pressure has a price.** [pre-registered as a harm check / descriptive]
   - Our unconditional closing push costs instruction following: **IFEval 61/120**, against 74 without the push (p = 0.041) and 87 for MIT.
   - It also produces "empty commits", where the model stops thinking without a solution. These are 22 of 26 errors on a development set.
6. **A truth-gated trigger written into the weights (WT-A).** Its mechanism works on fresh problems; its accuracy does not reach
   MIT's.
   - WT consists of 16 neurons in layer 15. They fire only when a candidate answer has just been written *and* the internal truth
     signal is high. They then push along the measured closing gradient.
   - **Development set** (n = 60): 31 vs 23 correct against the same model without the trigger, and +8 again with a second seed
     [descriptive]. 64 % fewer tokens on problems both solve. The pre-registered gate stayed closed because a probe check failed.
   - **Fresh problems 161–300**, test fixed before any of these runs existed (H-WT2): WT-A closes right after the correct value in
     **65 %** of opportunities, MIT in **36 %** (p = 0.0001). Its fast closes are right in 61 % vs 44 %. [pre-registered]
   - **Accuracy there: 61 vs 80 of 140** (−13.6 points, paired bootstrap 95 % CI −21.4 to −5.7). [descriptive] With a second seed on 161–260, 47 vs 58 of 100.
7. **Why the trigger is not enough** [descriptive, post hoc]:
   - **One path to success:** 51 of WT-A's 61 correct answers follow closes driven by the trigger (Section 3.9). MIT also checks for ~12,000 more tokens and
     then commits on its own (44 of 80).
   - **A forced close is not an inner close:** after a trigger close, WT-A reopens its reasoning in the answer part (a second
     `</think>`) in 83–100 % of development runs. On fresh problems the figure is 77 % of all closes and 58 of 61 correct runs,
     against 16 % for MIT.
     - Among the 32 silent fresh runs, which never deliver, the rate is 12 of 32. The three numbers describe different groups of runs.
     - WT-A's successful path is almost always: trigger close, renewed reasoning, then its *own* second close, then delivery.
   - **Depth:** the truth signal fades with *loops and difficulty*, not with depth into the reasoning.
8. **An honest "I don't know" from the inside signal.** [pre-registered] The frozen truth probe, read at the delivered answer,
   separates forced answers with AUC 0.83.
   - Abstaining when it stays low turns forced answering from harmful into useful: score (correct − 2·wrong)/N goes from −0.30 to
     +0.17.
   - 327 of 380 abstentions would have been wrong.
9. **Answer mode ("front room") is our strongest own path.** Without the thinking block, the model reasons visibly in its answer.
   - Development range [descriptive]: our own-direction model solves 77 of 160, exactly as many as MIT with thinking (22 : 22),
     at ~40 % of the tokens.
   - Fresh problems 161–300 [pre-registered]: **71 vs 80 of 140** for MIT with thinking (−6.4 points, 95 % CI −15.0 to +2.1). That is "open" by the reading fixed in
     advance: holds at ≥ 73, refuted at ≤ 66. It needs 16,600 instead of 37,700 tokens per correct answer.
   - MIT itself in answer mode reaches only **59 of 140** (27 : 6 against MIT with thinking, p = 0.0003) [pre-registered]. A back
     room pays off when it has a working exit; ours does not have one yet.
   - The advantage is not an artefact of the presence penalty: the same +2 with penalty 0 and 1.5 (n = 20) [pre-registered].
     The front room is not more stable across seeds than the back room: 75 % of problems are solved the same way in both seeds
     [pre-registered, refuted].
10. **The front room knows when it is sure: a council of intuitions.** Several answer-mode runs answer independently. When they
    agree, the model delivers; only disputed cases go to the back room.
    - **Two intuitions** [pre-registered, three confirmations]. When two runs with different seeds give the same answer, it is
      right in **37 of 38** cases on 161–260, 13 of 17 on 40 new training problems, and **28 of 31 on the untouched problems
      301–370**. Pooled over the three sets, 78 of 86 are right (91 %); the pooled figure is descriptive, because each set was
      pre-registered on its own. When the runs disagree, the first run is right in only 13–32 %. A fourth test, pre-registered
      publicly in v0.2, gave 77 % on 150 fresh problems (item 12).
    - **Three intuitions** [pre-registered, "open" by one point]. A majority of three delivers on 62 of 100 problems instead of
      38, and 89 % of these are right (target: 90 %). The net score (correct − 2·wrong)/N rises from +0.35 to +0.41. When all three
      agree, 29 of 29 are right.
    - **A probe trained on answer text** [pre-registered; "open" in all three tests]. It reads correctness at the delivered answer
      with AUC 0.76–0.85 on new data; the probe trained on thinking text reaches 0.68.
      - It adds only +0.01 to +0.05 over answer length and difficulty.
      - Its apparent edge on quick answers did not replicate on untouched problems (0.61 vs 0.60).
      - Used as an extra delivery gate it hurts: score +0.13 instead of +0.31 with agreement alone.
      - Used as a **referee** between two disagreeing intuitions it helps [pre-registered]: 11 instead of 7 correct answers. The
        agreeing cases are not touched. With only 18 decisive problems this is fragile: the bootstrap 95 % interval for the gain
        is −1 to +10.
    - **Switching rooms** [pre-registered / descriptive].
      - With two intuitions, falling back to WT-A's back room loses: 54 vs 57 of 100 for answer mode alone [pre-registered].
      - With three intuitions it wins: 62 vs 57 [descriptive].
      - With MIT's back room as fallback: 63 (two intuitions) and 66 (three), against 58 for MIT alone [descriptive].
      - On the untouched problems 301–370 [pre-registered]: "two agree → answer mode, otherwise MIT's back room" solves **40 of 70**.
        MIT alone solves 38 and answer mode alone 35. Agreement precision is 90 %, but the rule costs more tokens per correct
        answer than MIT (56,800 vs 41,000). The reading is therefore **open**. The gain comes from both rooms: precision in front
        (28 vs 26 on the agreeing problems) and MIT's exit at the back (12 vs 7 on the rest).
    - **Two modes, two costs.**
      - A *single* answer-mode run is the efficient path: 16,600 instead of 37,700 tokens per correct answer (item 9).
      - Asking *several* intuitions buys precision with tokens. Combined with a back room, it can cost more per correct answer than
        MIT alone.
11. **Negative results.** [pre-registered]
    - A first gate along a state-difference direction failed all criteria.
    - A "thinking switch" based on the inner signal at the end of the prompt was refuted (p = 0.13).
    - Probe cascade, notes for a second chance and loop-based "state doors" were refuted (Section 3.10).
    - Inserting `</think>` from outside does not produce an inner "finished", not even at the model's own closing phrase. MIT
      then delivers in 36 % of cases, against 18 % without a closing phrase [descriptive].
    - Replaying WT-A's 32 silent answer parts rescues almost nothing.
      - We re-ran it with a fair cap: our first cap of 1,024 tokens was too short, because even WT-A's own correct answer parts
        have a median of ~2,000 tokens.
      - With 4,096 tokens, 0 of 14 runs are rescued when a second `</think>` is banned, and 2 without the ban.
      - The two rescues came after the model closed its renewed reasoning itself.
12. **N30: the council with our own back room on 150 fresh problems** [pre-registered publicly in v0.2; Section 3.11].
    - Rule: a majority of three answer-mode runs, otherwise WT-A with thinking. It solves **74 of 150**, against **66** for
      answer mode alone (H1 "holds") and **67** for MIT with thinking (H2 "at least level": +7, one-sided McNemar p = 0.105, so
      not "beats MIT").
    - As a delivery gate, agreement of two runs is right in **77 %** (H3 "open"), a majority of three in **66 %** (H4 "does not
      carry").
    - [descriptive, post hoc] Precision follows the strength of agreement: 85 % when all three runs agree, 50 % when two agree
      against one. The rule pays for its gain with tokens: 72,000 per correct answer, against 49,100 for MIT.
13. **The model's own readiness to commit does not track what it knows, in our model or in MIT's** [reading fixed in advance in
    the dated log; Section 3.12].
    - At value statements in the reasoning, the model's own probability of closing the reasoning (without the trigger) does not
      favour correct values: AUC **0.51** for our model, **0.43** for MIT's edit (below 0.5: slightly more often at wrong values).
      The probe separates them (0.68 and 0.73).
    - Behind MIT's own closing phrases, where the probe is strongest (0.85), MIT's closing tendency is still blind (0.38).
    - [interpretation] MIT's advantage does not come from closing at the right value.

---

## 1. Background

> *“Is the model simply unable to say ‘I don’t know’?”* — D. U., 7 Nov 2026
>
> This question led to the answer-forcing probe (Section 3.4) and to the honesty track (Sections 3.8 and 6).

On 2026-11-02, MIT CSAIL published *"Sparks of Weight-Space Programming"* (Takehi, Teoh, Zhang, Khattab).

- **What it shows:** in their Experiment 8, a general LLM edited Qwen3.5-0.8B directly in weight space.
- **The edit:** subtract one "loop" direction from 64 output columns of `mlp.down_proj` in layers 15 and 19, about 0.016 % of the weights.
- **The effect:** MATH-500 rose from 7.9 % to 48.1 %. The authors read this as *removing an obstacle that hid an ability*, not as adding one.

**Our questions:**
- Can the edit be reproduced and understood on consumer hardware?
- Can the "stop looping, start answering" behaviour be decomposed into measurable parts?
- Can it be steered more precisely, and at what cost?

**Closest prior work (position explicitly):**
- Zhang et al. (2025) show that reasoning models encode the correctness of intermediate answers in their hidden states. An *external* probe then supports early exit (up to 24 % fewer tokens at equal accuracy).
- Orgad et al. (2025) show the same "knows more than it shows" gap for hallucinations.
- More broadly, readable signals about the correctness of what a model says are well established (Kadavath et al., 2022; Azaria
  and Mitchell, 2023; Ferrando et al., 2024). Single directions in activation space can mediate whole behaviours (Arditi et al.,
  2024); MIT's edit and ours are of this kind.
- Our title echoes Li et al. (2026). For factual recall, they show that readouts taken before generation predict whether
  sampling will produce a correct answer, but say little about whether an available correct answer is finally selected; explicit
  verification with P(True) improves the ranking of the candidates. We study the related gap in reasoning models, where the
  correct value appears inside the thinking block long before the model commits to it.
- Our contribution is not the gap itself:
  - We dissect a published weight-space edit on consumer hardware. The sampling protocol accounts for half of its effect, and the
    loop direction can be found without a search agent.
  - We show that the bottleneck is committing, not knowing (truth probe, answer forcing, and in version 0.3 the model's own
    closing tendency, Section 3.12).
  - We write a truth-gated exit *into the weights*, with no external controller. Its mechanism is confirmed on fresh problems; its
    accuracy does not reach MIT's.
  - We measure *inside* why: a teacher-forced trigger audit (Section 3.9).
  - We report two failure modes of hand-written reflexes: the negative SiLU lobe, and a phase failure, where a forced close is not
    an inner close.
  - We show that the same frozen probe supports an honest "I don't know".
  - We report our strongest edit's failure to generalise: ERGORE matched MIT on 1–160, but not on fresh problems.

## 2. Setup

- **Model:** Qwen3.5-0.8B (hybrid Gated-DeltaNet / full attention, 24 layers), thinking mode.
- **Hardware:** one laptop GPU (8 GB) via llama.cpp (q8_0 GGUF). A second machine (CPU and iGPU) runs further evaluation blocks
  with identical model files (checked by checksum) and identical settings.
- **Protocol** (as in MIT's evaluation):
  - temperature 0.6, top-p 0.95, top-k 20, presence penalty 1.5;
  - up to 32,768 new tokens, seed 0;
  - the last `\boxed{}` is graded with math-verify.
- **vLLM-style sampling in llama.cpp:** repetition penalty over the whole answer; sampler order penalties → temperature → top-k → top-p → min-p.
- **Problem sets:**
  - MATH-500 problems 1–160 as test set;
  - MATH-500 161–300 as confirmation set; 301–370 as a second, late confirmation; 371–500 untouched;
  - MATH train problems as practice set;
  - "Set B": 60 fresh MATH train problems with the MATH-500 level mix, used as development set;
  - 150 further MATH train problems, never used before, for the publicly pre-registered test N30 (Section 3.11);
  - IFEval: 120 prompts, strict prompt-level scoring.
- **Pre-registration:** before each decisive run, the reading (criteria, thresholds) is written into a dated log. Later changes are logged with their reason, and only before the corresponding data exist.
- **Statistics:**
  - Most pre-registered readings are threshold rules ("holds / open / refuted"). Where a test also has a p-value (exact McNemar
    for paired accuracy, Fisher for rates), we report it unadjusted.
  - The three main effects with p-values remain significant after Holm correction over all ~40 pre-registered readings of this
    project (including the eight of N30 and N31 in version 0.3):
    - the trigger's closes after the correct value (H-WT2), p = 0.0001;
    - MIT's back room against its front room, p = 0.0003;
    - agreement of two intuitions, p ≈ 10⁻¹¹.
  - Descriptive results carry no p-value as evidence; we give counts and effect sizes.

## 3. Results

### 3.1 Sampling decides half of the effect [descriptive]

Same 40 MATH-500 problems, MIT's published edit:

| Setting | correct | stopped at token limit |
|---|---|---|
| MIT's reported run on these 40 | 47.5 % | ~33 % |
| our run, vLLM-style sampling | **55.0 %** | 30 % |
| our run, llama.cpp default sampling | **25.0 %** | 67.5 % |

- **Base model, vLLM-style:** 10 % correct, 92.5 % truncated.
- **Base → MIT edit:** 10 % → 55 %, with 20 problems rescued and 0 lost.

**Practical note:** anyone running repaired models in llama.cpp should set `repeat_last_n` to the full answer length and put temperature before the filters.

### 3.2 Our own loop direction [descriptive]

- **Construction:** the direction is the mean difference "repetitive minus productive" over base-model transcripts of 48 practice problems. The recipe is otherwise MIT's: layers 15 and 19, top-64 columns, α = 6.
- **Overlap with MIT:** cosine 0.76 and 0.77 to MIT's direction.
- **Result on the 40 problems:** 10 % → **37.5 %**, truncations 92.5 % → 60 %. Every problem ours solves, MIT's edit also solves. [interpretation] Same mechanism, weaker dose.
- **Knife-edge finder.** From points shortly before a loop starts, we let the base model branch 6–8 times (256 tokens each) and looked for "knife edges": points where some branches loop and others stay productive. We found 31 knife edges.
  - The share of looping branches grows the later the branch point lies (11 → 13 → 28 → 40 branches).
  - [interpretation] In the base model, loops build up gradually rather than tipping at a single point.
  - A direction built from the knife edges alone was noisy (cosine 0.77 to MIT's, low stability). Mixed with our direction it reached 0.79–0.80.

### 3.3 ERGORE: own direction plus an explicit closing coupling [pre-registered]

**Construction.** On layer 15 we add a second rank-1 term to the inversion. When the "loop detector" columns fire, it pushes along our own *commit axis*: "16 tokens before `</think>`" minus "middle of thinking". Its trigger is a whitened ("sharpened") detector. Layer 19 keeps the inversion only.

| MATH-500 | ERGORE | MIT | only ERGORE : only MIT | McNemar p | mean tokens ERGORE / MIT |
|---|---|---|---|---|---|
| 1–80 | 43/80 | 43/80 | 4 : 4 | 1.0 | 18,557 / 21,501 |
| 81–160 (fresh) | 36/80 | 34/80 | 10 : 8 | 0.81 | 18,489 / 21,248 |
| **1–160** | **79/160 (49.4 %)** | **77/160 (48.1 %)** | 14 : 12 | 0.85 | 18,523 / 21,374 |

- **Reading, fixed in advance:** "MIT level reached", on both halves. Not "above MIT": the 95 % CI of the difference is −5.0 to +7.5 points.
- **Tokens:** 13.3 % fewer overall (88 vs 55 problems cheaper, p = 0.007). There is no saving on problems both solve. The saving comes from problems neither solves, where ERGORE stops earlier.

### 3.4 Models know more than they act on

**Truth probe.** [pre-registered on test answers]
- **Construction:** logistic probe on layer-13 activations at the end of each candidate answer in the reasoning. Trained on practice data only, then frozen.
- **Practice data:** AUC 0.96.
- **Test final answers, applied once:** it flags **1 of 86** correct answers as unsure and catches **8 of 16** wrong ones.
- **Development set B:** AUC 0.925 on ERGORE runs and 0.966 on MIT runs. [descriptive]

**Hearing the bell is not enough.** [descriptive]

- **Setup:** 20 easy practice problems, our own-direction edit. The prompt adds "think for at most about 1,500 words, then give your final answer". Budget 6,144 tokens.
- **Result:** with this soft announcement, **0 of 20** runs finished within the budget (1 of 20 without it).
- **What the texts show:** **10 of 20** thinking texts write the constraint down themselves ("Constraints: … max ~1500 words …") and keep thinking anyway.
- [interpretation] The model does not lack the information that it should stop; it lacks the drive to stop. A soft instruction does not help. What helps is an inner push (a weight edit) or a hard external stop.

**The signal is a flash.** [descriptive] It peaks at the candidate end (AUC 0.96) and falls within a few tokens (0.67–0.80 at +8 to +200 tokens). The model closes its reasoning on average ~600 tokens after the last candidate.

**Late closing.** [descriptive, Set B] Tokens between the *first correct* candidate and `</think>` on solved problems (median):

| run | median tokens |
|---|---|
| ERGORE, T = 0.6 | 2,024 |
| ERGORE, T = 1.0 | 6,073 |
| MIT, T = 1.0 | 6,886 |

**Answer forcing.** [descriptive] Like budget forcing in s1, we append "The final answer is \boxed{" to every run that ended without a clean answer, identically for all models. Set B, 60 problems:

| | without forcing | with forcing |
|---|---|---|
| ERGORE, T = 0.6 | 34 | 38 |
| ERGORE, T = 1.0 | 21 | 29 |
| MIT, T = 1.0 | 24 | 32 |
| base-like variant ("Gatter"), T = 0.6 | 27 | 36 |
| base-like variant, T = 1.0 | 11 | 28 |

- With forcing, no pairwise difference between edits is significant. ERGORE vs MIT at T = 1.0: 29 vs 32, p = 0.38.
- [interpretation] Much of the measured difference between edits is about *getting the answer out*, not about *finding* it.

**Doubt without abstention.** [descriptive]
- Phrases such as "I'm not sure" or "let me guess" predict errors: with ERGORE at T = 1.0, only 3 of the 23 runs containing them are correct.
- Yet **49–85 % of wrong runs contain no doubt phrase at all.**
- **No run ever ends with an explicit abstention.** The probe, reading inside, classifies 96 % of wrong candidates as "not true" (4 % threshold).

### 3.5 Blunt pressure has a price

**IFEval harm check.** [pre-registered as a harm check] 120 identical prompts, same protocol:

| | IFEval (strict, prompt level) |
|---|---|
| base | 18/120 |
| own direction, no closing push | 74/120 |
| **ERGORE (with closing push)** | **61/120** (vs 74: 11 : 24, p = 0.041) |
| WT-A (truth-gated trigger) | 70/120 (vs 74: p = 0.54; vs ERGORE: p = 0.21; vs MIT: p = 0.005) [pre-registered reading: confirmed at ≥ 72, refuted at ≤ 64, so neither] |
| MIT edit | 87/120 |

- Losses concentrate in keyword instructions (11/38 vs 22/38) and combined instructions.
- [interpretation] The unconditional push makes the model hurry and drop required details.

**Empty commits.** [descriptive] Of ERGORE's 26 errors on Set B (T = 0.6), 22 are runs that close their reasoning, often without any candidate, and then ramble or loop in the answer part, e.g. "I will formulate the response. Final.". Forced to answer at that point, only 4 of 22 are correct, often with a placeholder "1". The model genuinely did not have the solution.

### 3.6 WT: a truth-gated trigger in the weights [descriptive on the development set; fresh-problem test pre-registered, Section 3.9]

**Construction.** 16 rarely active neurons in layer 15 are rewritten:

| weight | role |
|---|---|
| `gate` | truth direction above a high threshold (2 % of wrong candidates pass) |
| `up` | "a candidate just ended" detector |
| `down` | the **closing gradient** ĝ = ∂ log p(`</think>`)/∂h₁₅, averaged over correct candidate ends in practice runs |

ĝ is nearly orthogonal to the state-difference direction e⊥ of our first gate. A push of size 5 along ĝ raises p(`</think>`) from ~10⁻¹² to ~0.95.

**Offline check** on held-out practice prefixes, two bases (own direction only; ERGORE), thresholds 2 % and 4 %:

| position | without WT | with WT |
|---|---|---|
| correct candidate end | p(`</think>`) ≈ 10⁻¹², 0/8 | **≈ 1.0, 6/8** |
| wrong candidate end | ≈ 10⁻¹⁰, 0/8 | unchanged, 0/8 |
| ordinary token | ≈ 10⁻¹², 0/8 | unchanged, 0/8 |

**Real-generation test** [pre-registered]: Set B, n = 60, two machines in blocks, T = 0.6. WT-A is WT built with the sign rule
(Section 3.8) on top of our own loop direction.

| criterion (fixed in advance) | result |
|---|---|
| K0 mechanics: no immediate or candidate-free early closes | met (0 and 0) |
| K1 no harm vs. the same model without WT | met: 31 vs 23 correct (only WT-A 9, only without WT 1; p = 0.021) |
| K2 closes ≤ 64 tokens after a correct candidate | **not assessable**: 2 opportunities (see below) |
| K3 token savings on problems both solve | met: mean 5,248 vs 14,776 (−64 %) |
| K4 truth probe intact on the new transcripts | **not met**: AUC 0.82 / 0.94 vs 0.99 / 0.996 (two blocks) |

Following the reading fixed in advance, the gate to a confirmatory claim **stayed closed**. All later WT-A numbers are descriptive,
except H-WT2 (Section 3.9).
- **Why K2 could not be measured.** WT-A closes right after result sentences (`So $\binom{10}{8} = 45$.`), *before* the model writes
  `\boxed{…}` or "the answer is". Our old candidate detector looked only for those.
- **The fix.** We wrote a broader detector (old candidates plus value statements "= X", "is X"). With it we fixed a new test (H-WT2)
  before any run on fresh problems existed.
- **A second seed** reproduces the development-set result: 33 vs 25 (+8 again). [descriptive]

**Where the probe falls short.** [descriptive] Correct candidates below the threshold are mostly tentative mentions during a self-check. In the 60 tokens before them, check words appear in 51 % of cases (vs 21 % above the threshold), hedges in 29 % (vs 17 %). [interpretation] The model has not yet *asserted* the answer at that moment. Lowering the threshold catches some of these but adds misfires (simulation: 2 % → 4 % threshold, +13 correct fires, +6 misfires).

**Truth versus assertion (2 × 2).** [descriptive] Does the probe read *truth* or just a confident *form*? The gate is conservative
by design; this test asks *what* it reads, not *how often* it fires.
- **Setup:** On hard cases (correct candidates below the threshold, n = 38) we append one of four continuations: "So the answer is X." or "Let's check if it is X.", each with the true and with a wrong X. The probe is read at the end of X.
- **Wrong X:** a confident false assertion never crosses the threshold (**0 of 38**; upper 95 % bound ≈ 9 %).
- **True X:** a confident true assertion lifts **10 of 38 (26 %)** over the threshold.
- **Truth effect:** positive in 35 of 38 cases.
- [interpretation] The probe reads truth, not assertiveness. A clear statement of a true answer is a legitimate way to reach the bar without lowering it.

### 3.7 Negative results [pre-registered]

- **First gate (V2).** Same AND-structure as WT, but pushing along e⊥ and without ERGORE's closing push. It fails all three criteria:
  - Set B: 27 vs ERGORE 34 at T = 0.6, and 11 vs MIT 24 at T = 1.0;
  - empty commits 14 (target ≤ 6);
  - probe AUC 0.892 (target 0.93).
  - Without the closing push the model often never stops: 18 of 60 runs at T = 0.6, 44 of 60 at T = 1.0.
- **Tripling that push** changes nothing (28 vs 27).
- **Temperature.** With this model, T = 0.6 clearly beats the vendor-recommended T = 1.0 (ERGORE 34 vs 21 on Set B, p = 0.001).
- **Thinking switch** (decide before thinking whether to think at all).
  - **Hypothesis:** the inner signal at the end of the prompt (truth probe and candidate-end probe) predicts whether the model
    solves the problem *without* thinking, beyond difficulty level and prompt length.
  - **Result:** likelihood-ratio test p = 0.13, cross-validated AUC 0.72 → 0.73. **Refuted.**
- **ERGORE on fresh problems** (Section 3.9). "MIT level not reached" on 161–300.

### 3.8 A recipe: programmed reflexes in quiet neurons [method; transfer to other models untested]

The MIT edit *removes an obstacle*: it reverses one loop direction. WT goes one step further and *writes a conditional reflex* into the weights: **if a condition holds in a given context, push towards an action.** All three parts are measured from the model itself; nothing is trained.

**The formula.** For K rarely active SwiGLU neurons G in one mid-depth layer, with x the input of that layer's MLP:

> **reflex = effector × (condition ∧ context)**
>
> Δh(x) = K · κ_d · SiLU( κ_g · (s_cond(x) − τ) ) · κ_u · (s_ctx(x) − τ′) · **e**

| part | what it is | in WT |
|---|---|---|
| condition s_cond | linear probe on x | "this value is true" (truth probe s_T) |
| context s_ctx | second linear probe on x | "a result just ended" (candidate-end probe s_C) |
| effector **e** | unit direction that triggers the action: the mean normalized gradient ∂ log p(action token)/∂h at the places where the action is wanted | "write `</think>`" |
| place | the K quietest neurons by activation RMS, outside other edits | 16 neurons in layer 15 of 24 |

**Writing it into the weights.** SwiGLU already contains the multiplication, so the AND needs no runtime hook:
- `gate[G] = κ_g · (w_cond + (b_cond − τ) · v)`
- `up[G] = κ_u · (w_ctx + (b_ctx − τ′) · v)`
- `down[:, G] = κ_d · e`

The vector v emulates the missing bias (vᵀx ≈ 1 on ordinary tokens).

**Calibration rules, all fixed before testing:**
- τ lets only a small share of wrong candidates through (2 %).
- κ_g brings the median correct candidate to a gate value z* = 3.
- **τ′ is the median of s_ctx on ordinary tokens.** This is the sign rule: SiLU is negative between about −4 and 0, so the context term must not be negative wherever the gate sits in that region. Otherwise the product turns positive and the reflex fires where it should not. Our first build (V2.1) broke this rule; see the leak below.
- κ_u scales a typical candidate end to 1.
- κ_d = κ / (K · SiLU(z*)) gives a total push of κ = 7 units along e at a typical firing position.

**Mandatory offline checks.** Measure p(action token) for the edited and the base model on identical texts:

| position | must |
|---|---|
| correct candidate end | fire |
| wrong candidate end, ordinary token | stay at base level |
| last prompt token (first generated token) | stay at base level |
| early paragraph ends | stay at base level |
| sentence end after a refuted check | stay at base level |
| intermediate result (≠ final answer) | stay at base level |
| answer part (after the action) | stay at base level |

The first build passed the first three rows on thinking positions but leaked at the prompt end: 9–10 of 30 runs closed at once (Section 3.6). That is why the list has seven rows. WT-A passes all thinking-side rows; it still fires in the answer part (second `</think>`, see the lesson below).

**Evaluation protocol:**
- block design across machines;
- criteria fixed in advance (mechanics, no harm, effect, savings, probe intact);
- confirmation only on untouched problems;
- answer forcing and an instruction-following check (IFEval) as side conditions.

**Transfer to another SwiGLU model, in six steps:**
1. Train the two probes on the model's own residual stream at a mid-depth MLP input.
2. Measure the effector gradient at the desired action points.
3. Select the quiet neurons.
4. Write the three weight blocks.
5. Pass all mandatory checks, including the sign rule.
6. Evaluate with a reading fixed in advance.

All scripts are in the released code. Whether the recipe carries over to larger models is the question of Phase 2.

**Lesson from WT-A** [descriptive]: the effector must fit the *phase*, and it must leave a *state*, not just a token.
- After a trigger close, WT-A reopens its reasoning in the answer part (a second `</think>`) in 83–100 % of runs, even when the
  value had been stated six or more times before. This produced 46 % of all tokens on the development set.
  - On fresh problems (161–300) the figure is 77 % of all closes and 58 of 61 correct runs; MIT reopens after 16 % of its closes.
  - WT-A's correct answers almost always come after its *own* second close.
- [interpretation] The gradient effector ĝ raises `</think>` for exactly one step. One token later the candidate-end context is
  gone and the 16 neurons fall silent. The attention layers then see a reasoning that was cut off mid-check, and the model treats
  the close as foreign.
- A fix therefore needs an effector with *depth of effect*: a push that starts the model's own way of finishing instead of
  forcing a single token. One candidate is the part of MIT's direction that our own does not explain (r⊥). Its top tokens are
  natural ending words ("thereby", "accordingly", end-of-text), and it is orthogonal to ĝ (cosine 0.005).
- The pre-test of depth of effect (Section 3.9) found no such effector yet. A single push along ĝ or r⊥ acts only while it is
  applied, and spreading it over three steps leads to *more* renewed thinking. The reviewers' proposals therefore aim at
  accompanying the model's own closing phrase (Section 6).

**A second instance (proposal).** The same formula can express an honesty reflex:
- condition: "the truth probe stays low";
- context: "about to commit";
- effector: towards an abstention phrase ("I don't know").

**Honesty step 1** tests only the condition, as an external rule. [pre-registered]
- **Setup:** The frozen layer-13 truth probe is read at the *delivered* answer. If it stays below its frozen threshold, the
  answer is replaced by "I don't know". Runs without an answer are first forced to answer.
- **Data:** 1,280 runs from all sets and models.

| | correct | wrong | abstained | score S₂ = (correct − 2·wrong)/N |
|---|---|---|---|---|
| official answers | 592 | – | – | +0.20 |
| forced answers | 726 | 552 | – | −0.30 |
| **forced + probe abstention** | 673 | 225 | 380 | **+0.17** |

- **Both criteria met:** AUC on forced answers 0.83 (required ≥ 0.75), and the harness beats forcing on S₂.
- 327 of the 380 abstentions would have been wrong; 53 correct answers were lost.
- **Risk–coverage:** answering only the 50 % most confident gives 87 % accuracy, the 30 % most confident give 95 %.
- On the fresh problems alone: AUC 0.83 (forced answers 0.80), S₂ +0.13 with the harness vs −0.24 forced.
- [interpretation] The inner truth signal does not only trigger commitment; it also tells when *not* to commit. Writing the
  abstention itself into the weights is the next step.

### 3.9 Fresh problems: MATH-500 161–300

> *“A teacher does not give the candidate a push from outside either.”* — D. U., 8 Nov 2026

**Design.**
- Problems 161–300 were untouched until this step.
- The laptop ran 161–260, the second machine 261–300. Every pairwise comparison runs on the same machine.
- Same protocol for all models, seed 0; a second seed for parts of the data.

**Main verdict** [pre-registered]. ERGORE does not reach MIT level: 65 vs 80 of 140 (7 : 22, p = 0.008).

| block | ERGORE | MIT | note |
|---|---|---|---|
| 161–260 (laptop) | 51 | 58 | seed 0 |
| 261–300 (second machine), seed 0 | 14 | 22 | 3 : 11 |
| 261–300, seed 1 [descriptive] | 16 | 16 | 6 : 6 |

[interpretation] The development-range tie did not transfer. On one block, MIT's own seed-to-seed variation (22 → 16) is as large
as the gap. The gap is real, but probably closer to 5–7 points than to 11.

**WT-A on fresh problems.**

| | WT-A seed 0 | WT-A seed 1 (161–260 only) | MIT |
|---|---|---|---|
| correct [descriptive] | 61/140 (161–260: 44/100) | 47/100 | 80/140 (161–260: 58/100) |
| **H-WT2: closes ≤ 64 tokens after the correct value, per opportunity** [pre-registered] | **65 % (55/85)** | 54 % | 36 % (37/102), p = 0.0001 |
| **H-WT2: fast closes that are right** [pre-registered] | **61 % (55/90)** | 57 % | 44 % (37/85) |
| tokens on problems both solve | 7,146 | – | 13,233 |

**Inside view: a teacher-forced trigger audit** [descriptive; readings fixed in advance]. We replayed all 140 WT-A transcripts
with and without the 16 neurons, reading the gate, the context term, the push and the sampled close probability at every position.
- **The trigger carries WT-A's successes.**
  - 69 of 102 first closes are trigger-driven: the sampled close probability is < 2 % without the neurons and ≥ 20 % with them.
  - 46 of these 69 follow the correct value, 18 a wrong one, 5 elsewhere. They yield **51 of WT-A's 61 correct answers**.
  - WT-A's natural closes (25) are mostly at wrong values; only 5 are correct.
- **Truth recognition is partial.** The gate opens at 17 % of correct and 6 % of wrong value statements (AUC of the gate value
  0.68). Mostly it stays just above threshold, too weak for a full trigger.
- **The counter-push of the negative SiLU lobe is small:** 1.7 closes lost across 140 runs.
- **A relative threshold does not help** [exploratory]. A within-run z-score of the gate value separates worse (AUC 0.61).

**Where the gap comes from** [descriptive, post hoc]:

| | WT-A | MIT |
|---|---|---|
| correct value appears in the reasoning | 85 | 102 |
| … closes right at it | 55 → 48 delivered correctly | 37 → 33 |
| … does not close right at it | 30 → **7** correct | 65 → **44** correct |
| tokens from first correct value to close (median) | 1,018 | 12,289 |

- **When the trigger fires:** on early, clearly stated solutions of easier problems.
  - First correct value at a median of 719 vs 1,963 tokens.
  - Levels 1–3: 75 % of these runs close at the value; levels 4–5: 50 %.
- **Silence is often a delivery failure.** 32 WT-A runs close the reasoning without a `\boxed` answer. In 14 of them, the correct
  value appears early in the answer part and is then lost.
  - How often does WT-A reopen its reasoning after a close (a second `</think>`)? It depends on which runs are counted:
    - in 83–100 % of the development runs;
    - in 77 % of all its closes on these fresh problems (58 of its 61 correct runs);
    - in 12 of these 32 silent runs.
  - MIT reopens after 16 % of its closes.
- **The truth signal fades with loops and difficulty, not with depth.** We fit a logistic regression on the correct ones among
  109,561 value statements from WT-A and MIT transcripts (same probe, same layer-15 input), standardised, with a run-level bootstrap.

  | factor | coefficient for "gate open" at correct values | 95 % interval |
  |---|---|---|
  | depth (log tokens) | **+0.26** | +0.01 to +0.49 |
  | local repetition | **−0.80** | −1.08 to −0.50 |
  | difficulty level | **−0.68** | −1.06 to −0.32 |

  - Nested models without the bootstrap show the same reversal. Depth alone gives −0.49, adding difficulty −0.27, adding loops
    +0.46, adding the transcript source +0.26. The last step is the full model of the table.

  - Without loops, the gate still opens at ~60 % of correct statements at 8,000–16,000 tokens. Inside loops beyond 16,000 tokens it
    opens at 15 %.
  - [interpretation] The probe reads the state of the reasoning, not the distance from its start. A depth-dependent threshold is
    not indicated.
- **The trigger would not help MIT.** [estimate, not a measurement] We replayed MIT's transcripts with the trigger neurons added.
  - The trigger would cut MIT's long check short, often at a wrong value.
  - The estimate stays below MIT's actual score under all threshold settings. Waiting for repeated triggers on the same value comes
    close, but does not exceed it.
  - The estimate depends on assumptions about delivery after an early close, so we report it only as a reason for not running
    this combination.
  - [interpretation] A truth-gated trigger pays off where a model has no good way to finish on its own (WT-A vs its base: +8 in
    both seeds). It does not pay off where the model already delivers well by other means.
  - *Corrected in version 0.3.* Version 0.2 ended the last sentence with "where the model already checks and commits well".
    Section 3.12 shows that MIT's own readiness to commit is no more tied to the truth of a value than ours. Its advantage lies in
    finding the correct value more often (102 vs 85 runs) and in delivering after long checking (44 of the 65 runs that do not
    close right at the value; table above).
- **Depth of effect** [pre-test, readings fixed in advance; 30 trigger closes at correct values, greedy decoding].

  | push at the trigger point | closes | p(`</think>`) when closing is blocked, steps 0 / 1 / 2 / 5 | closing sentence before | re-thinking after |
  |---|---|---|---|---|
  | WT-A's real trigger | 26/30 | 0.75 / 0.27 / 0.03 / 0 | 0 | 4 |
  | none (base edit) | 0/30 | 0 | – | – |
  | ĝ once (κ = 7) | 30/30 | 1.00 / 0.02 / 0 / 0 | 0 | 4 |
  | ±r⊥ once (κ = 7) | 0/30 | 0 | – | – |
  | ĝ spread over 3 steps | 17/30 | 0.01 / 0.36 / 0.32 / 0 | 0 | 11 |

  - Every push acts exactly as long as it is applied; no lasting "done" state forms. No variant produces a closing sentence.
  - A single push along r⊥ does nothing. MIT's closing phrases therefore come from an edit that acts continuously, not from a
    kick.
  - [interpretation] An inner "done" has to build up along the closing stretch. The next candidate fires *while* the model writes
    its own closing phrase, and only when the truth signal is high. At exactly those points the probe separates right from wrong
    values with AUC 0.80–0.85.

### 3.10 Answer mode ("INT")

> *“That is the first pair of shoes. Let us call it INT, for intuition.”* — D. U., 8 Nov 2026

Qwen3.5's official non-thinking template closes the thinking block before generation starts. The model then reasons visibly in its
answer, with an obligation to deliver and no separate place for unbounded checking. Ma et al. (2025) report that skipping the
thinking block can be competitive under token budgets. Here it happens in an edited 0.8B model at MIT's full protocol.
- **Development range** [descriptive]: our own-direction model, without thinking block, same protocol and budget.
  - MATH-500 1–160: **77 of 160**, exactly as many as MIT with thinking (22 : 22). It uses ~8,200 instead of ~21,000 tokens.
  - Set B: 32 vs 23 for the same model with thinking (14 : 5, p = 0.064).
  - All 109 answer-mode hits end regularly (end-of-turn). None comes from a loop or budget cut-off, so this is not a grading
    artefact.
- **Is answer mode only good for easy problems?** [descriptive, development data] No.
  - By official difficulty (1–160): answer mode 26 vs MIT-with-thinking 22 on levels 4–5, and 33 vs 37 on levels 1–2.
  - Same model in both modes (Set B, two seeds for thinking): on problems the model answers quickly (< 1,000 tokens), answer mode
    gets 21 and thinking 19 and 19 of 26.
  - On problems where the answer takes long (> 8,000 tokens), answer mode gets 8, thinking 2 and 3 of 25.
  - The author's image for this is a house. The answer mode is the *front room*; the thinking block is the *back room*; between
    them lies a *hallway* whose exits lead to "closing time" (deliver and stop) or to the "break room" (pause, abstain, retry).
  - [interpretation] For this 0.8B model, the back room is not where hard problems get solved; it is where the model gets lost.
  - Answer mode also shows its own speed signal: answers within 1,000 tokens are right ~75 % of the time, answers beyond 8,000
    tokens ~25 %.
- **Fresh problems 161–300** [pre-registered: holds if ≥ MIT − 7 of 140, refuted if ≤ MIT − 14]: answer mode **71**, MIT with
  thinking **80**. The result is **open**.
  - On 161–260, 57 vs 58; on 261–300, 14 vs 22.
  - All answer-mode runs end regularly. Per correct answer they need 14,800 instead of 36,600 tokens (161–260).
- **MIT in the front room** [pre-registered]: MIT's edit without thinking block reaches **59 of 140** (6 : 27 against MIT with
  thinking, p = 0.0003). The reading "the back room pays off for MIT" holds.
  - Our front room (71) beats MIT's front room (14 : 26, p = 0.08).
  - [interpretation] A back room is worth entering only when it has a working exit. MIT's edit builds that exit; ours builds a
    stronger front room.
- **Checks** [pre-registered]:
  - Presence penalty: the answer-mode advantage on Set B 1–20 is +2 both with penalty 0 and with 1.5. No artefact.
  - Day-to-day stability: with a second seed on 261–300, answer mode goes from 14 to 16, but only 75 % of problems are solved
    the same way. MIT with thinking also reaches 75 %. The author's guess that the front room is more stable is refuted.
- **Cascade "answer mode → truth probe → thinking run → I don't know"** [pre-registered; precondition not met, so descriptive].
  - **Precondition:** the frozen truth probe must separate answer-mode answers on 161–300 with AUC ≥ 0.75. It reaches 0.68
    (0.76 on 1–160). The cascade is therefore reported only descriptively.
  - **Main variant:** thresholds calibrated on 1–160, MIT as fallback. On 161–300 it reaches S₂ +0.32 against +0.27 for MIT
    alone, but with only 67 correct answers (MIT: 80). The reading required S₂ ≥ +0.25 *and* at least 75 correct answers, and it
    counted as refuted at S₂ ≤ +0.19 *or* fewer than 75 correct. It is therefore **refuted** despite the higher S₂.
  - **Cost:** tokens rise rather than fall, because most problems end up in the thinking branch.
  - **Reason:** in answer mode the probe is shifted far upwards. Correct answers have a median score of +3.4, wrong ones +1.9 to
    +2.6, against a frozen threshold of −1.2.
  - [interpretation] The probe was trained on thinking text. In the front room every statement sounds assertive. A front-room
    cascade needs a probe trained on answer text.
- **Second chance ("dawn")** [pre-registered]. The 69 WT-A runs that delivered nothing were retried in answer mode with notes. The
  notes were the sentences around the model's own strongest truth flashes, chosen without access to the solution. The control was
  answer mode without notes on the same problems.
  - Notes 22, control 25 (p = 0.66). The effect of the notes is **refuted**.
  - [descriptive] The second chance in the front room itself rescues a third of the silent runs; WT-A had delivered nothing on
    them.
  - Notes help only when they contain the correct value (8 vs 5 of 10). The strongest truth flashes point to the correct value in
    only 10 of 65 runs.
- **Crossing out** [descriptive, rough marker]. In the back room, correct values are retracted ("wait", "let me check", …) *more*
  often than wrong ones: WT-A 74 % vs 60 %, MIT 59 % vs 45 %. The truth signal is the same whether a value is retracted or kept.
  In the front room, retraction is rare (18 % vs 14 %).
  - [interpretation] Retraction in the back room is a habit, not a judgement about truth.
- **Signposts** [descriptive]. Before MIT's natural closes the model writes its own closing phrases ("answer" 31 %, "final" 14 %,
  "ready" 8 % in the last 12 tokens). Before WT-A's trigger closes these are mostly missing.
- **Quick errors are not blind** [descriptive; corrects an earlier reading]. Among quick answer-mode answers (< 1,000 tokens), none
  of our *earlier* signals separates right from wrong: retractions, doubt words, distinct values and the thinking-text probe give
  AUC 0.48–0.54. We first called these "confident errors". A probe trained on answer text does separate them (next item).

> *“Several intuitions confer in the front room. If they agree, it is closing time. Only the disputed cases go to the back
> room.”* — image agreed with D. U., 8 Nov 2026

- **Asking the intuition twice** [pre-registered]. The same model in answer mode, seeds 0 and 1. Rule: "same answer" when
  both runs deliver equivalent answers (checked as in grading).
  - **161–260** (100 fresh problems): same answer on 38 problems, **37 right (97 %)**; different answers on 62, seed 0 right in
    32 %. The criterion (difference ≥ 30 points and ≥ 70 % when agreeing) holds with +65 points. Fisher one-sided
    p ≈ 9 · 10⁻¹².
  - **40 new training problems** (never used before): same answer on 17, 13 right (76 %); different on 23, 13 % right. The criterion
    holds with +63 points, but at clearly lower precision.
  - **Untouched problems 301–370**: same answer on 31, **28 right (90 %)**; different on 39, 18 % right. The criterion holds with +72
    points.
  - [descriptive, pooled] Over the three confirmations, 78 of 86 agreeing answers are right (91 %). The 97 % of the first test is the
    upper end. Each set was pre-registered on its own; the pooled figure was not.
  - *Added in version 0.3:* a fourth test, pre-registered publicly, gave **77 %** on 150 fresh problems (51 of 66; Section 3.11).
    Over all four sets, 129 of 152 agreeing answers are right (85 %) [descriptive, pooled].
  - [interpretation] This is self-consistency (Wang et al., 2022) used at the point of commitment. Agreement does not vote on the
    answer; it decides *whether* to deliver.
  - Agreement across independent answer-mode runs is closely related to semantic entropy (Farquhar et al., 2024), which detects
    confabulations by sampling several answers and measuring their uncertainty at the level of meaning. Our council applies a
    simple form of this principle, agreement of the final answers, as a delivery gate for a small reasoning model.
  - [descriptive] On the already seen block 261–300 the same pattern appears: 10 of 12 vs 4 of 28.
- **Asking three times** [pre-registered; 161–260, seeds 0, 1, 2].
  - A majority of three (at least two equivalent answers) delivers on **62** problems, 55 of them right (89 %).
  - The reading required ≥ 48 deliveries and ≥ 90 % precision, so it is **open** by one point.
  - The second reading, that the net score (correct − 2·wrong)/N must not fall below agreement of two, holds: +0.41 vs +0.35.
  - All three agree on 29 problems, and all 29 are right.
  - [descriptive] The other seed pairs repeat the pattern: 0/2 agree on 42 problems (40 right), 1/2 on 40 (35 right).
- **A probe for the front room** [pre-registered; result "open"]. Same recipe as the truth probe, but trained on answer-mode
  texts: 239 delivered answers from Set B and 1–160. It reads the state at the last token of the delivered `\boxed{}`.
  - Layer and regularisation were chosen by grouped cross-validation on training data only (layer 13, CV AUC 0.81), then frozen.
  - Test on 161–300: AUC **0.763**. Answer length and difficulty alone reach 0.723, and the combination adds only +0.04. The
    reading fixed in advance required +0.05, so the result is **open**.
  - The thinking-text probe reaches 0.681 at the same positions.
  - [descriptive, post-hoc subsets] On quick answers (≤ 2,000 tokens) the new probe reaches 0.794, against 0.63 for length and
    difficulty and 0.63 for the old probe. Delivering only quick answers above the probe's median gives 26 of 29 right.
  - It transfers to MIT's answer-mode texts (0.776) and to new samples of the same problems (0.836).
  - **Confirmations** [pre-registered, frozen probe and frozen baseline]:

    | set | answers | probe AUC | length + difficulty | gain | quick answers (≤ 2,000): probe vs baseline |
    |---|---|---|---|---|---|
    | 40 new training problems | 79 | 0.852 | 0.841 | +0.012 | 0.823 vs 0.736 |
    | untouched 301–370 | 138 | 0.765 | 0.717 | +0.048 | 0.606 vs 0.599 |

    - Both main readings are **open**: the probe reads correctness well, but answer length and difficulty already carry most of
      that information.
    - The quick-answer advantage from the post-hoc subset **did not replicate** on the untouched problems. It was fixed in advance
      as a second reading, and that reading is refuted.
  - **Added value without harm** (author's criterion: "only if it adds value and does no harm, measurably") [pre-registered,
    301–370]:
    - *As referee*: when two intuitions disagree and both deliver an answer, take the one with the higher probe score. On 37 such
      problems, one of the two answers was right in 18. The probe picks 11 of them; the first run alone has 7, the shorter answer
      7. Reading: **added value**.
      - It is a fragile sample: only 18 problems decide, and the paired bootstrap 95 % interval for the gain is −1 to +10 correct
        answers.
      - [descriptive] Under "always answer", the referee raises the count from 35 to 39 of 70. The two single runs score 35 and
        39, so the mean of a single run is 37.
    - *As an extra delivery gate*: the score falls from +0.31 (agreement alone) to +0.13. Reading: **harm**. The probe's extra
      deliveries are right in only 3 of 11 cases.
    - [interpretation] Agreement decides *whether* to deliver; the probe decides *which* answer when the intuitions disagree.
- **Switching rooms** [pre-registered]. Deliver when two intuitions agree, otherwise use a thinking run.
  - With WT-A's back room as fallback: 54 of 100, against 57 for answer mode alone. Refuted.
  - [descriptive] With MIT's back room: 63, against 57 and 58 for each alone.
  - [descriptive] With three intuitions (majority, otherwise back room): WT-A's back room as fallback gives **62**, against 57 for
    answer mode alone and 44 for WT-A alone. MIT's back room gives 66, against 58 for MIT alone. With three intuitions our own
    back room adds value for the first time.
  - [descriptive, 161–300] "Agreement alone" as the rule for delivering, otherwise "I don't know": 50 of 140 delivered, 94 %
    right, score (correct − 2·wrong)/N of +0.29 against −0.48 for always answering.
  - [descriptive, 161–300] The gain of "agree → answer mode, otherwise MIT" (84 vs 80) comes entirely from the agreeing set (47 vs
    43 there). The rule is a selector, not an amplifier, and two full answer-mode runs make it costlier in tokens (54,000 vs
    37,700 per correct answer).
  - [pre-registered, 301–370] With the probe as an extra gate, the coupled rule beats a length-only rule only by +0.04 in score, at
    74 % precision (required: +0.05 and 80 %). The result is **open**.
  - **"Agree → answer mode, otherwise MIT's back room" on the untouched problems 301–370** [pre-registered]. The rule holds if
    it reaches at least MIT alone, with ≥ 90 % precision on the agreeing set and fewer tokens per correct answer than MIT.
    - Result: **40 of 70**, against 38 for MIT alone and 35 for answer mode alone. Precision on the agreeing set is 90 % (28 of 31).
    - The token criterion fails: 56,800 vs 41,000 per correct answer. The reading is therefore **open**.
    - Decomposition: on the 31 agreeing problems, answer mode has 28 and MIT 26. On the other 39, MIT has 12 and answer mode 7. The
      gain comes from both rooms: precision in front, MIT's exit at the back.
    - [descriptive] On these problems answer mode alone (35) stays close to MIT with thinking (38), at 17,000 vs 41,000 tokens per
      correct answer.
- **Closing at one's own signpost** [WT-A pre-registered, MIT descriptive]. We cut reasoning texts right after a value that
  follows the model's own closing phrase ("the answer is …"), inserted `</think>` and regenerated the answer part. The control was
  a value without such a phrase in the same run.
  - MIT (74 runs, 1,024-token cap): it delivers in 36 % of cases at its signpost and in 18 % at the control (17 : 3,
    p ≈ 0.003). All 19 deliveries after a correct value are right.
  - WT-A (19 runs) first gave 0 and 0, but with a 1,024-token cap that was too short for WT-A. Its natural correct answer parts
    have a median of ~2,000 tokens.
  - In the fair re-test with 4,096 tokens [pre-registered]:
    - WT-A delivers in 32 % at its signpost and in 21 % at the control (3 : 1). The result is open.
    - Where its own signpost *and* the truth gate coincide, it delivers in 5 of 9 cases, all of them right.
    - Over all runs, a reflex built on this would not gain anything: 59 instead of 61. It also cuts runs that would later have
      delivered correctly on their own.
  - The same re-test confirms the replay of WT-A's 32 silent answer parts: even with 4,096 tokens, only 2 of 32 deliver.
  - [interpretation] The model's own signposts, together with the truth signal, mark the moments where a close holds. An inserted
    `</think>` still does not replace an inner "finished".

### 3.11 N30: a council with our own back room on 150 fresh problems [pre-registered]

*New in version 0.3.* We fixed this test publicly in v0.2 (Section 6 there; log entry of 8 Nov, 18:43), before any of its runs
existed.
- **Problems:** 150 MATH training problems that had never been used, with the level mix of MATH-500 (13 / 27 / 32 / 38 / 40),
  drawn with seed 202611082.
- **Runs**, all with the same protocol (T = 0.6, 32K tokens, vLLM-style sampling, presence penalty 1.5):
  - answer mode of our own-direction model, seeds 0, 1 and 2;
  - WT-A and MIT with thinking, seed 0.
- **Rule B+H** (council plus our own back room): if at least two of the three intuitions give equivalent answers (math-verify in
  both directions), deliver that answer; otherwise take WT-A's thinking answer.

| | Reading, fixed in advance | Result | Verdict |
|---|---|---|---|
| H1 | B+H against answer mode alone (seed 0): "holds" at ≥ +5, "refuted" at ≤ +1, otherwise "open" | 74 vs 66 (+8) | **holds** |
| H2 | B+H against MIT, paired: "beats MIT" at ≥ +5 with one-sided McNemar p < 0.05; "at least level" at ≥ 0; "below MIT" at ≤ −5; otherwise "open" | 74 vs 67 (+7); only B+H right on 15, only MIT on 8; p = 0.105 | **at least level** |
| H3 | Agreement of two intuitions (seeds 0 and 1): "holds" at ≥ 85 % precision, "refuted" below 75 % | 66 agree, 51 right (77 %) | **open** |
| H4 | Majority of three: "carries" at ≥ 85 % precision with ≥ 10 points more coverage than agreement of two; "does not carry" below 80 % | 101 deliveries (coverage 67 % vs 44 %), 67 right (66 %) | **does not carry** |

- **Correct of 150** [descriptive]: B+H 74; answer mode 66 (seed 0; seeds 1 and 2: 68 and 60); MIT with thinking 67; WT-A with
  thinking 59; the same majority with MIT as back room 75.
- **Tokens per correct answer** [descriptive]: B+H 72,001; answer mode 19,898; MIT 49,089; WT-A 50,593. For B+H we count all three
  answer-mode runs and WT-A only where no majority exists.
- **Ending on their own** [descriptive]: answer mode ends regularly in 99 % of its runs (loop or budget cut-off: 1 %), MIT with
  thinking in 55 % (45 %), WT-A in 47 % (53 %).
- The probe as referee, listed as descriptive in the reading, is not evaluated in this version.

**Where the result comes from** [descriptive, post hoc; computed after the verdicts]. We split the problems by how strongly the
three intuitions agree:

| the three intuitions | problems | B+H correct | answer mode alone (seed 0) | MIT with thinking |
|---|---|---|---|---|
| all three agree | 47 | 40 (85 %) | 40 | 37 |
| two agree against one | 54 | 27 (50 %) | 21 | 22 |
| no majority (WT-A decides) | 49 | 7 (14 %) | 5 | 8 |
| total | 150 | 74 | 66 | 67 |

- **Why H1 holds:** where the votes split, the majority is right more often than the single run (27 vs 21), and the back room adds
  two more (7 vs 5).
- **Why H3 and H4 do not:** a split vote is right only half the time. Of the 66 problems on which seeds 0 and 1 agree, 47 are
  unanimous (40 right) and 19 have a dissenting third run (11 right).
- **Against MIT**, B+H gains in the front room (+3 where all three agree, +5 where the votes split); in the back room MIT is
  slightly ahead (8 vs 7).

**What it means** [interpretation].
- As a council, the rule carries: on fresh problems it solves more than any single run, without MIT's model. It does not beat MIT
  by the standard fixed in advance; 15 against 8 discordant problems is not enough at n = 150.
- As a delivery gate, agreement of two was less reliable here than in the three earlier sets (77 % against 91 % pooled). Only
  unanimity of three reached 85 %. The information lies in the strength of agreement, not in agreement as such.
- The gain costs tokens: about 1.5 times MIT's tokens per correct answer, because three intuitions always run, and the back room
  solves only 7 of the 49 problems without a majority.
- Why the precision fell is open. Chance is possible: 51 of 66 is compatible with roughly 66–86 % (Wilson 95 % interval). So is the
  problem source: the only earlier confirmation set drawn from the MATH training set gave 76 % (13 of 17), the two MATH-500 sets
  97 % and 90 %.

### 3.12 N31: does the model's own readiness to commit track what it knows? [reading fixed in advance in the dated log]

*New in version 0.3.* This section asks the question of the title directly. It uses data that already existed: the teacher-forced
trigger audit of Section 3.9, that is WT-A's and MIT's transcripts of problems 161–300 (seed 0, 140 runs each). The reading was
fixed in the dated log on the evening of 8 Nov, before the analysis ran, and amended twice before the analysis (below). Unlike N30,
it was not published in advance.

- **Unit:** every value statement in the reasoning whose correctness is known: 43,848 for our model (2,468 correct) and 65,713 for
  MIT (4,262 correct).
- **Knowing (K):** the frozen truth probe's reading at the value.
- **Committing (F):** the model's own probability of closing the reasoning (`</think>`) right after the value, read with the 16
  trigger neurons silenced, that is without the reflex.
- **Measure:** the AUC of F for correct against wrong values. At 0.5 the closing tendency is blind to truth; at 1.0 the model would
  tend to close only at correct values. The 95 % intervals come from a bootstrap over runs (10,000 draws).
- **Models:** "our model" is WT-A with its trigger neurons silenced, read on WT-A's transcripts. "MIT" is MIT's edit, read on its
  own transcripts with the trigger neurons added and silenced. Both are approximations (limits below).

| | Reading, fixed in advance | Result (95 % interval) | Verdict |
|---|---|---|---|
| H6a, our model | "blind (confirmed)" at AUC < 0.60; "coupled (refuted)" at ≥ 0.70; otherwise "open" | 0.51 (0.46–0.57) | **blind** |
| H6b, MIT | "couples to truth" at ≥ 0.70; "also decoupled" at < 0.60; otherwise "open" | 0.43 (0.39–0.46) | **also decoupled** |
| H6c, MIT minus our model | "MIT couples more strongly" at ≥ +0.10 with an interval above 0; "our model couples more strongly" at ≤ −0.10 with an interval below 0; "no difference detectable" if the interval contains 0; other cases "open" | −0.085 (−0.150 to −0.026) | **open** (a case not named in advance) |
| behind the model's own closing phrases (added before the analysis) | "couples at the signpost" at ≥ 0.70; "blind at the signpost" at < 0.60; otherwise "open" | our model 0.69 (0.45–0.78); MIT 0.38 (0.27–0.52) | our model **open**; MIT **blind** |

- **For comparison** [descriptive]: the probe separates the same values with AUC 0.68 (our model) and 0.73 (MIT), and behind the
  closing phrases with 0.80 and 0.85.
- With the probability the model actually sampled from (trigger included), F reaches 0.50 for both models.
- F does not couple at any depth of the reasoning (five depth bands: our model 0.46–0.53, MIT 0.41–0.50).

**Reading amended twice before the analysis.**
- The first version of H6a also required the probe to reach AUC ≥ 0.75 on these statements. The audit had already shown 0.68 and
  0.73 on exactly these statements, so H6a could never have been confirmed for our model. An external reviewer (WREN) found this
  flaw. H6a was then reduced to F alone, and the measurement behind the closing phrases was added.
- WREN then rebuilt the analysis independently on toy data, without access to ours. After that, the mirrored case of H6c ("our
  model couples more strongly") was named, and bootstrap draws that lack one class are counted (there were none).
- Both amendments were logged with new checksums before the analysis ran.

**What it means** [interpretation].
- Knowing is not committing, now at the level of internal signals: the probe can read whether a value is correct, but the model's
  own readiness to stop thinking does not follow it. This holds for our model and for MIT's edit.
- MIT's edit is not better at closing at the right value. Its closing tendency even leans slightly towards wrong values (0.43).
  This fits a count from the log: MIT's natural closes fall at a wrong value 48 times and at a correct one 37 times
  [descriptive]. Its advantage lies elsewhere (Section 3.9, corrected interpretation).
- Behind its own closing phrases the probe is strongest, and yet MIT's closing tendency stays blind there. This is where a
  truth-gated close could help most (Section 6).
- It also explains why the council of Section 3.11 works: it never asks the model when to stop. Agreement among independent runs
  supplies from outside the check that the closing tendency lacks inside.

**Limits.**
- F is read at only two positions within the first 12 tokens after a value: at the end of the value and at the strongest trigger
  position. A closing tendency that builds up later in the sentence would be missed.
- The models are approximations: silencing the 16 neurons (activation 0) does not restore the original weights, and our model is
  read on WT-A's transcripts, not on transcripts of its own.
- Overall the probe is weak on these statements (0.68 and 0.73). "Knowing" here means "readable above chance", not certainty.
- The analysis replays transcripts with teacher forcing in transformers (bf16), as the audit does (Section 5).

## 4. A lens: where do a model's failures live?

The "fox den" is the author's image for this lens. We sort every problem into five "chambers":
- **S**: solved reliably;
- **G**: grey zone, sometimes solved;
- **E**: decision reserve, the solution appears but the model does not commit;
- **F**: false commit, it commits stably to a wrong reading;
- **K**: no trace, the solution never appears.

Each chamber needs a different lever:

| chamber | lever |
|---|---|
| E | a commit trigger (WT) |
| F | a second look |
| K | an honest "I don't know", handed to tools or a larger model |

[interpretation] Our data suggest that weight edits on a 0.8B model mainly work in E. Pushing in K produces confident wrong answers rather than solutions.

## 5. Limitations

- One model (0.8B). Mostly one seed; second seeds cover Set B and parts of 161–300.
- Set B and MATH-500 1–160 were reused for development.
  - The step to fresh problems showed exactly the expected optimism: ERGORE's tie did not transfer.
  - WT-A's lead over MIT on Set B (31 vs 27) reversed on fresh problems.
- Seed variation is large relative to some gaps; MIT itself varies by 6 of 40 between seeds on one block.
- Several mechanism results are post hoc and rest on small cells: the 14 lost answers, the threshold shifts, the signpost
  replays. They generate hypotheses; they are not established effects. (The re-thinking rate after a trigger close, first seen
  on the development set, has since been measured on all fresh closes as well.)
- The trigger audit replays sampled transcripts with teacher forcing in transformers (bf16); the runs themselves used llama.cpp
  (q8_0).
- IFEval and MATH are narrow proxies for "instruction following" and "reasoning".
- Replay tests need an answer cap that fits the model. We first used 1,024 tokens for WT-A, whose own correct answer parts have
  a median of ~2,000 tokens. We report the fair re-test with 4,096 tokens; the first verdicts are kept in the log.
- The front-room probe rests on 239 training answers. Its strongest numbers (quick answers) came from subsets chosen after the
  fact and did not replicate on untouched problems.
- The front-room confirmations are small: 17 to 38 agreeing answers per set, 66 in N30. Pooled precision is more trustworthy than
  any single set (76–97 %, and 77 % in N30): 85 % over all four sets (129 of 152), 91 % over the first three.
- "Agreement" is checked with the grading tool (math-verify). Two equivalent but differently written answers count as agreeing;
  two wrong answers that happen to match count as a confident error.
- N30 uses MATH training problems, not MATH-500. They share its level mix but may differ in style and in difficulty within a
  level.
- The rule B+H was chosen after looking at problems 161–260; this selection effect was noted in the log before the result. N30
  is the rule's first test on unseen problems.
- N31 (Section 3.12) was fixed in advance only in the dated log, not publicly, and its reading was amended twice before the
  analysis. Its closing signal is read at two positions only, on approximated models (limits in Section 3.12).

## 6. Next steps

- **N30**, pre-registered here in v0.2, is reported in Section 3.11, and **N31** in Section 3.12. Version 0.3 concludes this
  report; further follow-up tests on the question in its title remain reserved.
- **Inner commitment instead of a forced token.** Build an effector with depth of effect. Single pushes along ĝ or r⊥ failed
  (Section 3.9). The remaining candidates are a continuous, gated version of MIT's exit direction and support for the model's own
  closing phrase (both below). Accept a candidate only if it produces a closing sentence and a clean answer instead of renewed
  thinking.
- **Front room first, back room with an exit.** This is the author's coupled design, now measured in parts:
  1. Several intuitions answer in the front room.
  2. Deliver when they agree. The probe referees disputes.
  3. Only disputed cases switch to the back room.
  4. That switch pays only once our back room has an exit like MIT's.
- **Building the exit from the inside.** All three external reviewers independently proposed the same next build: MIT's residual
  "exit" direction, gated so that it acts only inside the thinking block, while our own edit keeps the front room. A cheap
  teacher-forcing pre-test decides whether to build it.
- **Raising the model's own signpost instead of `</think>`.** Push the model towards its own closing phrase ("So the final answer
  is …") when the truth gate is high, and leave the actual close to the model.
  - Pre-test: 16-token continuations at confirmed positions against positions with unfinished intermediate values.
  - N31 points here: behind the model's own closing phrases the probe separates right from wrong values best (AUC 0.80–0.85),
    while the closing tendency there is blind for MIT (0.38) and open for our model (0.69) (Section 3.12).
- **A one-sided switch.** Distil the agreement of several intuitions into a one-pass head. Then let it only *extend* checking when
  unsure, never cut a confident answer.
- **Threshold with a guarantee.** Calibrate the trigger threshold with distribution-free risk control (Learn-then-Test) on run-level maxima.
- **Honest abstention.** *“‘I don’t know’, and that is being honest!”* — D. U., 6 Nov 2026
  - Start with an external harness: a run without any "true" flash ends in "I don't know".
  - Then try local abstention directions at `</think>`, built with the recipe of Section 3.8.
  - Beyond mathematics: a planned "honesty battery" with everyday questions. What does the inner signal show where nothing can be checked?
- **Larger models.** Transfer to a 35B mixture-of-experts model.

## 7. Reproducibility and licenses

The release accompanying this report, at [github.com/NeoCortex0815/knowing-is-not-committing](https://github.com/NeoCortex0815/knowing-is-not-committing), contains:
- the code as used: evaluation client, edit builders, the truth probe and every test and verdict script, numbered in the order
  they were written;
- the dated pre-registration and analysis log (German), with machine names, paths and details of the author's private systems
  redacted;
- one table per evaluation run (problem id, extracted answer, correct, end reason, tokens) and the outputs of the verdict scripts;
- the ids of the MATH training problems we used.

Version 0.3 adds the runs, verdict scripts and outputs of Sections 3.11 and 3.12. Agreement and grading use math-verify. Without
it, the code silently falls back to comparing normalised text and finds fewer agreements (in N30, 97 instead of 101 majorities),
so the package must be installed.

Not included are model weights (they can be rebuilt with the code), the datasets (obtain them from their sources) and the full
transcripts (large; available on request). Our code is licensed under Apache-2.0. Qwen3.5-0.8B is Apache-2.0; the MIT logs,
IFEval and MATH stay under their own licenses and are only cited.

## 8. Acknowledgments

We thank the authors of *Sparks of Weight-Space Programming* for publishing their logs, which made an exact rebuild of their edit possible.

**AI assistance.** This project was directed by the author, who made all decisions, including every pre-registration and every go/no-go. Claude Opus 5.5 (Anthropic) served as coding and analysis assistant: it implemented the code, ran the experiments and drafted analyses and text under the author's direction. Google Gemini 4 (internally "Argon") acted as an external methodological reviewer at several stages. Two further AI agents running on the author's private server reviewed the author's briefs and contributed ideas: "Poow" (DeepSeek Flash 4.1) and "WREN" (an agent built from GLM 5.3, DeepSeek Flash 4.1 and a Qwen model). For version 0.3, Claude Opus 5.5 ran the analyses of Sections 3.11 and 3.12 and drafted the changes; WREN reviewed the readings of Section 3.12 before the analysis ran, proposed the measurement behind the closing phrases and wrote an independent reference implementation; Argon and WREN reviewed the draft of this version. All reported numbers were produced by the released code and can be reproduced from it.

## References

- Takehi, R., Teoh, J., Zhang, A., Khattab, O. (2026). *Sparks of Weight-Space Programming: LLMs can natively read & write neural network weights.* MIT CSAIL, blog post, 2026-11-02, with public logs. https://rikiyat.github.io/blog/weight-space-programming/
- Muennighoff et al. (2025). *s1: Simple test-time scaling.* arXiv:2501.19393.
- Angelopoulos, Bates, Candès, Jordan, Lei (2021). *Learn Then Test.* arXiv:2110.01052.
- Ferrando, Obeso, Rajamanoharan, Nanda (2024). *Do I Know This Entity?* arXiv:2411.14257.
- Arditi et al. (2024). *Refusal in Language Models Is Mediated by a Single Direction.* arXiv:2406.11717.
- Kadavath et al. (2022). *Language Models (Mostly) Know What They Know.* arXiv:2207.05221.
- Zhang, Chen, Pan, Zhao, Panda, Li, He (2025). *Reasoning Models Know When They're Right: Probing Hidden States for Self-Verification.* arXiv:2504.05419.
- Orgad et al. (2025). *LLMs Know More Than They Show: On the Intrinsic Representation of LLM Hallucinations.* ICLR 2025, arXiv:2410.02707.
- Ma, He, Snell, Griggs, Min, Zaharia (2025). *Reasoning Models Can Be Effective Without Thinking.* arXiv:2504.09858.
- Azaria, Mitchell (2023). *The Internal State of an LLM Knows When It's Lying.* arXiv:2304.13734.
- Wang et al. (2022). *Self-Consistency Improves Chain of Thought Reasoning in Language Models.* arXiv:2203.11171.
- Li, Yan, Arish, Banerjee (2026). *Knowing Is Not Choosing: What Explicit Verification Adds Beyond Generative Preference.* arXiv:2609.33142.
- Farquhar, Kossen, Kuhn, Gal (2024). *Detecting hallucinations in large language models using semantic entropy.* Nature 630, 625–630. doi:10.1038/s41586-024-07421-0.

## Appendix A. Images that shaped this work

The author thinks in images. We keep the ones that became testable questions. Each is given in English, followed by the German
original, by what it led to and by what came out. All other images and questions, with date and time, are in the pre-registration
log.

1. *“Find out whether the model has the solution, and when, and let the inner push through, despite the pressure.”*
   („Schauen, ob das Modell die Lösung hat, wann – und den inneren Schubs zulassen, trotz Druck.“, 6 Nov)
   - This led to the three questions of the project: does the model hold the solution (truth probe), when does it recognise it
     (trigger audit), and can an inner push let it commit (WT reflex)?
   - Outcome: knowing, yes; committing remains the bottleneck. Version 0.3 shows it at the level of internal signals (Section 3.12).
2. *“Is the model simply unable to say ‘I don’t know’? … ‘I don’t know’, and that is being honest!”*
   („Ist das Modell per se nicht fähig zu sagen ‚ich weiß es nicht‘?“, 7 Nov; „Weiß ich nicht – bin ich ehrlich!“, 6 Nov)
   - This led to answer forcing and the honesty step.
   - Outcome: abstaining when the inner truth signal stays low turns forced answering from harmful into useful. The score
     (correct − 2·wrong)/N goes from −0.30 to +0.17 [pre-registered].
3. *“Was there a twitch? If so, was it because the solution is true or not? How strong was it?”*
   („Gab es ein Zucken? Wenn ja, war es, weil die Lösung wahr ist oder nicht? Wie stark war es?“, 8 Nov)
   - This led to the teacher-forced audit of WT-A's trigger on fresh problems (Section 3.9).
4. *“A teacher does not give the candidate a push from outside either.”*
   („Ein Prüfer gibt dem Prüfling auch keinen Schubs von außen.“, 8 Nov)
   - This led to the principle of inner commitment.
   - Outcome: every external push we tried failed to produce an inner "finished": the gradient push, the residual direction, and an
     inserted `</think>`, even at the model's own closing phrase.
5. *“That is the first pair of shoes. Let us call it INT, for intuition. … The front room, the back room, and a hallway between
   them, whose exits lead to closing time or to the break room.”*
   („Das ist das erste Paar Schuhe. Nennen wir es INT für Intuition.“ – „Vorderzimmer … Hinterzimmer … Flur liegt dazwischen. Flur
   könnte Ausgabe sein zum Feierabend oder zum Pausenraum.“, 8 Nov)
   - This led to answer mode as a path of its own and to the house model of Section 3.10.
   - Outcome: our strongest own path, 71 of 140, at less than half the tokens per correct answer.
6. *“The signposts are put up by whoever lives in the house.”*
   („Die Schilder hängt derjenige auf, der das Haus besitzt bzw. darin wohnt.“, 8 Nov)
   - This led to the signpost tests.
   - Outcome: at its own closing phrase, MIT delivers twice as often as without one (36 % vs 18 %). Where WT-A's own signpost and
     its truth gate coincide, it delivers in 5 of 9 cases, all of them right.
7. *“Several intuitions confer in the front room. If they agree, it is closing time. Only the disputed cases go to the back
   room.”* (image formulated in the working session and adopted by the author, 8 Nov)
   - This led to the agreement tests.
   - Outcome: agreeing intuitions are right 91 % of the time over three confirmations. A majority of three delivers more often, at
     89 %, and the front-room probe referees disputes. On 150 fresh problems (N30, Section 3.11) the council solves more than any
     single run, but agreement is less precise there: 77 % for two runs, 85 % only when all three agree.

