# B 档外部 API 自优化闭环脚手架 — 交付说明

> 本文档配合 **本仓库本批次提交** 阅读，说明这次「新增 B 档真·外部 API 脚手架」都交付了什么、怎么设计的、和此前 WorkBuddy 内测是什么关系、以及如何运行。
> 适用读者：想复用这套闭环、或想复现/验收本批次改动的人。

---

## 1. 交付内容

本批次新增 / 变更的文件如下：

| 类别 | 文件 | 说明 |
|---|---|---|
| 新增 | `scripts/run_loop.py` | B 档主循环脚手架（约 330 行，纯 Python，零框架）。真实调用目标模型跑「执行 → 评分 → 优化」闭环，达 4/4 或轮次上限即停。 |
| 新增 | `scripts/.env.example` | 配置模板。含 `OPENAI_API_KEY` / `BASE_URL` / `MODEL` / `JUDGE_MODEL`，并附 DeepSeek、智谱 GLM、通义千问、腾讯混元 的 OpenAI 兼容地址注释。 |
| 新增 | `scripts/README.md` | 脚手架独立使用说明（依赖、配置、运行、输出、循环逻辑、防坑）。 |
| 变更 | `README.md` | ① 目录树新增 `scripts/` 一节；②「自优化演进」章节补 B 档外部 API 说明与诚实边界；③ 现状标注更新为「B 档双重实现已就绪」。 |
| 关联（既有，本批次未改） | `skill/references/eval-spec.md`、`optimizer-meta-prompt.md`、`b-tier-test-record.md`、`b_tier_harness.md`、`b_tier_test/candidate_v1.md`、`candidate_v2.md` | 用例、优化器、内测记录与产物——本脚手架与它们共享同一套逻辑与证据。 |

**诚实边界重申**：本批次交付的是 **脚手架 + 内测证据**，不是跨模型的基准成绩。分数来自真实模型调用，但若语义层用同模型自评仍有偏差；要严谨请填 `JUDGE_MODEL` 上 C 档独立裁判（已在代码中预留）。

---

## 2. 设计要点

`run_loop.py` 的设计遵循「可替换执行器、可复用评分/优化、诚实可复现」三原则：

1. **执行器可替换**
   内测用 WorkBuddy 子 Agent 当执行器；本脚手架把执行器换成标准 `call_model(system, user)` —— 一个 OpenAI 兼容的 `chat.completions.create` 封装（`system=候选提示词`，`user=用例输入`）。其余逻辑不变，因此内测跑通的结论可直接迁移到真实模型。

2. **OpenAI 兼容协议**
   通过 `BASE_URL` + `MODEL` 适配主流国产模型（DeepSeek / GLM / Qwen / 混元），不绑定任何一家。换模型只改 `.env`，不动代码。

3. **规则层 + 语义层双评分**
   - **规则层**（零成本）：正则/结构判定能判的先判（反问数 ≤3、无成品代码块、自称教练非皇帝、无免责串词、补了约束+示例等）。见 `rule_pass()`。
   - **语义层**（LLM-judge）：`shows_gap_diagnosis`、`marks_changes` 这类无法纯规则判定的维度，交给裁判模型打 0–1 分。见 `semantic_score()`。
   - 每个维度带 `weight`，加权求和得单用例分；规则能判的绝不调模型，省成本。

4. **优化器复用已有模板思路**
   `_OPTIMIZER_SYSTEM` 与 `skill/references/optimizer-meta-prompt.md` 同源：吃「候选 + EVAL_REPORT」，输出「改动日志 + 改进版代码块」。解析时取最后一个 markdown 代码块作为下一版候选（`_extract_code_block`）。

5. **主循环与停止条件**
   ```
   候选 = --candidate
   for 轮次 in 1..N:
       输出   = 对每条用例 call_model(候选, 用例输入)
       报告   = 规则层 + 语义层评分（含失败标签）
       存档   = candidate_roundN.md / report_roundN.json
       if 4/4 通过 → 停止
       候选   = 优化器(候选, 报告)
   输出 best_candidate.md + history.json（取最高分轮，未必是最后一轮）
   ```
   停止条件有三：① 4/4 通过；② 到 `--rounds` 上限；③ 优化器未产出有效改动（防空转）。

6. **C 档预留位**
   `JUDGE_MODEL` 留空则语义层同 `MODEL` 自评；填入另一模型即升级为 C 档独立裁判，消除自评宽松偏差——**同一份代码、一个环境变量切换档位**。

7. **可复现与诚实**
   执行温度固定（执行 0.4 / 裁判 0.0）；每轮产出报告 JSON（含模型原始输出）便于审计；`history.json` 可画分数曲线。代码含清晰 TODO 与默认值，按你的 API 微调即可。

---

## 3. 与内测的关系

本脚手架是 WorkBuddy 内测的**对等实现（external 版）**，不是另一套东西。

