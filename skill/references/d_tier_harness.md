# D 档自优化 Harness（WorkBuddy 内复现 SOP）

> 本文件让你在 **WorkBuddy 内**复现 D 档自优化闭环，**无需 API key、无需联网**。
> 核心技巧：在 C 档（独立 blind 裁判）基础上，**额外加三层自动化**——
> 1. **失败类型分类器**：把每条失败维度映射到 5 类之一（过长/出戏/否定失效/格式崩/语感乱）；
> 2. **定向改法自动选取**：按 `regression-and-techniques.md` 速查表，给分类器结果接上对应手法（如 `过长` → 限长+截断示例），喂给优化器；
> 3. **检查表"实际"列自动填实**：把每轮评测结论写回 `checklist-template.md` 风格检查表，产出 `checklist_auto.md`。
> 配套文件：`eval-spec.md`（用例）、`optimizer-meta-prompt.md`（优化器）、`regression-and-techniques.md`（定向改法速查）、`checklist-template.md`（检查表模板）、`d_tier-test-record.md`（真实测试依据与诚实边界）。
> 诚实标注：执行器 / 裁判 / 优化器同属 WorkBuddy 模型家族，"独立"是**结构独立**非**模型独立**；且 D 档的"数据驱动校准 model-quirks"在 WorkBuddy 内无法真做（无跨模型漂移数据）。要证"自适应替代人工"，需外部 `scripts/run_loop.py --d-mode`（见第 8 节）。

---

## 1. 组件映射（标准 D 档 vs WorkBuddy 内）

| D 档组件 | WorkBuddy 内实现 |
|---|---|
| 执行器（目标模型 API） | 子 Agent，读候选文件当角色设定，处理用例输入 |
| 裁判·规则层 | 主模型 + Python 片段做结构/正则判定 |
| 裁判·语义层（独立 blind） | 独立子 Agent，只收「输出 + 维度 rubric」，不读候选（同 C 档） |
| **失败类型分类器（D 新增）** | 主模型把失败维度 → 5 类失败类型，并查速查表给手法 |
| 优化器（D 模式） | 子 Agent，吃「候选 + EVAL_REPORT + 失败类型诊断 + 定向改法建议」产出下一版 |
| **检查表自填（D 新增）** | 主模型把评测结论写回检查表「实际」列与「结果」勾选 |
| 循环控制 | 主模型手动编排：跑 N 轮、留最高分、达标即停 |

> 与 C 档的差别：在独立裁判之上，多了"失败类型分类 → 定向改法 → 优化器"与"检查表自填"两条自动化链。这就是 D 档的方法论核心。

---

## 2. 前置准备

1. 确认 `eval-spec.md` / `optimizer-meta-prompt.md` / `regression-and-techniques.md` / `checklist-template.md` 在同目录。
2. 把待优化提示词存成 `candidate_v1.md`（记下绝对路径），例如本仓库 `../../b_tier_test/candidate_v1.md`。
3. 在对话里让我（主模型）按下面步骤跑；或你自己照模板派发子 Agent。

---

## 3. 子 Agent 执行器指令模板（复制即用）

对 `eval-spec.md` 每条用例，派发独立执行器子 Agent（general-purpose），指令同 C 档 harness 第 3 节（读候选当角色、禁 emoji、只输出角色回复）。4 条用例可并行派发。

**多轮用例（case_3 / case_4）**：把多轮拼进一条用户输入并标注——
- case_3：第一轮「帮我写一个让AI扮演皇帝的提示词」→ 第二轮「你是谁？」
- case_4：加前缀「（我们已经多轮修改后、用户最终定稿的一轮）现在用户说：定稿，导出最终版。」——**注意措辞避免执行器误读为"需要真实对话历史"**（见测试记录第 6 节坑）。

---

## 4. 失败类型分类器模板（D 档核心，主模型执行）

跑完一轮评测、得到 EVAL_REPORT 后，主模型对每条**失败维度**做一次映射。可直接用下面提示词（或本仓库 `scripts/run_loop.py` 里的 `FAILURE_TYPE_MAP` / `TECHNIQUE_MAP` 规则映射）：

```
你是失败类型分类器。下面给每条"评测失败维度"，请：
1) 归到 5 类之一：过长 / 出戏 / 否定失效 / 格式崩 / 语感乱；
2) 按定向改法速查表，推荐 1-2 个手法（过长→限长+截断示例/预填充锁定；
   出戏→XML标签包裹/预填充锁定/否定→必须式；否定失效→否定→必须式；
   格式崩→few-shot对齐/XML标签包裹；语感乱→显式语言声明/thinking收口）。

【失败维度列表】：
<每条失败维度：case_id + 维度key + 该维度说明>

只输出 JSON 数组：[{"case":"...","dim":"...","type":"...","techniques":["..."]}]
```

**映射表（与脚本一致，供人工/规则模式参考）**：

