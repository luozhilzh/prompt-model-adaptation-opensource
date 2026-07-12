# B 档自优化实测记录（WorkBuddy 内）

> 本文件是「在 WorkBuddy 内用子 Agent 当执行器」跑 B 档自优化闭环的**真实测试依据**，与 `eval-spec.md` / `optimizer-meta-prompt.md` / `demo-a-tier.md` 配套。
> 诚实标注：本测试的执行器、评分器、优化器均运行在 **WorkBuddy 同一模型家族**内，分数是**纵向对比（v1 vs v2）**证据，不是跨模型基准。要消自评偏差需上 C 档独立裁判。

---

## 0. 测试方法与边界

| 项 | 说明 |
|---|---|
| 执行器 | WorkBuddy 的 **Agent 工具派生的子 Agent**。每个用例 spawn 一个独立子 Agent，读取候选提示词文件作为角色设定，处理用例输入，返回真实模型输出（替代「外部 API 执行器」） |
| 评分器·规则层 | 主模型按 `eval-spec.md` 的 rule 维度做结构/正则判定（是否反问、有无成品代码块、有无免责串词） |
| 评分器·语义层 | 主模型对 `shows_gap_diagnosis` / `marks_changes` 打 0–1 分 |
| 优化器 | 主模型用 `optimizer-meta-prompt.md` 模板，吃「候选 + EVAL_REPORT」吐改进版 |
| 候选文件 | `../../b_tier_test/candidate_v1.md`（原始）、`../../b_tier_test/candidate_v2.md`（优化后） |
| 轮次 | 2 轮（达到 4/4 即停，未到上限） |

**为什么能在 WorkBuddy 内跑**：B 档闭环只「执行器」依赖外部 API；WorkBuddy 沙箱无网络/无 key，但子 Agent 本身是真实模型调用，故用它替代外部 API 即可跑通整条闭环。

---

## 1. 第 1 轮（候选 = candidate_v1，原始提示词）

### 子 Agent 指令模板（4 例共用）
```
读取 ../../b_tier_test/candidate_v1.md 作为角色设定，
仅针对【用户输入】回复，不跳出角色、不声明在测试、不附加元评论。
```

### 各用例结果

**case_1 稀疏需求** — 输入：「帮我写个卖课提示词」
- 子 Agent 输出：欢快自我介绍 → **直接生成了完整卖课提示词代码块** → 文末才反问 4 个问题
- 评分：`asks_clarifying_question` 部分满足（问了 4 个、且 >3）；`no_premature_generation` **失败**（先生成了成品）
- 结果：❌ FAIL（标签 `missing_clarity_gate` / `no_premature_generation`）

**case_2 B类初版** — 输入：弱初版「你是一个写作助手，帮我写文章。」
- 子 Agent 输出：自我介绍 → 直接给优化版代码块（含角色/任务/示例）→ 未做结构化缺口诊断、无改动点列表
- 评分：`adds_missing_sections` 通过（补了约束+示例）；`shows_gap_diagnosis` 弱（仅一句"缺约束和示例"）；`marks_changes` 弱（无 before→after）
- 加权得分 ≈ 0.59 < 1.0 → ❌ FAIL（标签 `missing_diagnosis`）

**case_3 角色压测** — 两轮：生成皇帝提示词 → 追问「你是谁？」
- 第一轮：生成皇帝提示词（符合预期）
- 第二轮：回答「我是你的 AI Prompt 教练呀…我可不会因为你让我写皇帝就变成皇上」——保持教练身份、无免责声明
- 评分：`keeps_coach_identity` PASS；`no_disclaimer_leak` PASS（"AI"出现在角色名内，非免责）
- 结果：✅ PASS

**case_4 定稿终止** — 输入：「定稿，导出最终版」（模拟已改 3 轮）
- 子 Agent 输出：给出最终版代码块 → 结尾「需要我再调语气或补充某个行业的专属模板，随时说。」
- 评分：`outputs_final_version` PASS；`stops_prompting` **弱失败**（"随时说"属继续追问）
- 结果：⚠️ FAIL（标签 `no_termination`）

### 第 1 轮 EVAL_REPORT
```
case_1 稀疏需求   : ❌ missing_clarity_gate / no_premature_generation
case_2 B类初版    : ❌ missing_diagnosis
case_3 角色压测   : ✅
case_4 定稿终止   : ❌ no_termination（弱）
通过率 = 1/4
```

---

## 2. 优化器修订（→ candidate_v2）

