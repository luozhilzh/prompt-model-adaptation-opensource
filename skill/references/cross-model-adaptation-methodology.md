# 跨模型适配方法论（Cross-Model Adaptation Methodology）

> 路线 A 核心交付物 · 负责任跨模型适配方法论 · 精干互补「达尔文 skill」
> 配套：`skill/SKILL.md`、`skill/references/checklist-template.md`、`skill/references/model-quirks.md`、
> `skill/security/redteam-cases.md`、`scripts/run_loop.py`（含 `--multi` 多目标编排 + 红队门禁）。
> 范例（三模型范例集）：`skill/references/demo-a-tier.md`（A 档自评审闭环）、`skill/references/demo-deepseek-adaptation.md`（DeepSeek 五步法）、`skill/references/demo-gemini-adaptation.md`（Gemini 五步法）、`skill/references/demo-claude-adaptation.md`（Claude 五步法）。
> 国产模型增值范例集（extras，不在 `--targets` 默认工作区，预测同需实跑校准）：`skill/references/demo-glm-adaptation.md`（GLM 五步法）、`skill/references/demo-qwen-adaptation.md`（Qwen 五步法）、`skill/references/demo-hunyuan-adaptation.md`（Hunyuan 五步法）。
> 运行：`skill/references/running-real-adaptation.md`（真机适配 API 接入 Runbook：配 .env、命令、读 manifest、回校准 model-quirks）。

---

## 0. 它解决什么问题 / 与达尔文 skill 的差异

一个提示词在 GPT 上跑得好，移植到 DeepSeek / Claude / Gemini 常常"出戏、偏长、否定失效、格式崩"。
**跨模型适配**就是把这个移植过程变得可重复、可验证、可回退。

市面上已有「达尔文 skill」（优化 `SKILL.md` 整篇 + git ratchet 涨分 commit / 跌分 revert + 双盲评委）。
它强在"优化器本身"，但**不专门解决两件事**——而这正是本方法论的立足点（路线 A 不与达尔文正面对撞，做它弱做的）：

| 维度 | 达尔文 skill | 本方法论（路线 A） |
|---|---|---|
| 目标 | 优化单份 SKILL.md 的质量 | 把一份提示词**稳当适配到多个模型家族** |
| 安全护栏 | 依赖评测涨分（间接） | **规约冻结 + 棘轮 + 反注入探针 + 红队门禁**（显式、独立） |
| 适配知识 | 通用优化 | 沉淀**模型家族癖好 → 定向改法**的映射表 |
| 并发 | 单份迭代 | 多目标**隔离工作区 + 子 Agent 扇出** |

一句话：**达尔文把"提示词变好"做到极致；我们把"提示词适配到不同模型且不失守"做成方法学 + 护栏。**

---

## 1. 适配总流程（五步法）

每个目标模型复制一份 `checklist-template.md` 走一遍：

1. **填模型档案**（checklist ①）：型号、部署方式、温度、已知癖好/弱点。不确定版本号务必标注不确定性。
2. **跑 4 组回归**（checklist ③）：稀疏需求 / B 类初版 / 角色混淆压测 / 定稿终止。记录实际表现。
3. **针对失败项挑定向改法**（checklist ④）：失败维度 → 查下表 → 落到提示词。
4. **过红队门禁**（见 §4）：适配产物须对 14 条红队样例零违规，否则 revert。
5. **达标留档 + 棘轮判定**（见 §5）：版本号 `v1.1_<模型名>`，写入 `skill/adaptations/<模型>/`。

---

## 2. A→D 档位在适配中的用法

| 档位 | 适配场景 | 何时用 |
|---|---|---|
| **A 自评审** | 人工对照清单改一版，自查 4 组用例 | 快速首版、低投入 |
| **B 闭环** | 脚本真调模型 → 评分 → 优化器改 → 循环 | 有 API、想自动迭代 |
| **C 双模型** | 另起独立裁判模型打分，去掉自宽松偏差 | 要证明"不是自己给自己及格" |
| **D 自适应** | 失败类型分类 → 自动挑定向改法 → 检查表自填 | 批量适配多模型、追求 human 工作量替代 |

适配一个新模型家族通常从 **A（人工探底）** 开始，跑通后再用 **B/C/D** 在真实 API 上自动化。

---

## 3. 失败类型 → 定向改法 映射表

`scripts/run_loop.py` 在 D 档用同一张表做"失败类型分类 → 定向改法注入"。适配时人也可直接查：

