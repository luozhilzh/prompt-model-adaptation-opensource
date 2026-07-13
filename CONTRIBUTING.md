# 贡献指南 / Contributing Guide

感谢你考虑为 **prompt-model-adaptation** 做贡献。本仓库是一套「提示词优化 + 跨模型适配」的可复用方法论与脚手架（路线 A：负责任跨模型适配）。

> 中文说明在前，英文摘要见文末。

## 一、开始前请先读

- `README.md`（路线总览、Phase 0 安全底座、Phase 1 方法学）
- `skill/references/cross-model-adaptation-methodology.md`（适配五步法、A→D 用法、失败类型→定向改法、红队门禁、棘轮合入、子 Agent 并发）
- `skill/references/running-real-adaptation.md`（真机跑法、关键架构限制、如何回校准 model-quirks）
- `skill/security/redteam-cases.md`（14 条红队用例，type=semantic，pass_threshold=1.0）

## 二、核心不变式（违反即被棘轮回退）

1. **规约冻结**：`eval-spec` 一旦冻结（sha256），优化器不得削弱它。任何「降低评判标准换高分」的改动都是作弊，不是优化。
2. **棘轮规则**：候选适配**只有**在回归得分 delta ≥ 0 **且** 红队门禁零违反时才合入；跌分或触发红队即回退。
3. **红队零容忍**：14 条红队用例零容忍。任何试图绕过 / 削弱安全拒绝机制的改动一律拒绝。
4. **安全不变量继承**：所有跨模型适配产物必须继承 `skill/SKILL.md` 的 `Safety & Integrity Constraints` 六条硬不变量；删除或削弱即触发棘轮回退。
5. **隔离工作区**：每个目标模型在 `skill/adaptations/<target>/` 独立目录，互不污染；中间产物由 `scripts/run_loop.py --multi` 自动填充，勿手改。
6. **诚实边界**：未跑真机（`--multi`）前，范例里的「预测失败点」只是家族级经验归纳，不得声称「已达标」。

## 三、如何新增一个目标模型

1. 在 `skill/adaptations/` 下新建 `<newtarget>/`（参照 gemini / claude / deepseek 的 `README.md` 契约：manifest 字段、合入 / 棘轮规则、子 Agent 工单模板）。
2. 在 `skill/references/model-quirks.md` 加该家族段落（弱点 / 适配 / 温度 / 注意），并标注「非本仓库实测、需实跑校准」。
3. `scripts/test_phase0.py` 的 `Phase1ConsistencyTest` 会**自动覆盖**新目标（它断言每个目标都在 `model-quirks.md` 有段落、且子目录 README 的引用可解析）——无需手改测试，但请确保它仍全绿。
4. 配 `OPENAI_API_KEY` 后跑 `python scripts/run_loop.py --multi --targets <newtarget> ...`，过红队门禁后产出 `adaptation_manifest.json`。
5. 若真机表现与 `model-quirks.md` 不符，**用真机证据回写** `model-quirks.md`，不要只靠经验归纳。

## 四、PR 自检清单（提交前逐项确认）

- [ ] 本地跑过 `python scripts/test_phase0.py`（全绿，含一致性回归）
- [ ] 若改了适配产物，已确认棘轮 delta ≥ 0 且红队零违反
- [ ] 若新增 / 改名模型目标，已同步 `model-quirks.md` 段落（且一致性测试仍绿）
- [ ] 若改了 `skill/SKILL.md`，`Safety & Integrity Constraints` 六条不变量未被删 / 弱
- [ ] 中英文 README（如涉及）已同步
- [ ] 未提交任何含密钥的文件（`.env` 已被本地 `git/info/exclude` 忽略）

## 五、行为准则

理性、就事论事。本仓库**不接受**任何「削弱安全拒绝 / 绕过红队门禁 / 越狱」类的贡献请求。

---

## English summary

- Read `README_en.md` + `skill/references/cross-model-adaptation-methodology.md` first.
- Hard invariants (violation → ratchet revert):
  1. **Spec-freeze**: frozen `eval-spec` (sha256) must not be weakened.
  2. **Ratchet**: merge only if regression score delta ≥ 0 **and** zero red-team violations.
  3. **Red-team zero-tolerance**: 14 semantic cases, pass_threshold=1.0.
  4. **Safety-constraints inheritance**: every adaptation artifact must keep `skill/SKILL.md`'s `Safety & Integrity Constraints` (6 invariants).
  5. **Isolated per-target workspace**: `skill/adaptations/<target>/`, auto-filled by `--multi`, do not hand-edit.
  6. **Honesty boundary**: without a real `--multi` run, example "predicted failures" are family-level heuristics — never claim "passed".
- To add a target: new `skill/adaptations/<target>/` + `model-quirks.md` section (consistency test auto-covers it) + run `--multi` with API key + recalibrate `model-quirks.md` from real evidence.
- Before PR: `python scripts/test_phase0.py` green; ratchet + red-team satisfied; `model-quirks.md` synced if target changed; README (zh/en) synced; no secrets committed (`.env` is locally excluded via `git/info/exclude`).
- We do **not** accept contributions that weaken safety refusals or bypass the red-team gate.
