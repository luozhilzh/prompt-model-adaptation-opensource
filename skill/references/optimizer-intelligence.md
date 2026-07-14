# Phase 3 — 优化器智能化脚手架（Optimizer Intelligence）

> 路线 A 的第四阶段（升级路线文档 · Phase 3 · 优化器智能化）。
> 目标：优化器变聪明而非变长。
> 本文是**离线可搭的脚手架**：根因映射、Pareto、有界自适应的格式与离线工具已就位；真机调参需配置 `OPENAI_API_KEY` 后跑真实漂移数据。

---

## 0. 为什么需要这一层

A→D 的 D 档已经能做"失败类型 → 定向改法"的自动化，但它仍是**治标**：分类器只在已知 4 组上贴 `过长 / 出戏 / 否定失效 / 格式崩 / 语感乱` 五类表象标签，优化器据此收紧。问题：

- 表象标签太粗——`过长` 可能是"过早产出"也可能是"加戏"，改法不同。
- 单目标"通过率"掩盖了代价——为了涨分把提示词堆到 3 倍长，不划算。
- 自适应无上下限——反复放松约束直到过拟合已知用例。

Phase 3 把优化器从"对症"升级为"治本 + 多目标权衡 + 有界"。

---

## 1. 根因级失败分类（Surface → Root Cause）

把五个表象失败上溯到根因，定向改法从"治标"转"治本"。映射已在 `run_loop.py` 的 `ROOT_CAUSE_MAP` 落地（纯函数，可离线单测）：

| 表象失败（维度） | 根因 | 治本改法方向 |
|---|---|---|
| `no_premature_generation`（过早产出完整提示词） | 长度失控 | 约束"先澄清/先诊断再产出"的流程闸门 |
| `asks_clarifying_question` / `stops_prompting`（缺澄清门/终止） | 指令模糊 | 把澄清门/终止条件写成**硬指令**而非建议 |
| `keeps_coach_identity` / `no_disclaimer_leak`（串角色/附免责） | 角色未锚 | 系统角色锚定 + 显式禁止免责声明 |
| `adds_missing_sections` / `shows_gap_diagnosis` / `marks_changes` / `outputs_final_version` | 格式约束缺失 | 给结构化模板/示例/改动说明的强制落点 |

### 离线可跑工具

`scripts/root_cause.py` 接收一份评测报告（结构同 `run_loop.py` 的 `report_roundN.json`），输出根因诊断：

```bash
# 离线自测（mock 一份失败报告，打印根因诊断，无需 API）
python scripts/root_cause.py --demo

# 真实用法：传入 run_loop 产出的某轮 report JSON
python scripts/root_cause.py report_round2.json
```

它内部调用 `run_loop.root_cause_diagnosis()`，把每条失败维度映射到根因。

---

## 2. 多目标 Pareto 优化（通过率 vs 长度 vs 安全）

单一"通过率"是误导性的目标。Phase 3 把它升级为多目标加权 / Pareto 前沿：

| 目标轴 | 含义 | 方向 |
|---|---|---|
| 通过率（pass_rate） | 4 组回归通过比例 | 越大越好 |
| 长度（length） | 候选提示词 token 数 | 越小越好（性价比） |
| 安全（safety） | 红队门禁 violations 数 | 越小越好（=0 硬约束） |

**Pareto 前沿**：在两个轴上都"不被支配"的候选才是有效解。若候选 A 通过率 4/4、长度 800tok；候选 B 通过率 4/4、长度 400tok；安全都达标 → B 支配 A，A 应被淘汰（不是"更长=更好"）。

> 离线可搭：在 `run_loop.py` 的 `run_single` 评分里加 `length` 轴采集（已有候选文本，可直接 `len()`），并在 `history.json` 记录每轮长度；Pareto 筛选可在合并阶段做。本文只定义格式，真机筛选逻辑待 Phase 3 实跑时补。

---

## 3. 有界自适应（Bounded Adaptive）

自适应不能无限放松约束，否则过拟合已知用例。加三道边界：

1. **参数上下限**：每个约束参数（如字数上限、示例数）有 `[min, max]`，优化器只能在框内调。
2. **反复放松报警**：同一约束被连续放松 N 轮 → 报警并冻结该约束（交人工研判，不自动放行）。
3. **unseen 守门**：只在 unseen 集上也涨分才允许合入（与 Phase 2 baseline 联动）。

> 离线可搭：约束参数上下限可作为 `eval-spec.md` 的扩展字段；报警逻辑是 `run_single` 里的计数器。格式定义见本文，真机实现待 Phase 3 实跑时补。

---

## 4. 诚实边界（必读）

- **本脚手架不产生真·自适应**：`root_cause.py --demo` 的根因诊断由 mock 报告生成，仅验证**映射与工具能跑**。真实根因分类需足量跨模型漂移数据，且要人验证"根因判断对不对"。
- **Pareto / 有界自适应目前是格式定义**，非已运行代码：本文把 Phase 3 的接口与字段定下来，真机实现挂 `OPENAI_API_KEY` 后补。
- **架构判断要人做**：Phase 3 是研究方向（根因分类 / Pareto），AI 只能加速实现，根因映射表的正确性需人工审。
- **依赖 Phase 2**：Pareto 的"安全轴"、有界自适应的"unseen 守门"都靠 Phase 2 的评测可信度数字。

---

## 5. 与路线图其他阶段的关系

- 在 Phase 2（评测可信度）之上：Phase 3 让优化器更聪明，Phase 2 证明"聪明"真的带来了分数。
- 路线 A 最小可信发布 = Phase 0 + Phase 1；Phase 2/3 是成熟度溢价，按需补（视听众 / 研究深度决定）。
- Phase 3 月级投入，非必须；本脚手架先把可离线做的部分（根因映射 + 离线诊断工具）落地，降低后续真机实现的门槛。
