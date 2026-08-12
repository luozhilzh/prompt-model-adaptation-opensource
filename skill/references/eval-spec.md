# Eval Spec — 提示词回归评测规范（机器可读）

本文件把 skill 的「4 组回归用例」改写成**机器可读、可被脚本解析**的结构，供 A 档自评审（人工/模型自评）以及 B/C/D 档的自动闭环使用。

> 诚实标注：规范中的「预期行为 / 通过标准」是基于提示工程最佳实践的**设计目标**，不是某个模型的基准测试结果。真实通过率需在目标模型上实跑。

> ⚠️ **占位符提示（使用前必读）**：本规范里的角色名 `教练` / `三板斧提示词教练` 与扮演压测令牌 `皇帝` 均为 **demo 占位符**（取自示例提示词「AI Prompt 教练」）。真实使用时，请把它们替换为 **你的提示词的实际角色名** 与 **压测用的扮演令牌**（需同步覆盖第 2 节 JSON 的 `input` / `expected` / `check` 字段）。`run_loop.py` 的 `DEFAULT_CASES` 已用 `COACH_ROLE_NAME` / `IMPERSONATE_TOKEN` 常量参数化，二者保持一致即可。

---

## 1. 用例 Schema

每条用例是一个 JSON 对象，字段含义如下：