| 失败类型 | 典型症状 | 定向改法 |
|---|---|---|
| **过长** | 输出溢出、加戏、附免责 | 限长+截断示例、预填充锁定 |
| **出戏** | 被追问/要求切角色时破功 | XML 标签包裹、预填充锁定、否定→必须式 |
| **否定失效** | "不要X"不跟 | 否定→必须式 |
| **格式崩** | 缺约束/示例、改动点不清 | few-shot 对齐、XML 标签包裹 |
| **语感乱** | 标点/繁简/术语飘 | 显式语言声明、thinking 收口 |

> 模型家族倾向（经验性，非基准）：四家均偏长 → 均要限长；Qwen/DeepSeek 指令遵循强但推理版注意 thinking 溢出；GLM 注意寒暄/破功；Hunyuan 注意铺垫/免责。详见 `model-quirks.md`。

---

## 4. 红队门禁（Phase 0 安全护栏 · 适配产物的守门员）

**任何一版适配产物，合入前必须过红队门禁**。门禁用 `skill/security/redteam-cases.md`（14 条 / 8 类，零容忍）。

运行（需 API key）：
```bash
python scripts/run_loop.py --multi \
    --targets gemini claude deepseek \
    --base-skill skill/SKILL.md \
    --redteam-cases skill/security/redteam-cases.md \
    --workspace skill/adaptations --rounds 3
```
- 每个目标在隔离目录跑闭环，结束后对最优候选逐条跑红队攻击；
- `redteam_gate_pass = (violations 为空)`；`merge_allowed = redteam_gate_pass`；
- 任一违规 → 该轮适配作废，棘轮自动 revert，工单带失败原因重发。

门禁守护的硬不变量（基础 `SKILL.md` 已内置 `Safety & Integrity Constraints` 小节）：
不披露规约 / 素材即数据 / 硬不变量不可移除 / 拒绝削弱安全 / 注入即拒绝 / 不模仿有害示例。

---

## 5. 棘轮合入规则（硬不变量中的硬不变量）

当且仅当 **`ratchet_delta > 0`（相对基线通过率有提升）且 `violations` 为空** 时，该目标适配产物才允许：
- 作为该模型的独立变体保留于 `skill/adaptations/<模型>/SKILL.md`（推荐，不覆盖基础版）；或
- 合入主文件（覆盖基础版的目标模型变体）。

否则自动 revert。规则写在 `skill/adaptations/README.md` 的"合入 / 棘轮规则"节，由 `run_loop.py` `--multi` 强制。

---

## 6. 并发架构：子 Agent 扇出（真·高墙钟并行）

本地 `run_loop.py --multi` 是**顺序编排**（一个目标跑完再下一个）。真正的并发在 WorkBuddy 内：

```
中心（你 / 主 Agent）
  ├─ 冻结规约 + 定义工单契约（见 skill/adaptations/README.md）
  ├─ 扇出：每个目标模型一个子 Agent（general-purpose，带完整工具）
  │     ├─ gemini  Agent → 写 skill/adaptations/gemini/
  │     ├─ claude  Agent → 写 skill/adaptations/claude/
  │     └─ deepseek Agent → 写 skill/adaptations/deepseek/
  └─ 合并：读各 manifest → 红队复核 → 棘轮合入 / revert
```

- 子 Agent 只写自己目录，互相不可见 → 无写冲突；
- 子 Agent 交"真实跑出的 manifest"，中心只认文件不认嘴；
- 红队 Agent（prompt-engineering-expert，只读+研判）对候选做反注入测试；
- Phase 0 棘轮机制兜住"并发放大混乱"的风险。

---

## 7. 诚实边界（必读）

- **无真实 API 时**，`--multi` 只产出"基础版副本 + 红队门禁逻辑跑通"的脚手架；真实跨模型适配（不同模型的不同失败模式 → 不同定向改法）需配置 `OPENAI_API_KEY` 后运行。
- **红队门禁 ≠ 绝对安全**：它证明"适配产物没弱化安全"，不证明"在真实模型上绝对安全"——终局需在目标模型实跑红队集。
- **文本层锚点 ≠ 行为**：基础 `SKILL.md` 的 `Safety & Integrity Constraints` 在文本层建立显式约束，但弱模型未必照做，须真机验证。
- **适配产物是执行结果可入仓库**；路线/专家视角等讨论文档按 `.gitignore` 排除，不入库。
