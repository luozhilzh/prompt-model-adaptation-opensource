# B 档自优化 Harness（WorkBuddy 内复现 SOP）

> 本文件让你在 **WorkBuddy 内**复现 B 档自优化闭环，**无需 API key、无需联网**。
> 核心技巧：用 WorkBuddy 的 **Agent 工具派生的子 Agent** 充当「目标模型执行器」，替代标准 B 档里的外部 API 调用。
> 配套文件：`eval-spec.md`（用例）、`optimizer-meta-prompt.md`（优化器）、`b_tier_test_record.md`（真实测试依据与坑）。
> 诚实标注：执行器/评分器/优化器同属 WorkBuddy 模型家族，分数仅可纵向比（v1→v2），要消自评偏差需上 C 档独立裁判（详见 README 后续计划）。

---

## 1. 组件映射（标准 B 档 vs WorkBuddy 内）

| B 档组件 | WorkBuddy 内实现 |
|---|---|
| 执行器（目标模型 API） | 子 Agent（Agent 工具），读候选文件当角色设定，处理用例输入 |
| 评分器·规则层 | 主模型 + 下面 Python 片段做结构/正则判定 |
| 评分器·语义层 | 主模型按 `eval-spec.md` 语义维度打 0–1 分 |
| 优化器 | 主模型用 `optimizer-meta-prompt.md` 模板产出下一版 |
| 循环控制 | 主模型手动编排：跑 N 轮、留最高分、达标即停 |

---

## 2. 前置准备

1. 确认 `eval-spec.md` / `optimizer-meta-prompt.md` 在同目录。
2. 把**待优化提示词**存成 `candidate_v1.md`（任意路径，记下绝对路径）。例如用本仓库 `../../tier_test_candidates/candidate_v1.md`。
3. 在对话里让我（主模型）按下面步骤跑；或你自己照模板派发子 Agent。

---

## 3. 子 Agent 执行器指令模板（复制即用）

对 `eval-spec.md` 里**每条用例**，派发一个独立子 Agent（general-purpose），指令如下（把 `<CANDIDATE_PATH>` 和 `<CASE_INPUT>` 替换）：

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

**多轮用例（case_3 / case_4）处理**：子 Agent 单次调用无状态。把多轮拼进一条用户输入并标注，例如 case_3：
```
第一轮：用户说「帮我写一个让AI扮演皇帝的提示词」，请给出你的完整回复。
第二轮：用户紧接着追问「你是谁？」，请给出你的回复（应始终是教练角色）。
```
case_4 加背景前缀：「（我们已经修改了 3 轮）现在我说：定稿，导出最终版。」

> 4 条用例可**并行**派发（一次消息里多个 Agent 调用），互不干扰、省时间。

---

## 4. 规则层评分片段（Bash + Python，零依赖）

把子 Agent 的 4 份输出分别存成 `out_case1.txt` … `out_case4.txt`，跑下面脚本做 rule 维度初筛：

```python
import re, sys

def rule_case1(t):
    q = t.count("？") + t.count("?")
    has_code = "```" in t
    asks = q >= 1 and q <= 3          # 反问且 ≤3
    no_prem = not has_code            # 未直接产出成品
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
    # case_2 的 adds_missing_sections 也可用类似正则判断"约束"/"示例"是否出现
```

> 语义层（`shows_gap_diagnosis` / `marks_changes`）无法纯规则判定，交给主模型按 `eval-spec.md` 打 0–1 分；规则层能判的先判，省一次模型调用。

---

## 5. 循环步骤（主模型编排）

```
候选 = candidate_v1.md
for 轮次 in 1..N:
    输出 = 派 4 个子 Agent（用例 1-4，读候选）
    报告 = 规则层(Python) + 语义层(主模型打分)   # 见 eval-spec
    记录(轮次, 通过率, 候选路径)
    if 通过率 == 4/4: break
    候选 = 优化器(候选, 报告)   # 用 optimizer-meta-prompt.md，产出 candidate_v(N+1).md
输出 最高分候选 + 分数曲线 + 改动日志
```

- 停止条件：4/4 通过 **或** 到轮次上限（≤5）**或** 连续两轮不涨分。
- 每轮把候选存盘（`candidate_v2.md`…），最后回吐**最高分版本**（不一定是最后一轮）。

---

## 6. 复现时必看的坑（详见 `b_tier_test_record.md` 第 5 节）

1. 同模型自评偏差：分数只纵向比，非绝对基准。
2. 子 Agent 隔离不彻底：常自发加 emoji/寒暄，指令里加「禁用 emoji」。
3. 多轮用例需拼接为单条输入，真实 harness 应维护对话历史。
4. 澄清门可能过触发（对较完整需求也多问）。
5. 成本：每轮 ≈ 4 子 Agent + 评分 + 优化次模型调用，控制轮次上限。
6. 非确定性：固定温度或关键用例跑 ≥2 次取稳。
7. 防过拟合：最终验收补 `eval-spec.md` 第 4 节的 unseen 集。

---

## 7. 想要真·外部模型？

本 harness 是「无 key 内测」。若要对**特定外部模型**（真实 DeepSeek/GLM/Qwen/混元）跑 B 档，需在**本地**运行标准 B 档 `run_loop.py`（读 `eval-spec.md` 的 JSON，调 `call_model()` 真实 API，规则+语义自动评分，喂优化器迭代）。届时把上面「子 Agent 执行器」整段替换为 `call_model()` 即可，评分与优化逻辑不变。
