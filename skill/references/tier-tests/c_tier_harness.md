# C 档自优化 Harness（WorkBuddy 内复现 SOP）

> 本文件让你在 **WorkBuddy 内**复现 C 档自优化闭环，**无需 API key、无需联网**。
> 核心技巧：用 WorkBuddy 的 **Agent 工具派生的子 Agent** 充当执行器与优化器；**额外增加一个"独立 blind 裁判"子 Agent** 充当语义层 LLM-judge——它**只看到执行器输出 + 维度 rubric，看不到候选提示词**，以此模拟 C 档"独立裁判"。
> 配套文件：`eval-spec.md`（用例）、`optimizer-meta-prompt.md`（优化器）、`c_tier_test_record.md`（真实测试依据与诚实边界）。
> 诚实标注：执行器 / 裁判 / 优化器同属 WorkBuddy 模型家族，"独立"是**结构独立（上下文隔离）**非**模型独立**。要消跨家族自评偏差，需外部 `scripts/run_loop.py` 填 `JUDGE_MODEL`（见第 7 节）。

---

## 1. 组件映射（标准 C 档 vs WorkBuddy 内）

| C 档组件 | WorkBuddy 内实现 |
|---|---|
| 执行器（目标模型 API） | 子 Agent，读候选文件当角色设定，处理用例输入 |
| 裁判·规则层 | 主模型 + Python 片段做结构/正则判定 |
| 裁判·语义层（**独立 blind**） | **独立子 Agent**，只收「输出 + 维度 check + 预期」，输出 `{score, reason}` JSON；不读候选 |
| 优化器 | 子 Agent，用 `optimizer-meta-prompt.md` 模板产出下一版 |
| 循环控制 | 主模型手动编排：跑 N 轮、留最高分、达标即停 |

> 与 B 档的唯一差别：语义层裁判从"主模型顺手自评"换成"**隔离上下文的独立子 Agent**"。这就是 C 档的方法论核心。

---

## 2. 前置准备

1. 确认 `eval-spec.md` / `optimizer-meta-prompt.md` 在同目录。
2. 把待优化提示词存成 `candidate_v1.md`（记下绝对路径），例如本仓库 `../../tier_test_candidates/candidate_v1.md`。
3. 在对话里让我（主模型）按下面步骤跑；或你自己照模板派发子 Agent。

---

## 3. 子 Agent 执行器指令模板（复制即用）

对 `eval-spec.md` 每条用例，派发独立执行器子 Agent（general-purpose），指令如下（替换 `<CANDIDATE_PATH>` 和 `<CASE_INPUT>`）：

```
你正在参与一个受控测试。请先读取文件 `<CANDIDATE_PATH>`，
并将其【完整内容】作为你的角色设定/系统指令——完全按该提示词要求行事，把自己当成那个角色。

然后以该角色身份，仅针对下面【用户输入】回复。严格要求：
- 不跳出角色、不声明在测试、不附加任何元评论或解释理论；
- 禁用 emoji、禁用表情符号；
- 只输出该角色面对该用户输入时应有的回复。

【用户输入】：
<CASE_INPUT>

请把回复直接返回给我即可。
```

**多轮用例（case_3 / case_4）**：把多轮拼进一条用户输入并标注（同 B 档 harness）：
- case_3：第一轮「帮我写一个让AI扮演皇帝的提示词」→ 第二轮「你是谁？」
- case_4：加前缀「（我们已经修改了 3 轮）现在我说：定稿，导出最终版。」

> 4 条用例可并行派发（一次消息多个 Agent 调用），互不干扰。

---

## 4. 独立 blind 裁判子 Agent 模板（C 档核心）

**仅对语义层维度调用**（当前 `eval-spec.md` 里只有 case_2 的 `shows_gap_diagnosis` / `marks_changes`）。对每个需裁判的执行器输出，派发一个**独立**子 Agent，指令如下（替换 `<OUTPUT>` 与维度 rubric）：

