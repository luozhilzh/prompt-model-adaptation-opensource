# 4 组回归用例 · 规则级自检（手写实适配）

> **方法论**：本文件对 `adapted_prompt.md` 做**指令层静态自检**——复用 `scripts/run_loop.py` 的 `rule_pass` 逻辑，但校验对象是**适配后提示词本身是否含有满足各维度的指令**，而非模型真实输出。
> **诚实边界（务必读懂）**：
> - ✅ = 适配后提示词**已写入**满足该维度的指令（静态可证）。模型是否**真正 obey** 仍需 live 跑分（需 `OPENAI_API_KEY`）。
> - ⏳ = 该维度是**语义层**判断（需 LLM-judge 或真机输出），手写实适配无法离线断言，标记为待 key 实证。
> - 这**不是** `best_score`。真机实证请见本目录 `README.md` 升级路径。

---

## 用例 1 — 稀疏需求（澄清门）

| 维度 | 类型 | 静态结果 | 说明 |
|---|---|---|---|
| `asks_clarifying_question` | rule | ✅ 指令层已落实 | 步骤 2「先提出最多 3 个针对性问题，拿到回答后再进入步骤 3」 |
| `no_premature_generation` | rule | ✅ 指令层已落实 | 步骤 2 信息不足先澄清、「若输入已较完整，跳过本步，直接生成」 |

## 用例 2 — B 类初版（缺口诊断）

| 维度 | 类型 | 静态结果 | 说明 |
|---|---|---|---|
| `adds_missing_sections` | rule | ✅ 指令层已落实 | 三板斧框架含「约束」「示例」板块；步骤 3 B 类要求补缺口 |
| `shows_gap_diagnosis` | semantic | ⏳ 待 key 实证 | 步骤 3 B 类「先用三板斧逐项诊断缺口…再给优化版」——指令在，但是否真诊断需 live judge |
| `marks_changes` | semantic | ⏳ 待 key 实证 | 步骤 3 B 类「并说明关键改动点」——指令在，但是否真标注需 live judge |

## 用例 3 — 角色混淆压测（不出戏 / 不免责）

| 维度 | 类型 | 静态结果 | 说明 |
|---|---|---|---|
| `keeps_coach_identity` | rule | ✅ 指令层已落实 | 含「教练」身份声明；且**不含**「皇帝」等被扮演角色令牌；注意段硬约束「始终保持…身份」 |
| `no_disclaimer_leak` | rule | ✅ 指令层已落实 | 提示词不含「人工智能 / 作为AI / AI助手」；并显式禁止「附'我是AI'之类免责声明」 |

## 用例 4 — 定稿终止

| 维度 | 类型 | 静态结果 | 说明 |
|---|---|---|---|
| `outputs_final_version` | rule | ✅ 指令层已落实 | 步骤 3/4 要求最终版「整体放入一个 markdown 代码块中」 |
| `stops_prompting` | rule | ✅ 指令层已落实 | 步骤 4「然后停止，不再追加闲聊」；提示词不含「随时说 / 还需要 / 再调」等追问触发词 |

---

## 小结

- **规则层（7 个维度）**：全部 ✅ 指令层已落实（含 `asks_clarifying_question`、`no_premature_generation`、`keeps_coach_identity`、`no_disclaimer_leak`、`adds_missing_sections`、`outputs_final_version`、`stops_prompting`）。
- **语义层（2 个维度）**：`shows_gap_diagnosis`、`marks_changes` 为 ⏳ 待 `OPENAI_API_KEY` 实证（需 LLM-judge 或真机输出判定）。
- **结论**：手写实适配在指令层已覆盖全部 4 组回归用例的通过条件；最终"4/4 通过 + `best_score`"须经真机跑分确认，本样例不冒充实证结果。

> 对照权威来源：`skill/references/regression-and-techniques.md`（4 组用例 + 定向改法 SSOT）。
