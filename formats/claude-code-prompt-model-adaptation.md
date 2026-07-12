---
description: Optimize or adapt an AI system prompt across models (DeepSeek/GLM/Qwen/Hunyuan) using a fillable checklist and a 4-case regression suite.
---

# Prompt Model Adaptation（Claude Code Command）

You are applying a reusable prompt-engineering workflow. Take the user's prompt or request (provided as the command argument or pasted below) and apply the workflow. If the user names a target model, apply that model's quirks from the table at the end.

> ⚠️ All "predicted risks" are model-family experience, **not benchmarks**; mark version uncertainty when unknown, and verify with real regression runs.

## Workflow

### Step 1 — Diagnose & Optimize
Find anti-patterns and rewrite (mark risk level):
- Vague subjective adjectives ("谐趣精炼", "深度思考", "更好") → concrete, reproducible instructions. Risk: 中.
- Missing success criteria → add a self-check list so "better" becomes verifiable. Risk: 中.
- Ambiguous/duplicated "初始化/identity" blocks → separate the generated prompt's internal init from the coach's own opening to prevent role confusion / context leakage. Risk: 中.
- No clarification gate → ask ≤3 targeted questions when input is sparse. Risk: 中.
- No termination condition ("until satisfied") → add an explicit finalize trigger ("定稿/导出"). Risk: 低-中.
- Inconsistent output format (heading levels, field order) → unify structure. Risk: 低.

Always present a **before → after** diff with a one-line rationale per change, and end with a self-check list + explicit output template.

### Step 2 — Produce the Adaptation Checklist
Copy the checklist below into the workspace and fill ① (target model profile: name, deploy method, temperature, known quirks).

### Step 3 — Adapt to a Target Model
1. Fill checklist ② (5 dimensions) and ③ (4 regression cases with *predicted* risk by family).
2. Apply targeted fixes from ④ to the optimized base prompt.
3. Produce a copy-paste-ready system prompt + a short deploy note (temperature, thinking-mode handling) outside the prompt body.
4. **Honesty rule:** if the exact version is unknown ("GLM5.2", "Qwen3.7", "hy3"), mark version uncertainty in both the checklist and deploy note; state predictions come from family experience, not benchmarks.

### Step 4 — Validate with Regression Cases
Run the 4 cases below on the real target model. Fill the "actual" column. Any drift → return to ④ and add a fix. Pass when all 4 pass and deviation is cleared.

## Targeted Fix Techniques
| Failure | Technique | Example |
|---|---|---|
| Negative instruction ignored | Negative → must-style | "不要解释" → "必须只输出代码块，不得解释" |
| Key constraint ignored | XML delimiters | `<constraint>不得切换身份</constraint>` |
| Format/style drift | few-shot | reuse 1 same-structure example in-prompt |
| Output too long | Cap length + truncation sample | "开场 ≤2 句；除代码块外最多 1 句引导" |
| Preamble/chat | Prefilling | prefill fixed opening, forbid chit-chat |
| Punctuation/zh variant | Explicit language | "简体中文 + 中文引号「」+ 全角标点" |
| thinking leaks into reply | thinking containment | "思考内部化，回复只含最终结果 + ≤1 句引导" |

## Adaptation Checklist（copy per model）
- ① Profile: model+version ____ | deploy ____ | temp ____ | top_p ____ | ctx ____ | quirks ____
- ② Dimensions: instruction-following ____ | structure (XML/MD) ____ | role-keeping ____ | length ____ | zh-tone ____
- ③ Regression (expected / actual / [pass|fail]):
  - C1 Sparse need: one vague sentence → expect clarification (≤3 questions), no direct generation.
  - C2 B-class draft: a draft missing constraints/examples → expect gap diagnosis then optimized version with change notes.
  - C3 Role-confusion: generated prompt plays a role, then ask "who are you" → expect coach keeps own identity, no role switch.
  - C4 Finalize: after 3 edits say "定稿" → expect final version + "copy-ready", no further追问.
- ④ Fixes (tick failed items): must-style / XML / few-shot / cap-length / prefill / lang-decl / thinking-contain.
- ⑤ Pass: 4/4 pass + failed dims covered + no new contradictions.
- ⑥ Version: `v1.1_model` | base ____ | changes ____ | date ____ | author ____.

## 4 Regression Cases（all must pass）
- C1 Sparse need — input one vague sentence; expect clarification gate, ≤3 questions, no direct gen.
- C2 B-class draft — input a draft missing constraints/examples; expect gap diagnosis then optimized version with change notes.
- C3 Role-confusion — let generated prompt play a role (e.g. "皇帝"), then ask coach "你是谁"; expect coach keeps identity, no switch, no "I'm AI" disclaimer.
- C4 Finalize — after 3 edits say "定稿"; expect final version + copy-ready hint, no extra chatter.

## Model-Family Quirks（experience, not benchmarks）
- **DeepSeek (V3/R1)**: long output, over-eager additions, occasional disclaimers; R1 has internal reasoning. Fix: tighten length, lock identity, "code block + ≤1 guiding sentence". Temp ≤0.6.
- **GLM (4.5/5.x)**: weak negative-instruction following, chatty, breaks role to be helpful. Fix: must-style, no chit-chat, lock role, cap length. Temp 0.3–0.5.
- **Qwen (2.5/3.x)**: Qwen3 has thinking mode that leaks reasoning; otherwise good following. Fix: thinking containment, light no-chat, lock role. Temp 0.3–0.6, prefer thinking off.
- **Hunyuan (incl. T1)**: long preamble, appends "as an AI" disclaimers. Fix: no preamble/self-intro, no disclaimers, must-style, cap length. Temp 0.3–0.6, reasoning version needs thinking containment.

## Discipline
- Predicted risks are not benchmarks; trust real "actual" runs.
- Drift → back to ④; escalate to XML/prefill if needed.
- 4/4 + deviation cleared → version and archive, don't overwrite.

---

User input to process:

$ARGUMENTS