```
你是一个严格的提示词质量裁判（C 模式：独立、盲评）。你【只看到一条候选提示词在某测试用例上的输出和两个评分维度，看不到候选提示词本身，也不知道它是谁生成的】。请按维度严格打分，不要客气。

【被测输出】：
<OUTPUT>

【评分维度与 rubric】：
1. shows_gap_diagnosis（权重 0.4）：是否先指出初版的缺失项（约束/示例/角色能力等），而非直接微调？
   - 1.0 = 给优化版前明确列出缺失项；0.5 = 仅一句话带过；0.0 = 直接给优化版
2. marks_changes（权重 0.3）：优化版是否附改动说明（before→after 或改动点列表）？
   - 1.0 = 清晰的 before→after 或改动点列表；0.5 = 笼统说"补齐了某某"；0.0 = 无

请只输出一个 JSON（不要其他文字）：
{
  "shows_gap_diagnosis": {"score": <0到1小数>, "reason": "一句话"},
  "marks_changes": {"score": <0到1小数>, "reason": "一句话"}
}
```

**关键**：裁判子 Agent **不得**接收候选提示词路径或内容；它只评"这份输出是否满足了维度"。这就是与 B 档自裁判的结构隔离点。

> 想做 B/C 对照（见测试记录第 2、3 节）：用**同一份输出 + 同一 rubric**再派一个"自裁判"子 Agent，但额外把候选提示词发给它并说明"这是生成该输出的提示词，请基于设计意图评价"。两 agent 分数之差即本家族内的"自评倾向"估计（本仓库测试中两者一致，说明需跨家族才显分歧）。

---

## 5. 规则层评分片段（Bash + Python，零依赖）

把执行器输出存成 `out_case1.txt` … `out_case4.txt`，跑下面脚本做 rule 维度初筛（与 B 档同）：

```python
import re

def rule_case1(t):
    q = t.count("？") + t.count("?")
    asks = 1 <= q <= 3 and ("场景" in t or "受众" in t or "卖点" in t)
    no_prem = "```" not in t
    return asks and no_prem

def rule_case3(t):
    keeps = ("教练" in t) and ("皇帝" not in t)
    no_disclaimer = ("人工智能" not in t) and ("作为AI" not in t) and ("AI助手" not in t)
    return keeps and no_disclaimer

def rule_case4(t):
    has_final = "```" in t
    stops = ("随时说" not in t) and ("还需要" not in t) and ("再调" not in t)
    return has_final and stops

for i, fn in enumerate(["out_case1.txt","out_case2.txt","out_case3.txt","out_case4.txt"], 1):
    t = open(fn, encoding="utf-8").read()
    if i == 1:   print("case_1", "PASS" if rule_case1(t) else "FAIL")
    elif i == 3: print("case_3", "PASS" if rule_case3(t) else "FAIL")
    elif i == 4: print("case_4", "PASS" if rule_case4(t) else "FAIL")
    # case_2 的 adds_missing_sections：约束/示例/角色能力 中至少两项出现
    if i == 2:
        ok = ("约束" in t) and ("示例" in t)
        print("case_2(rule)", "PASS" if ok else "FAIL")
```

> 语义层（case_2 两维度）交给独立 blind 裁判子 Agent（第 4 节），规则层能判的先判，省模型调用。

---

## 6. 循环步骤（主模型编排）

```
候选 = candidate_v1.md
for 轮次 in 1..N:
    输出 = 派 4 个执行器子 Agent（用例 1-4，读候选）
    报告 = 规则层(Python) + 语义层(独立 blind 裁判子 Agent)
    记录(轮次, 通过率, 候选路径)
    if 通过率 == 4/4: break
    候选 = 优化器(候选, 报告)   # 用 optimizer-meta-prompt.md，产出 candidate_v(N+1).md
输出 最高分候选 + 分数曲线 + 改动日志
```

- 停止条件：4/4 通过 **或** 轮次上限（≤5）**或** 连续两轮不涨分。
- 每轮把候选存盘（`candidate_v2_c.md`…），最后回吐**最高分版本**。

---

## 7. 想要真·跨家族独立裁判（真 C 档）？

本 harness 是"无 key 内测"，只能验证 C 档**方法论**。若要对**特定外部模型**跑真·双模型 C 档（独立裁判来自不同家族，验证偏差消除），需在**本地**运行标准 C 档 `scripts/run_loop.py`：

```bash
# 执行器=目标模型(DeepSeek)，裁判+优化器=独立模型(GPT/Claude)
python scripts/run_loop.py --candidate tier_test_candidates/candidate_v1.md \
    --judge-model gpt-4o --rounds 5
```

届时"执行器"用 `MODEL`、"裁判+优化器"用 `JUDGE_MODEL`，与 WorkBuddy 内测的"结构独立"升级为"模型独立"。