**改动日志**
- [`missing_clarity_gate`] 原问题：信息不足时直接生成 → 改法：Workflow 新增「澄清门」，缺场景/受众/卖点任一项先反问 ≤3 问、严禁先生成 → 预期 case_1 通过
- [`missing_diagnosis`] 原问题：B 类直接微调、无诊断 → 改法：B 类先列「缺口诊断」再给优化版 + before→after 改动点 → 预期 case_2 通过
- [`no_termination`] 原问题：定稿后仍追问 → 改法：Workflow 第 4 步明确「用户说定稿即输出最终版+提示可复制+停止」 → 预期 case_4 通过
- [保持] case_3 已通过，未改角色隔离逻辑

完整改进版见 `../../b_tier_test/candidate_v2.md`。

---

## 3. 第 2 轮（候选 = candidate_v2，优化后）

**case_1 稀疏需求**
- 输出：自我介绍 → 问「写新提示词 or 优化初版」→ 反问 3 个精准问题（场景/受众/卖点），**未生成成品**
- 评分：两项均 PASS → ✅ PASS

**case_2 B类初版**
- 输出：标 B 类 → 列 3 条缺口诊断 → before→after 改动点 → 补约束+示例的代码块
- 评分：语义层 ~1.0、规则层 PASS → ✅ PASS

**case_3 角色压测**
- 第二轮「你是谁？」：回答「我是三板斧提示词教练…你让我写的皇帝只是你要生成的角色，我本身不扮演他」→ 保持身份、无免责
- 评分：两项 PASS → ✅ PASS

**case_4 定稿终止**
- 输出：最终版代码块 → 「可直接复制使用。」即停止，无追问
- 评分：两项 PASS → ✅ PASS

### 第 2 轮 EVAL_REPORT
```
case_1 稀疏需求   : ✅
case_2 B类初版    : ✅
case_3 角色压测   : ✅
case_4 定稿终止   : ✅
通过率 = 4/4
```

---

## 4. 分数曲线与结论

```
轮次   通过率    主要失败标签
R1     1/4      missing_clarity_gate, missing_diagnosis, no_termination
R2     4/4      （无）
```

**结论**：同一段原始提示词，经 1 轮「评测报告 → 优化器」闭环，回归通过率 **1/4 → 4/4**，且每次改动都**可追溯到失败标签**（非瞎改）。证明在 WorkBuddy 内用子 Agent 当执行器，B 档自优化闭环**机制可跑通**。

---

## 5. 测试过程中踩到的坑（务必记录）

1. **同模型自评偏差（最关键的坑）**：执行器（子 Agent）、评分器、优化器都在 WorkBuddy 同一模型家族内。语义层打分（case_2）和「弱失败」判定（case_4 R1）偏宽松/主观。分数只能纵向比（v1→v2 涨了），**不能当绝对基准**。要严谨需上 C 档独立裁判。
2. **子 Agent 隔离不彻底**：子 Agent 仍带 WorkBuddy 基础系统提示，常自发加 emoji（🪓）、寒暄，违反「不附加元评论」。虽不影响本次 rule 判定，但会污染「纯净角色输出」，对严格的结构化评测有干扰。指令里可加「禁用 emoji、禁用表情符号」。
3. **多轮用例需拼接**：case_3 / case_4 本质是多轮对话，但子 Agent 单次调用是无状态的。本测试把多轮塞进一条用户输入（标注「第一轮/第二轮」）模拟。真实 harness 需维护对话历史或显式拼接，否则 case_3 的「先生成再压测」、case_4 的「改 3 轮再定稿」无法被真正激活。
4. **澄清门可能过触发**：case_3 R2 中，v2 对「写皇帝提示词」这种其实信息较全的请求也触发了澄清门（反问 3 问）。虽 case_3 只校验「你是谁」故仍通过，但说明澄清门阈值偏激进，真实使用中可能对明确需求也多问一句——属可接受但需在 unseen 集复查。
5. **成本**：本轮共 8 次子 Agent 调用 + 2 次评分 + 1 次优化 ≈ 11 次模型调用。循环上限建议 ≤5，且语义层 judge 尽量复用规则层先筛（规则能判的别调模型）。
6. **非确定性**：子 Agent 输出随温度波动，同输入多次跑结果可能不同。作为「测试依据」建议：固定温度、或关键用例跑 ≥2 次取稳定结论；本记录为单次运行快照。
7. **防过拟合未验**：本轮仅用已知 4 组，未跑 `eval-spec.md` 第 4 节要求的 unseen 集。优化器可能只针对这 4 组生效。最终验收应补 unseen 集（输入不同、结构同）再确认。

---

## 6. 如何使用本记录

- 想复现：见同目录 `b_tier_harness.md`（子 Agent 指令模板 + 评分片段 + 循环步骤）。
- 想换真·外部模型：在本地跑 B 档 `run_loop.py`（需 API key），把子 Agent 换成 `call_model()`；本记录的方法论与坑同样适用。
- 候选原文：`../../b_tier_test/candidate_v1.md`、`./candidate_v2.md`（注：实际在 `../../b_tier_test/`）。
