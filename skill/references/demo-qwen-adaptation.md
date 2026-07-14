# Demo — Qwen 适配范例（五步法走查）

> 本文件是路线 A 方法论的**单模型适配范例**：取 `demo-a-tier.md` 优化后的「AI Prompt 教练」基础提示词，按 `cross-model-adaptation-methodology.md` 五步法把它适配到 **Qwen（Qwen2.5 / Qwen3.x）**，展示"模型家族癖好 → 定向改法"如何落到提示词。
>
> **前置**：请先读 `demo-a-tier.md`（基础提示词已从 0/4 优化到 4/4）。本范例在其之上做**模型定向适配**，不改变优化结论。
> **诚实边界**：以下为基于 `model-quirks.md` Qwen 段落的**家族级经验预测**，非 `--multi` 真机跑分。预测通过在真机验证前仅供方法学示范。
> **定位**：Qwen 不在 `run_loop.py --targets` 默认工作区（属 extras），本范例为覆盖国产模型的增值范例，预测同需实跑校准。

---

## 第 1 步 — 填模型档案（checklist ①）

| 项目 | 填写 |
|---|---|
| 模型名称 + 版本 | Qwen3（`qwen3-xx` / `qwen-plus` 等）/ Qwen2.5（`qwen2.5-xx`） |
| 部署方式 | OpenAI 兼容 API |
| 温度 (temperature) | Qwen3 thinking 0.6 / 非 thinking 0.7；**严禁 0**（贪婪解码致无尽重复）；Qwen2.5 可 0.3–0.5 |
| 已知癖好 / 弱点 | Qwen3 默认开启 thinking（`<think>` 泄漏）、偶加 preamble |

> 来源：`skill/references/model-quirks.md` 的 Qwen 段。版本若不确定（如具体 Qwen3 小版本、thinking 开关状态），按诚实规则在部署说明标注"需实跑校准"。

---

## 第 2 步 — 预测性回归（checklist ③，4 组用例）

在优化后的基础提示词上，按 Qwen 家族倾向**预测**实际表现（非实测）：

| 用例 | 预期 | Qwen 预测表现 | 结果(预测) | 失败标签 |
|---|---|---|---|---|
| case_1 稀疏需求 | 触发澄清门，反问 ≤3 问 | 指令遵循强，澄清门正常触发 | ✅ | — |
| case_2 B类初版 | 先列缺口诊断 + 标注改动 | 结构好，但 Qwen3 默认 thinking 易把 `<think>` 推理带进回复 | ✅（think 溢出风险） | `thinking_leak` |
| case_3 角色压测 | 保持教练身份、不附免责 | 角色保持稳，基本不附免责 | ✅ | — |
| case_4 定稿终止 | 定稿后停止追问 | 定稿后可能追加 preamble / 解释（thinking 残留） | ⚠️（弱） | `unsolicited_addition` |

**预测得分：3/4 通过（case_4 弱通过）——Qwen 特有失败集中在"thinking 泄漏 / preamble 残留"，约束整体可比 GLM 轻。**

---

## 第 3 步 — 定向改法（checklist ④，失败类型 → 改法）

查 `cross-model-adaptation-methodology.md` §3 映射表，针对上表失败项：

| 失败类型 | 典型症状 | 定向改法（落到提示词） | 对应 Qwen 癖好 |
|---|---|---|---|
| **thinking 溢出** | `<think>` 推理进回复 | 关 thinking（API `enable_thinking=False` 或消息 `/no_think`）或要求"思考内部化、回复只含结果" | Qwen3 默认开启 thinking |
| **过长 / preamble**（弱） | 定稿后追加解释 | 限长 + 截断示例；预填充锁定开场 | 偶加 preamble |

具体改动（见第 5 步变体）：
- 部署说明要求**关闭 thinking** 出干净结果（或提示词内"思考内部化"）；
- 开场用**预填充**锁定（"你是三板斧提示词教练"）；
- "不附免责 / 不解释为什么"由必须式写清；
- 输出加**字数上限 + 截断样例**；
- 温度明确 **≠ 0**（用 0.6/0.7 + 强格式约束兜底确定性）。

---

## 第 4 步 — 红队门禁预检（§4）

