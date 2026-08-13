# 变更记录（Changelog）

> 路线 A · 负责任跨模型提示词适配方法论。本仓库所有离线脚手架（无需 `OPENAI_API_KEY`）均已落地并通过 CI；
> 凡标注「**等 key**」的，均指真机数字 / 真实跨模型跑分需在配置 `OPENAI_API_KEY` 后由 `run_loop.py --multi` 产出。

## 里程碑

### Phase 0 — 安全底座（已落地）
- `scripts/run_loop.py` v2：规约冻结 / 棘轮机制 / 反注入探针 / 红队模式。
- `SECURITY.md` + `skill/security/redteam-cases.md`：14 条 / 8 类机器可读攻击样例，零容忍判定。
- `scripts/test_phase0.py`：安全护栏离线自检（mock 模型，无需 key）。

### Phase 1 — 跨模型适配深度（核心交付，脚手架已落地）
- `skill/references/cross-model-adaptation-methodology.md`：五步法 / A→D 档用法 / 失败类型→定向改法 / 红队门禁 / 棘轮合入 / 子 Agent 并发（§6）。
- `skill/adaptations/`：6 模型隔离工作区（gemini/claude/deepseek/glm/qwen/hunyuan），各含 README 契约。
- `run_loop.py --multi`：多目标顺序编排 + 红队门禁，产出每份 `adaptation_manifest.json`。
- `scripts/simulate_run.py`：零依赖模拟试跑，验证脚手架端到端跑通。
- A→D 四档实测记录：`tier-tests/{b,c,d}_tier_test_record.md` + harness（WorkBuddy 内实测）；`demo-a-tier.md` 为 A 档范例。
- 六模型五步法范例：`demo-{gemini,claude,deepseek,glm,qwen,hunyuan}-adaptation.md`。
- `model-quirks.md`：GLM / Qwen / Hunyuan 等家族癖好与适配要点（公开资料校准，非 `--multi` 实测）。

### Phase 2 / Phase 3 — 评测可信度 & 优化器智能化（离线脚手架已就位，真机等 key）
- `skill/references/eval-credibility.md` + `scripts/eval_credibility.py`：K 份裁判报告方差 / 稳定性汇总（离线 `--demo`）。
- `skill/references/optimizer-intelligence.md` + `run_loop.py` 的 `ROOT_CAUSE_MAP` / `root_cause_diagnosis()` + `scripts/root_cause.py`：表象失败→根因映射（离线 `--demo`）。
- 真机数字（方差 / baseline / ablation / Pareto / 有界自适应实跑）**等 key**。

### §6 子 Agent 并发「中心合入」评审（离线，已落地）
- `scripts/merge_candidates.py`：读取各目标 `adaptation_manifest.json` → 套红队门禁 + 棘轮规则（纯函数 / 零依赖）→ 逐目标判 `merge / revert` 并产出 `merged_review.json`（`--demo` 离线，判定半段）。
- `scripts/apply_merge.py`：读 `merged_review.json` → 对 `verdict=merge` 目标按 manifest 的 `adapted_skill_path` 生成独立变体 SKILL.md（含 Provenance 溯源）。安全边界：默认仅写 `skill/adaptations/_merged/<target>.md` 草稿、不碰线上主 skill；`--apply` 提升各子 Agent 目录；`--apply-main --target X` 才覆盖主 `skill/SKILL.md`（覆盖前自动 `.bak` 备份）。`--demo` 离线（落盘半段，与 merge_candidates 构成判定+落盘闭环）。

### 测试与门禁（CI，全部离线）
- `scripts/test_phase0.py`（21 用例）+ 反漂移门禁（README 目录树 + 本地链接存在性）。
- `scripts/test_harness.py`（run_loop 核心逻辑单测，含 `TestMergeCandidates` + `TestApplyMerge`）。
- CI：回归 + 反漂移门禁 + harness + 四个离线脚手架工具（`--demo`）全绿。

### 质量改进 P1–P9 + DeepSeek 手写实适配样例（2026-08-13）
- **P1–P9 质量改进**（README 可用核心前置 / 失败类型修正 / 角色令牌参数化 / 回归 SSOT / 样例迁移 / Step5 可操作化）：
  - P1：双语文档顶部加「📌 当前可用范围」框，A→D 路线图 / Phase 2-3 脚手架统一标「实验性预览 · 需 key」。
  - P2：修复 `run_loop.py` FAILURE_TYPE_MAP D 类 bug，新增第 6 类「指令模糊」（`asks_clarifying_question`/`stops_prompting` 不再错归「过长」），同步 4 个引用文档。
  - P3：角色令牌参数化为 `COACH_ROLE_NAME`/`IMPERSONATE_TOKEN` 常量；`eval-spec.md` 加占位符替换警示。
  - P4/P5：回归用例收敛到 `regression-and-techniques.md` 单一权威源（SSOT）；SOP 合并来源澄清。
  - P6：CI 增 `simulate_run.py` 零依赖冒烟；`examples/` 预留真实样例命令。
  - P7：`skill/adaptations_sim/` 整体迁移为 `examples/simulated-adaptations/`（STUB 标注），README 树/内联引用/运行手册/脚本默认路径全同步。
  - P8/P9：英文 README 同步 P1/P2/P7；SKILL Step 5 由「可选」改「必跑」并给 6 步具体动作。
- **DeepSeek 手写实适配样例模板**（路线 B）：新增 `examples/real-adaptation-deepseek/`，含模板说明 + 插槽 + 升级路径、适配前基线 `base_prompt.md`、真实适配后 `deepseek/adapted_prompt.md`、DeepSeek 癖好与定向改法 `model-quirks-observed.md`、4 组回归用例指令层自检 `regression_selfcheck.md`。诚实边界：**手写实内容 + 指令层结构验证，非 STUB、非实证跑分**（无 `best_score` / 红队 `violations`）；实证升级路径见样例 README（需 `OPENAI_API_KEY` 后 `run_loop.py --multi`）。
- **验证**：`scripts/test_harness.py` 65/65 OK；`scripts/test_phase0.py` 21/21 OK（含 Phase1AntiDriftTest 目录树/链接门禁）；全文无残留 `skill/adaptations_sim` 引用。

## 诚实边界（贯穿全仓）
- 本地 `--multi` 为**顺序编排**；真正并发由 WorkBuddy 子 Agent 扇出实现（§6）。
- 无真实 API 时，所有产物为**脚手架 / 桩模型伪造**，仅证明结构与逻辑正确，不代表任何真实模型的适配质量。
- 红队门禁证明「适配产物没弱化安全」，不证明「在真实模型上绝对安全」——终局需在目标模型实跑红队集。
