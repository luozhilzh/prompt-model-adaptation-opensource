# prompt-model-adaptation

一套可复用的 **提示词优化 + 跨模型适配** 方法论，打包成开源资源，可在 WorkBuddy、Cursor、Claude Code、Codex、以及任意支持长指令的 AI 工具里使用。

核心思想：**把"主观感受词"换成"可验证的动作与标准"**，并堵住两个最容易让提示词跑偏的坑——信息不足直接生成、以及角色混淆 / 上下文泄漏；再把优化后的提示词按目标模型的家族癖好做定向适配，用 4 组回归用例验证不引入回归。

> ⚠️ 免责声明：本仓库中所有「模型家族癖好 / 预测风险」均为**经验性归纳，非基准测试**。具体版本请以你在真实模型上跑回归的「实际」结果为准；未知版本号（如 GLM5.2 / Qwen3.7 / hy3）务必标注不确定性。

---

## 目录结构

```
prompt-model-adaptation-opensource/
├── LICENSE                                # MIT 许可证文本
├── README.md                              # 本文件：使用说明
├── SOP.md                                 # 纯文本 SOP（合并 4 文件、去 frontmatter），可直贴任意 AI 工具
├── skill/                                 # WorkBuddy 原生 skill（带 frontmatter，给 WorkBuddy 用户）
│   ├── SKILL.md
│   └── references/
│       ├── checklist-template.md         #   可填写的 6 区块适配检查表
│       ├── regression-and-techniques.md  #   4 组回归用例 + 定向改法速查
│       ├── model-quirks.md               #   各模型家族癖好与适配要点
│       └── 模型适配横向对比.md           #   多模型适配差异横向对比表
└── formats/                               # 跨工具格式转换（各自独立可用）
    ├── cursor-prompt-model-adaptation.mdc   # Cursor Rule（.mdc）
    ├── claude-code-prompt-model-adaptation.md  # Claude Code 命令
    └── codex-AGENTS.md                     # Codex / Agents 指引（AGENTS.md 风格）
```

---

## 工作流概览（4 步）

1. **诊断与优化**：找反模式（主观形容词、缺成功标准、角色混淆、无澄清门、无终止条件、格式不一致），给 before→after 对照并附理由。
2. **生成适配检查表**：复制检查表，填目标模型档案（名称 / 部署方式 / 温度 / 已知癖好）。
3. **适配到目标模型**：填 5 维度 + 4 组回归的*预测*风险，套用定向改法，产出「可直接复制的系统提示词 + 部署须知」。未知版本号须标注不确定性。
4. **回归验证**：在真实模型上跑 4 组用例，填「实际」列。漂移则回改法表补刀。4/4 通过 + 偏差清零即达标。

---

## 优化风格与原理

![提示词优化生命周期：风格与原理](assets/style-principle-method.svg)

### 风格：工程化、结构化、可复现（不是"措辞玄学"）

| 风格特征 | 具体表现 |
|---|---|
| 诊断驱动 | 不急着写，先找反模式、打风险等级（高/中/低），再动手 |
| 对照式交付 | 每条改动都是 `改动前 → 改动后 + 理由`，不是只甩一个成品 |
| 以"可验证"为唯一标尺 | 每条建议都能回答"怎么算做对了"，而非"感觉更好了" |
| 版本化、防漂移 | 每个模型一份适配版，互不覆盖，方便横向对比 |
| 诚实标注 | 预测风险明确写"未实测"，不把经验当结论 |

### 原理：用可验证约束替代主观感受

**核心原理只有一条：把「主观感受」换成「可验证的动作 + 标准」。**

原始提示词的问题几乎都源于"靠模型自由发挥"——形容词无锚点、成功标准缺失、角色边界模糊。优化的本质就是**用约束替代模糊**，让模型每一步都有明确边界。围绕这条核心，派生出 6 条可操作原理：

1. **模糊 → 可验证（核心）**：「更好」→ 5 条可勾选自检清单；「谐趣」→ 1–2 句 + 明确询问。每个形容词都要有对应动作。
2. **角色与上下文隔离**：消除"双初始化"歧义（生成提示词内的角色 vs 教练自身），切断角色混淆与上下文泄漏——这是稳定性最大的隐患。
3. **澄清门 + 终止条件**：信息不足先问 ≤3 个问题再生成（防跑偏）；用户满意即定稿（防无限循环）。把开环变成有进出口的闭环。
4. **模型差异维度化**：把"哪个模型表现差"拆成 5 个可测维度——指令遵循 / 结构化敏感度 / 角色保持 / 输出长度 / 中文语感，再映射到定向改法（否定→必须式、XML 包裹、限长、few-shot、预填充）。
5. **回归验收闭环**：4 组用例跑「预期 vs 实际」，偏差清零才算完成。让"优化"从艺术变成可验收的工程。
6. **经验诚实化**：模型癖好是公开经验归纳，不是基准测试——所以检查表留"实际"空白待你实测，避免误导。