| 维度 | WorkBuddy 内测（`b-tier-test-record.md`） | 本脚手架（`scripts/run_loop.py`） |
|---|---|---|
| 执行器 | WorkBuddy 子 Agent（读候选文件当角色设定） | 真实 `call_model()`（OpenAI 兼容 API） |
| 评分器 | 主模型按 `eval-spec` 打分 | `rule_pass()` + `semantic_score()`，逻辑同源 |
| 优化器 | `optimizer-meta-prompt.md` 模板 | `_OPTIMIZER_SYSTEM`，同源 |
| 用例 | 内置 4 组（稀疏需求/B类初版/角色压测/定稿终止） | `DEFAULT_CASES`，结构同 eval-spec，可 `--cases` 替换 |
| 结论 | 同一候选 1/4 → 4/4，闭环机制可跑通 | 对真实目标模型跑同一闭环，逻辑一致 |

**内测给了三件东西，本批次把它"落地成可复用代码"：**

- **机制验证**：内测已证明「评测报告 → 优化器」闭环能把回归通过率从 1/4 拉到 4/4，且每次改动可追溯至失败标签（非瞎改）。本脚手架把这个机制做成脚本，任何人填 key 即可复现。
- **坑的对应处理**：内测踩的 7 个坑，本脚手架做了对应：
  - *同模型自评偏差* → 预留 `JUDGE_MODEL` 上 C 档。
  - *空转* → 优化器未产出有效改动即停。
  - *解析脆弱* → `_extract_code_block` 取最后一个代码块，并提示异常时改这里。
  - *非确定性* → 固定温度。
  - *防过拟合* → 默认只用内置 4 组，文档提示最终验收补 unseen 集。
  - *多轮用例拼接* / *子 Agent 隔离* → 内测需手动拼多轮、子 Agent 自带系统提示；外部版因真实 API 有对话上下文，这部分后续可接对话历史（已在代码中留可扩展点）。
- **诚实标注延续**：内测明确"分数是纵向对比（v1 vs v2），非跨模型基准"；本脚手架 README 与本文档同样标注，不把经验当结论。

一句话：**内测负责"证明能跑通"，本脚手架负责"让你也能跑"**，两套共享 `eval-spec` 与优化器逻辑，仅执行器不同。

---

## 4. 运行方式

### 4.1 安装依赖

```bash
pip install openai python-dotenv
```

### 4.2 配置

```bash
cd scripts
cp .env.example .env
# 编辑 .env，至少填 OPENAI_API_KEY / BASE_URL / MODEL
# JUDGE_MODEL 可选（填了即 C 档独立裁判）
```

`.env.example` 已注释好常见服务商的 `BASE_URL`：

| 服务商 | BASE_URL |
|---|---|
| OpenAI | `https://api.openai.com/v1` |
| DeepSeek | `https://api.deepseek.com/v1` |
| 智谱 GLM | `https://open.bigmodel.cn/api/paas/v4` |
| 通义千问 | `https://dashscope.aliyuncs.com/compatible-mode/v1` |
| 腾讯混元 | `https://api.hunyuan.cloud.tencent.com/v1` |

### 4.3 运行

在**仓库根目录**下执行（候选路径相对根目录）：

```bash
# 用仓库里的原始候选跑，最多 5 轮
python scripts/run_loop.py --candidate b_tier_test/candidate_v1.md --rounds 5

# 用你自己的候选 + 自定义用例
python scripts/run_loop.py --candidate my_prompt.md --cases my_cases.json --rounds 3

# 产物输出到自定义目录
python scripts/run_loop.py --candidate b_tier_test/candidate_v1.md --out my_output
```

### 4.4 输出（默认 `scripts/output/`）

| 文件 | 内容 |
|---|---|
| `candidate_roundN.md` | 第 N 轮的候选提示词 |
| `report_roundN.json` | 第 N 轮逐用例评分（维度、分数、失败标签、模型原始输出） |
| `best_candidate.md` | 最高分版本候选（未必是最后一轮） |
| `history.json` | 每轮通过率与报告，便于画分数曲线 |

### 4.5 预期

- 用 `b_tier_test/candidate_v1.md`（原始提示词）跑，通常第 1 轮 1/4，经 1–2 轮优化达 4/4 停止——与内测记录一致。
- 若想验证 C 档去偏效果：填 `JUDGE_MODEL` 为另一模型，重跑，对比分数严格度/波动。

---

## 5. 本批次提交范围小结

- **新增**：`scripts/run_loop.py`、`scripts/.env.example`、`scripts/README.md`
- **变更**：`README.md`（目录树 + B 档外部 API 说明 + 现状标注）
- **关联未改**：`skill/references/*`、`b_tier_test/*`（本批脚手架与之共享逻辑）

> 建议单独提交本批次，提交信息可参考：`feat: 新增 B 档外部 API 自优化闭环脚手架（scripts/run_loop.py）`。