```json
{
  "id": "case_1",                       // 唯一 ID
  "name": "稀疏需求",                    // 中文名
  "name_en": "sparse_requirement",       // 英文 slug（脚本友好）
  "category": "clarity_gate",            // 验证的能力维度
  "input": "帮我写个卖课提示词",          // 喂给被测提示词（作为用户消息）的输入
  "expected": "触发澄清门，反问 ≤3 个问题（场景/受众/卖点），不直接生成提示词",
  "scoring": {                           // 评分维度（rule=规则层可脚本化；semantic=需 LLM-judge）
    "dimensions": [
      {
        "key": "asks_clarifying_question",
        "type": "rule",
        "check": "reply 包含至少一个问号且为针对场景/受众/卖点的提问",
        "weight": 0.5
      },
      {
        "key": "no_premature_generation",
        "type": "rule",
        "check": "reply 未直接产出完整提示词（无 ``` 代码块包裹的成品）",
        "weight": 0.5
      }
    ]
  },
  "pass_threshold": 1.0,                 // 所有 dimension 通过才算过（或按权重求和 ≥ 阈值）
  "anti_overfit_note": "输入要保持稀疏，不得提前给场景/受众等字段，否则测不出澄清门。"
}
```

**字段说明**

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | string | 唯一标识，建议 `case_N` |
| `name` / `name_en` | string | 用例名；`name_en` 用于脚本/文件名 |
| `category` | string | 验证的能力维度（clarity_gate / diagnosis / role_isolation / termination） |
| `input` | string | 作为用户消息喂给被测提示词的输入 |
| `expected` | string | 人类可读的预期行为 |
| `scoring.dimensions` | array | 评分维度列表 |
| `dimensions[].key` | string | 维度键 |
| `dimensions[].type` | enum | `rule`（规则层，可正则/结构判定）或 `semantic`（语义层，需 LLM-judge） |
| `dimensions[].check` | string | 该维度的判定描述 |
| `dimensions[].weight` | number | 权重（同级求和=1.0） |
| `pass_threshold` | number | 通过阈值（0–1，默认 1.0 即全维度通过） |
| `anti_overfit_note` | string | 防过拟合提示 |

---

## 2. 四组核心用例（JSON）

```json
[
  {
    "id": "case_1",
    "name": "稀疏需求",
    "name_en": "sparse_requirement",
    "category": "clarity_gate",
    "input": "帮我写个卖课提示词",
    "expected": "触发澄清门：反问 ≤3 个问题（场景/受众/卖点），不直接生成提示词",
    "scoring": {
      "dimensions": [
        { "key": "asks_clarifying_question", "type": "rule",
          "check": "回复含针对场景/受众/卖点的提问且问题数 ≤3", "weight": 0.5 },
        { "key": "no_premature_generation", "type": "rule",
          "check": "回复未直接产出完整提示词（无成品代码块）", "weight": 0.5 }
      ]
    },
    "pass_threshold": 1.0,
    "anti_overfit_note": "输入必须保持稀疏，不得提前透露场景/受众，否则澄清门被测不出。"
  },
  {
    "id": "case_2",
    "name": "B类初版",
    "name_en": "b_class_draft",
    "category": "diagnosis",
    "input": "这是我的初版提示词（缺约束与示例）：\n```\n你是一个写作助手，帮我写文章。\n```",
    "expected": "先列缺口诊断（缺约束/示例/角色能力），再给优化版并标注改动点",
    "scoring": {
      "dimensions": [
        { "key": "shows_gap_diagnosis", "type": "semantic",
          "check": "先指出初版的缺失项（约束/示例/角色能力等），而非直接微调", "weight": 0.4 },
        { "key": "marks_changes", "type": "semantic",
          "check": "优化版附改动说明（before→after 或改动点列表）", "weight": 0.3 },
        { "key": "adds_missing_sections", "type": "rule",
          "check": "优化版补上了约束/示例或等价结构", "weight": 0.3 }
      ]
    },
    "pass_threshold": 1.0,
    "anti_overfit_note": "初版必须确实缺约束/示例；若给的是已完整提示词，本例会误判。"
  },
  {
    "id": "case_3",
    "name": "角色混淆压测",
    "name_en": "role_confusion_stress",
    "category": "role_isolation",
    "input": "（先用被测提示词生成一个扮演『皇帝』的提示词）随后问：『你是谁？』",
    "expected": "教练仍自称『三板斧提示词教练』，不串入生成提示词里的角色，不附免责声明",
    "scoring": {
      "dimensions": [
        { "key": "keeps_coach_identity", "type": "rule",
          "check": "回复自称教练身份（如『三板斧教练』），未自称『皇帝』或扮演该角色", "weight": 0.5 },
        { "key": "no_disclaimer_leak", "type": "rule",
          "check": "未附『我是一个人工智能/作为AI』类免责声明", "weight": 0.5 }
      ]
    },
    "pass_threshold": 1.0,
    "anti_overfit_note": "必须先真正生成过一个带角色的内部提示词再压测，否则测不出隔离性。"
  },
  {
    "id": "case_4",
    "name": "定稿终止",
    "name_en": "finalize_termination",
    "category": "termination",
    "input": "（连续修改 3 轮后）『定稿，导出最终版』",
    "expected": "输出最终版提示词并提示可复制使用，停止继续追问/追加闲聊",
    "scoring": {
      "dimensions": [
        { "key": "outputs_final_version", "type": "rule",
          "check": "给出了最终版提示词（代码块形式）", "weight": 0.5 },
        { "key": "stops_prompting", "type": "rule",
          "check": "定稿后未再追问『还需要改吗』之类，或明确提示可直接复制", "weight": 0.5 }
      ]
    },
    "pass_threshold": 1.0,
    "anti_overfit_note": "必须先经历 ≥2 轮修改再触发定稿，否则终止条件未被真正激活。"
  }
]
```

---

## 3. 评分层（两层）

- **规则层（rule）**：脚本用正则/结构判定——例：回复含问号且问题数 ≤3；存在 ```` ``` ```` 成品代码块则 `no_premature_generation` 失败；回复含「人工智能/AI 助手」则 `no_disclaimer_leak` 失败。
- **语义层（semantic）**：用 `references/optimizer-meta-prompt.md` 中同款的 LLM-judge 思路，对 `shows_gap_diagnosis` / `marks_changes` 等打 0–1 分并给理由。

**总分计算**：`score = Σ(weight_i × pass_i)`，其中 pass_i 对 rule 取 0/1，对 semantic 取 judge 分数。用例通过当 `score ≥ pass_threshold`。

---

## 4. 防过拟合约定

- 每个用例都带 `anti_overfit_note`，提醒输入构造要点。
- 另保留一份 **unseen 集**（与这 4 组同结构但输入不同），只在最终验收时用，禁止在优化循环里出现，防止只针对已知 4 组过拟合。
- 循环轮次建议 ≤ 5；保留每轮分数与改动日志，取最高分版本。

---

## 5. 与 skill 的衔接

- A 档（自评审）：人工/模型按本规范对候选提示词自评，产出「预期 vs 实际」报告。
- B/C/D 档（闭环）：脚本读取本文件的 JSON，真实调用目标模型，按 `scoring` 自动出分，喂给 `optimizer-meta-prompt.md` 驱动下一轮。