> 一句话总结：**风格 = 系统化的「诊断 → 对齐标准 → 适配 → 验收」流水线；原理 = 用可验证约束替代主观感受，并针对模型族弱点做定向加固。** 它不追求"一句话让 AI 质变"的神话，而是把提示词当作可测试、可移植、可版本化的工程产物来对待。

---

## 用法一：WorkBuddy（原生 skill）

把 `skill/` 目录整体复制到你的用户级 skills 目录：

```bash
# 复制后路径应为：
#   ~/.workbuddy/skills/prompt-model-adaptation/SKILL.md
#   ~/.workbuddy/skills/prompt-model-adaptation/references/*.md
cp -r skill ~/.workbuddy/skills/prompt-model-adaptation
```

之后在任意对话中说：
- 「优化这段提示词」→ 触发 Step 1
- 「适配成 DeepSeek / GLM / Qwen / 混元」→ 触发 Step 2–3
- 「给我个模型适配检查表」→ 触发 Step 2
- 「校验这个提示词稳不稳」→ 触发 Step 4

也可手动输入 `/prompt-model-adaptation` 或「用 prompt-model-adaptation skill 看这段」。

---

## 用法二：任意 AI 工具（纯文本 SOP）

直接把 `SOP.md` 全文复制粘贴进对话 / 项目说明 / 知识库，当作一份 SOP 文档投喂即可。任何支持长指令的 agent（Claude / GPT / 通义 / 豆包 …）都能照做。

---

## 用法三：Cursor

把 `formats/cursor-prompt-model-adaptation.mdc` 放到项目（或用户级）的 Cursor rules 目录：

```bash
# 项目级
mkdir -p .cursor/rules && cp formats/cursor-prompt-model-adaptation.mdc .cursor/rules/

# 用户级（全局）
# macOS/Linux: ~/.cursor/rules/
# Windows:     %USERPROFILE%\.cursor\rules\
```

规则带 `description` + `globs`，Cursor 会在涉及 `*.prompt.md` / `prompts/**` / `*system*prompt*` 等文件或相相关对话时自动匹配；也可在设置里手动启用。

---

## 用法四：Claude Code

把 `formats/claude-code-prompt-model-adaptation.md` 放到 Claude Code 的命令目录（文件名即命令名）：

```bash
# 项目级
mkdir -p .claude/commands && cp formats/claude-code-prompt-model-adaptation.md .claude/commands/prompt-model-adaptation.md

# 用户级（全局）
# ~/.claude/commands/prompt-model-adaptation.md
```

之后在 Claude Code 里输入：

```
/prompt-model-adaptation <这里贴你要优化/适配的提示词>
```

命令文件内含 `$ARGUMENTS` 占位，会自动接收你贴入的提示词并按工作流处理。

---

## 用法五：Codex / 通用 Agents

把 `formats/codex-AGENTS.md` 放到仓库根目录（或重命名为 `AGENTS.md`）：

```bash
cp formats/codex-AGENTS.md AGENTS.md
```

Codex 与多数 coding agent 会自动加载仓库根目录的 `AGENTS.md` 作为 agent 指引；涉及提示词优化 / 适配的任务会按其中工作流执行。

---

## 4 组回归用例（适配是否完成的判定）

| 用例 | 输入 | 预期 |
|---|---|---|
| 1 稀疏需求 | 一句模糊需求（如「帮我写个卖课提示词」） | 触发澄清，先问 ≤3 问，不直接生成 |
| 2 B 类初版 | 一段缺「约束/示例」的初版提示词 | 先诊断缺口，再给优化版并标注改动点 |
| 3 角色混淆压测 | 生成提示词扮演角色后问「你是谁」 | 教练仍自称原身份，不串角色 |
| 4 定稿终止 | 连改 3 轮后说「定稿」 | 输出最终版并提示可复制，不再追问 |

4/4 通过 + 偏差清零 = 适配完成，写版本号归档（建议 `v1.1_模型名`），**不覆盖原版**。

---

## 许可与贡献

- 本仓库以 MIT 许可证开源，许可证文本见根目录 `LICENSE` 文件；允许自由使用、修改、分发，请保留版权与许可声明。
- 欢迎提交 Issue / PR 补充更多模型家族的癖好与回归用例。
- 维持「经验性归纳，非基准测试」的诚实标注：任何具体版本的断言都应来自真实回归，而非推测。