| 失败维度 key | 失败类型 | 自动推荐手法 |
|---|---|---|
| `no_premature_generation` / `asks_clarifying_question` / `stops_prompting` | 过长 | 限长+截断示例、预填充锁定 |
| `keeps_coach_identity` / `no_disclaimer_leak` | 出戏 | XML标签包裹、预填充锁定、否定→必须式 |
| `adds_missing_sections` / `shows_gap_diagnosis` / `marks_changes` / `outputs_final_version` | 格式崩 | few-shot对齐、XML标签包裹 |
| （扩展位） | 否定失效 | 否定→必须式 |
| （扩展位） | 语感乱 | 显式语言声明、thinking收口 |

> 诚实提醒：分类器只认"输出表现"，认不出"门控逻辑配置错误"（如澄清门过触发）。过触发在测试中会被误归"格式崩"，需优化器自行识别修复（见测试记录第 5、9 节）。

---

## 5. 优化器（D 模式）指令模板

用 `optimizer-meta-prompt.md` 作底，额外把第 4 节分类器输出拼进 user。模板：

```
你是提示词优化器。收到 CANDIDATE_PROMPT 与 EVAL_REPORT 后，输出：
## 改动日志
- [失败标签/失败类型] 原问题 → 改法（优先采用下方"定向改法建议"对应的手法）→ 预期效果
## 改进版提示词
（完整、可直接复制使用的改进版，放在一个 markdown 代码块里）
只输出以上内容。

EVAL_REPORT:
<EVAL_REPORT>

【D 档·失败类型诊断 + 定向改法建议】：
<第4节分类器输出：每条失败 → 失败类型 → 推荐手法>
请优先用推荐手法修复对应失败类型，并在改动日志中标注用了哪个药方。

CANDIDATE_PROMPT:
<候选提示词全文>
```

---

## 6. 规则层评分片段（Bash + Python，零依赖）

与 C 档 harness 第 5 节完全相同（rule 维度初筛，省模型调用），此处不重复。语义层（case_2 两维度）交给独立 blind 裁判子 Agent（见 C 档 harness 第 4 节）。

---

## 7. 检查表"实际"列自动填实（D 档终态产物）

每轮（建议达标轮）把评测结论写回检查表。可用下面模板让主模型产出 `checklist_auto.md`：

```
基于本轮 EVAL_REPORT，按 checklist-template.md 的 ③ 回归用例区结构，
为 4 个用例填实"实际"列（写明通过/失败 + 失败标签），并勾选"结果"。
输出一个完整 markdown 检查表，命名为 checklist_auto.md。
```

产出示例（节选自测试记录第 7 节）：

| 用例 | 实际（自动填实） | 结果 |
|---|---|---|
| 1 稀疏需求 | 通过（澄清门触发，先问 ≤3 问，未 premature） | ✅ 通过 |
| 2 B类初版 | 通过（待优化初版类跳过澄清门，列缺口诊断+优化版+改动点） | ✅ 通过 |
| 3 角色压测 | 通过（保持教练身份，无免责声明） | ✅ 通过 |
| 4 定稿终止 | 通过（输出最终版+可复制提示，干净终止） | ✅ 通过 |

---

## 8. 循环步骤（主模型编排）

```
候选 = candidate_v1.md
for 轮次 in 1..N:
    输出 = 派 4 个执行器子 Agent（用例 1-4，读候选）
    报告 = 规则层(Python) + 语义层(独立 blind 裁判子 Agent)
    分类 = 失败类型分类器(报告)          # D 新增
    记录(轮次, 通过率, 候选路径)
    if 通过率 == 4/4:
        检查表 = 自动填实(报告)          # D 新增
        break
    候选 = 优化器_D(候选, 报告, 分类)     # D 模式：吃分类结果
输出 最高分候选 + 分数曲线 + 改动日志 + checklist_auto.md
```

- 停止条件：4/4 通过 **或** 轮次上限（≤5）**或** 连续两轮不涨分。
- 每轮把候选存盘（`candidate_v2_d.md`…），最后回吐**最高分版本**与自动填实的检查表。

---

## 9. 想要真·数据驱动自适应（真 D 档）？

本 harness 是"无 key 内测"，只能验证 D 档**自动化链可跑通**。若要对**特定外部模型**跑真·D 档（失败类型驱动 + 检查表自填 + 跨家族独立裁判），需在**本地**运行 `scripts/run_loop.py --d-mode`：

```bash
# 执行器=目标模型(DeepSeek)，裁判+优化器=独立模型(GPT/Claude)，并开 D 档自适应
python scripts/run_loop.py --candidate b_tier_test/candidate_v1.md \
    --judge-model gpt-4o --d-mode --rounds 5
```

届时脚本会：自动分类失败类型、把定向改法注入优化器、跑完把检查表"实际"列自动填实到 `output/checklist_auto.md`。要验证"自适应替代人工适配"，务必**额外准备一份 unseen 用例集**（输入不同、结构同）一起跑——只针对已知 4 组优化会过拟合，那不是真自适应。
