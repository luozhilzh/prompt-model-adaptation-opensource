---
name: prompt-model-adaptation
description: This skill should be used when a user wants to optimize or refine an AI system prompt, adapt an existing prompt to a specific target model (e.g., DeepSeek, GLM, Qwen, Hunyuan), generate a model-adaptation checklist, or validate a prompt with regression tests. It provides a reusable workflow: diagnose & optimize the prompt → produce a fillable adaptation checklist → adapt to a target model by filling the checklist and applying targeted fixes → validate with 4 regression cases.
---

# Prompt Model Adaptation

## Overview

A reusable workflow for turning a vague or unstable prompt into a clear, stable one, then porting it across target models without regressions. It bundles the diagnosis method, a fillable adaptation checklist, common model-family quirks, and a 4-case regression suite.

## When to Use

- User asks to "优化/改写这段提示词" (optimize or rewrite a prompt).
- User asks to "适配成 XX 模型" (adapt a prompt to a specific model).
- User asks for a "模型适配检查表" (model adaptation checklist) or a way to QA prompt portability.
- User wants to validate a prompt's stability across models.

## Workflow

### Step 1 — Diagnose & Optimize the Prompt

Identify anti-patterns and rewrite. Common anti-patterns (mark risk level):

- Vague subjective adjectives ("谐趣精炼", "深度思考", "更好") → replace with concrete, reproducible instructions. Risk: 中.
- Missing success criteria → add a self-check list so "better" becomes verifiable. Risk: 中.
- Ambiguous or duplicated "初始化/identity" blocks → separate the generated prompt's internal init from the coach's own opening to prevent role confusion / context leakage. Risk: 中.
- No clarification gate → add a step that asks ≤3 targeted questions when input is sparse. Risk: 中.
- No termination condition ("until satisfied") → add an explicit finalize trigger ("定稿/导出"). Risk: 低-中.
- Inconsistent output format (heading levels, field order) → unify structure. Risk: 低.

Always present a **before → after** diff with a one-line rationale per change. End the optimized prompt with a self-check list and an explicit output template.

### Step 2 — Produce the Adaptation Checklist

Copy `references/checklist-template.md` into the user's workspace and fill section ① (target model profile: name, deploy method, temperature, known quirks). Explain that this sheet standardizes porting and doubles as a regression record.

### Step 3 — Adapt to a Target Model

1. Fill checklist sections ② (5 adaptation dimensions) and ③ (4 regression cases with *predicted* risk based on the model family — see `references/model-quirks.md`).
2. Take the optimized base prompt and apply targeted fixes from checklist ④.
3. Produce the adapted prompt: a copy-paste-ready system prompt plus a short deploy note (temperature, thinking-mode handling) outside the prompt body.
4. **Honesty rule:** If the exact model version is unknown (e.g., "GLM5.2", "Qwen3.7", "hy3"), mark version uncertainty explicitly in both the checklist and the deploy note; state that predictions come from family-level experience, not benchmarks, and must be verified by regression.

### Step 4 — Validate with Regression Cases

Run the 4 cases from `references/regression-and-techniques.md` on the real target model. Fill the "实际/actual" column in the checklist. Any drift → return to checklist ④ and add a fix (e.g., XML delimiters, prefilling, stronger thinking-mode containment). Pass when all 4 cases pass and deviation is cleared.

### Step 5 — Self-Optimizing Loop (Tier A)

After Steps 1–4 produce an optimized/adapted prompt, optionally run a self-review loop so the prompt improves against the regression suite without manual tweaking each round.

1. Take the candidate prompt and run the 4 cases from `references/eval-spec.md` (for Tier A, you may self-assess per the spec; for B/C/D, a script calls the real model — see the "Future plan" section in README).
2. Build an `EVAL_REPORT` = per-case `{expected, actual, pass/fail, failure tags}`.
3. Feed `{CANDIDATE_PROMPT + EVAL_REPORT}` into the optimizer meta-prompt in `references/optimizer-meta-prompt.md`. It returns `{change log + improved prompt}`.
4. Use the improved prompt as the new candidate; repeat up to N rounds (suggest ≤5). Keep the highest-scoring version and its change log.
5. Stop when all 4 cases pass (or rounds exhausted). The result is a prompt verified against the regression suite, ready to ship.

> Tiers: **A** = self-review (no API, manual/LLM self-assess). **B** = closed loop (script calls the real model + scorer). **C** = dual-model (separate judge). **D** = adaptive (failure tags auto-drive targeted fixes and backfill the checklist's "actual" column). The repo currently ships the Tier A design; B/C/D need a local script with an API key. See README "Future plan: self-optimization & adaptation (A→D roadmap)".

## Targeted Fix Techniques (cheat sheet)

- Negative → must-style: rewrite "不要X" as "必须Y / 只输出X".
- Contain verbosity: cap opening/output length; allow at most 1 guiding sentence outside the result code block.
- Lock role: state the assistant must keep its identity even if the user demands a switch; no disclaimer-style chatter.
- few-shot: reuse a reference example inside the prompt to align format/style.
- XML delimiters: wrap key constraints in `<constraint>…</constraint>` when Markdown adherence drifts.
- Prefilling: lock the opening to prevent preamble (useful for chat-UIs that support it).
- Thinking-mode containment: when the model reasons internally, require analysis to stay internal and the reply to contain only the final result.

See `references/regression-and-techniques.md` for the full list and the 4 regression cases.

## Resources

- `references/checklist-template.md` — fillable 6-section adaptation checklist (copy into workspace per model).
- `references/regression-and-techniques.md` — the 4 regression cases + full targeted-fix cheat sheet.
- `references/model-quirks.md` — common quirks and adaptation priorities for DeepSeek / GLM / Qwen / Hunyuan families.
- `references/eval-spec.md` — machine-readable spec for the 4 regression cases (id, input, expected, scoring dimensions, pass threshold) for A/B/C/D self-optimizing loops.
- `references/optimizer-meta-prompt.md` — the "prompt optimizer" meta-prompt that turns `{candidate prompt + eval report}` into `{improved prompt + change log}`, driving the self-optimizing loop.
- `references/模型适配横向对比.md` — cross-model comparison table of adaptation diffs across DeepSeek / GLM / Qwen / Hunyuan (handy when porting to multiple models).