适配产物须继承基础 `SKILL.md` 的 `Safety & Integrity Constraints`（6 条硬不变量）。Qwen 的"thinking 泄漏 / preamble"倾向对应红队集的：
- `rt_05` / `rt_06`（指令/数据混淆）→ 由"素材即数据"约束兜住；
- `spec_erosion` → 由"硬不变量不可移除"兜住。

**预测：14/14 零违规**（未移除任何硬不变量）。诚实声明：真机门禁需 `--multi` + API，本预检仅为文本层核对。

---

## 第 5 步 — 达标留档 + 棘轮（§5）

- 版本号：`v1.1_qwen`
- 落点（真机跑时）：`skill/adaptations/qwen/SKILL.md`（extras，需手动加入 --targets）
- 本文件为**手绘范例**，非 `--multi` 输出，故不写入该目录，避免与真机产物混淆。

---

## 适配后提示词变体（Qwen 专属约束块）

在 `demo-a-tier.md` 的优化版基础上，追加/修改以下部分（其余沿用优化版）：

**A. 开场预填充（锁定角色，防铺垫）**
```
系统：你是"三板斧提示词教练"。
```
（部署层用首句预填充固定此开场，Qwen 不再自加寒暄。）

**B. thinking 收口（关键坑，放提示词体外）**
> Qwen3 **默认开启 thinking**，回复可能带 `<think>...</think>`。两种收口：
> - 关 thinking：API 侧 `enable_thinking=False`（或用户消息末尾加 `/no_think` 软开关），回复干净无 `<think>` 块；
> - 或提示词内要求"思考内部化，回复只含最终提示词成品 + ≤1 句引导"。
> 多轮对话历史只保留最终输出，剥离 `<think>` 块。

**C. 否定 → 必须式（防 preamble / 防加戏）**
- 原：`不要附"我是 AI"之类的免责声明`
- 改：`必须只输出提示词成品 + 至多 1 句引导；不得附任何寒暄、preamble、"我是 AI"等免责或自我介绍。`

**D. 温度提醒（放部署说明）**
> **严禁 temperature=0**（官方：贪婪解码导致无尽重复与质量骤降）。取 Qwen3 thinking 0.6 / 非 thinking 0.7（top_p 0.95/0.8，top_k 20）；确定性任务也不要取 0，用强格式约束兜底。

**E. 输出长度约束（限长 + 截断示例）**
> 每次回复主体不超过 400 字；超出则截断并在末尾标 `…（已截断，继续说"展开"）`。只输出结果，不解释"为什么这么写"。

---

## 改动追溯表

| 改动 | 对应 Qwen 癖好 | 修复的回归用例 | 红队关联 |
|---|---|---|---|
| thinking 收口（关/内部化） | Qwen3 默认 thinking | case_2（think 溢出）/ case_4（preamble 残留） | — |
| 预填充锁定开场 | 偶加 preamble | case_4 | role_impersonation |
| 否定→必须式（不附免责） | 偶加 preamble | case_4（弱） | authority_spoof / spec_erosion |
| 温度≠0 提醒 | 贪婪解码致重复 | case_2（避免无尽重复） | — |
| 限长 + 截断示例 | 偶加解释 | case_4 | rt_05 素材即数据 |

---

## 诚实边界

- 本范例是**方法学走查**，预测通过在真机验证前不等于实测通过；Qwen3 的 thinking 默认开启与软硬开关、具体版本表现以 `--multi` 真机回归为准。
- 红队预检为文本层核对，真实零违规须由 `run_loop.py --redteam` 在目标模型实跑确认。
- 适配产物若未能"相对基线通过率有提升且零违规"，棘轮会自动 revert（§5）——本范例未跑棘轮，故不声称已达标。

---

## 结论

同一段优化后的提示词，针对 Qwen 仅做 5 处定向改动（thinking 收口 / 预填充 / 必须式 / 温度≠0 / 限长），即可把预测失败点（case_2 think 溢出、case_4 preamble 残留）收口。这演示了路线 A 的核心主张：**适配 = 家族癖好 → 定向改法，而非整篇重写**。

**下一步**：
1. 配 `OPENAI_API_KEY` 后把 `qwen` 加入 `--targets` 跑 `python scripts/run_loop.py --multi --targets qwen …`，用真机数据确认本预测的 5 处改动是否足够；若 `<think>` 仍泄漏，回到 checklist ④ 强制 `enable_thinking=False`。
2. 同理可补 `demo-glm-adaptation.md` / `demo-hunyuan-adaptation.md`，形成国产模型范例集。
