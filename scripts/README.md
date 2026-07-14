# B/C/D 档自优化闭环脚手架（真实外部 API）

本目录提供 `run_loop.py`：对候选提示词**真实调用目标模型**，按 `eval-spec` 评分，把评测报告喂给优化器产出下一版，循环直到 4/4 通过或轮次上限。与 `skill/references/tier-tests/b_tier_test_record.md` / `references/tier-tests/c_tier_test_record.md` / `references/tier-tests/d_tier_test_record.md` 的 WorkBuddy 内测共用同一套评测/优化逻辑，**仅把「子 Agent 执行器」换成真实 `call_model()`**。

> **档位说明**：不填 `JUDGE_MODEL` 即 **B 档（自裁判）**——执行器 / 裁判 / 优化器同模型；填了 `JUDGE_MODEL`（或传 `--judge-model`，且与 `MODEL` 不同）即 **C 档（双模型 / 独立裁判）**——执行器留 `MODEL` 测真实表现，裁判 + 优化器走独立模型，消除自评宽松；加 `--d-mode` 即 **D 档（自适应）**——在 C 档之上自动分类失败类型、注入定向改法、跑完自填检查表。详见第 7、8 节。

> 诚实边界：B 档分数来自真实调用但语义层同模型裁判仍有自评偏差；C 档用独立模型裁判可消去该偏差，但成本更高（多一次模型调用 / 轮）；D 档的"自适应替代人工"需跨家族 `JUDGE_MODEL` + 足量 unseen 集才成立，仅针对已知 4 组优化会过拟合。

## 1. 安装依赖

```bash
pip install openai python-dotenv
```

## 2. 配置

```bash
cp .env.example .env
# 编辑 .env，填入 OPENAI_API_KEY / BASE_URL / MODEL
# JUDGE_MODEL 可选（C 档独立裁判）
```

`BASE_URL` 与 `MODEL` 按你的服务商填（DeepSeek / GLM / Qwen / 混元 等 OpenAI 兼容地址见 `.env.example` 注释）。

## 3. 运行

```bash
# B 档（自裁判）：只填 MODEL，裁判/优化器同模型
python scripts/run_loop.py --candidate tier_test_candidates/candidate_v1.md --rounds 5

# 指定自己的用例 JSON（结构同 run_loop.py 里的 DEFAULT_CASES）
python scripts/run_loop.py --candidate my_prompt.md --cases my_cases.json --rounds 3

# C 档（双模型/独立裁判）：--judge-model 填不同于 MODEL 的模型
#   执行器=目标模型(如 DeepSeek)，裁判+优化器=独立模型(如 gpt-4o)
python scripts/run_loop.py --candidate tier_test_candidates/candidate_v1.md \
    --judge-model gpt-4o --rounds 5
```

## 4. 输出（默认 `scripts/output/`）

| 文件 | 内容 |
|---|---|
| `candidate_roundN.md` | 第 N 轮的候选提示词 |
| `report_roundN.json` | 第 N 轮逐用例评分（维度、分数、失败标签、模型原始输出） |
| `best_candidate.md` | 最高分版本的候选（未必是最后一轮） |
| `history.json` | 每轮通过率与报告，便于画分数曲线 |

## 5. 循环逻辑

```
候选 = --candidate
for 轮次 in 1..N:
    输出 = 对每条用例 call_model(候选, 用例输入)
    报告 = 规则层(零成本) + 语义层(LLM-judge) 评分
    存 candidate_roundN.md / report_roundN.json
    若 4/4 通过 → 停
    候选 = 优化器(候选, 报告)   # 解析代码块里的改进版
输出 best_candidate.md + history.json
```

停止条件：4/4 通过 **或** 到 `--rounds` 上限 **或** 优化器未产出有效改动（防空转）。

## 6. 防坑提醒（与内测一致）

- **自评偏差**：语义层同模型裁判偏宽松 → 填 `JUDGE_MODEL` 上 C 档。
- **防过拟合**：默认只用内置 4 组；最终验收应补 unseen 集（输入不同、结构同）。
- **成本**：每轮 ≈ 4 次执行 + 语义 judge 调用 + 1 次优化；控制 `--rounds`。
- **非确定性**：固定 `temperature`（脚本默认 0.4/0.0）以便复现。
- **解析脆弱**：优化器输出靠正则取最后一个代码块作为改进版；若你的模型输出格式异常，调 `_extract_code_block`。

## 7. C 档（独立裁判 / 双模型）

C 档是 B 档的升级：**把"裁判 + 优化器"从目标模型拆到独立模型**，只留执行器在目标模型上（因为候选提示词必须真跑在目标模型才能测出适配效果）。

### 模型分配

| 角色 | B 档 | C 档 |
|---|---|---|
| 执行器（跑候选提示词） | `MODEL` | `MODEL`（目标模型） |
| 裁判（语义层 LLM-judge） | `MODEL` | `JUDGE_MODEL`（独立） |
| 优化器（产下一版） | `MODEL` | `JUDGE_MODEL`（独立） |

### 怎么开 C 档

两种方式任选其一（效果相同）：

```bash
# 方式一：环境变量（.env 里填 JUDGE_MODEL）
JUDGE_MODEL=gpt-4o        # 与 MODEL 不同即进入 C 档

# 方式二：命令行参数（覆盖环境变量）
python scripts/run_loop.py --candidate tier_test_candidates/candidate_v1.md \
    --judge-model gpt-4o --rounds 5
```

启动时脚本会打印档位：
```
档位：C（双模型·独立裁判） ｜ 执行器(MODEL)=deepseek-chat ｜ 裁判/优化器(JUDGE_MODEL)=gpt-4o
```

### 与 WorkBuddy 内测的关系（诚实边界）

- `references/tier-tests/c_tier_test_record.md` 在 WorkBuddy 内用「blind 裁判子 Agent（不读候选）」模拟 C 档，证明**方法论可跑通**（角色隔离的裁判能正确运行）。
- 但 WorkBuddy 内执行器 / 裁判 / 优化器同属一个模型家族，"独立"只是**结构独立**，**无法证实"独立裁判更严/更稳"**。
- 真正的偏差消除，必须由本脚手架填**跨家族**的 `JUDGE_MODEL`（如执行器 DeepSeek、裁判 GPT/Claude）来成立——这才是 README 里"C 档分数比 B 档更严格、波动更小"所指的真·双模型场景。

## 8. D 档（自适应 · 失败类型驱动定向改法 + 检查表自填）

D 档 = C 档（独立裁判）之上加一层**自动化适配链**：把评测里的失败维度自动归类为 5 类失败类型，按速查表给优化器推荐定向改法，跑完把检查表"实际"列自动填实。

### 怎么开 D 档

```bash
# 建议配 --judge-model（独立裁判）一起开，避免自用自评
python scripts/run_loop.py --candidate tier_test_candidates/candidate_v1.md \
    --judge-model gpt-4o --d-mode --rounds 5

# 指定自动填实的检查表输出路径（默认 output/checklist_auto.md）
python scripts/run_loop.py --candidate tier_test_candidates/candidate_v1.md \
    --judge-model gpt-4o --d-mode --checklist my_checklist.md --rounds 5
```

### D 档自动做了什么

| 步骤 | 行为 | 来源 |
|---|---|---|
| 失败类型分类 | 把每条失败维度映射到 `过长 / 出戏 / 否定失效 / 格式崩 / 语感乱` | 脚本内 `FAILURE_TYPE_MAP`（对应 `eval-spec` 维度 key） |
| 定向改法推荐 | 按类型查 `regression-and-techniques.md` 速查表，给出 1–2 个手法（如 `过长` → 限长+截断示例） | 脚本内 `TECHNIQUE_MAP` |
| 优化器增强 | 把"失败类型诊断 + 定向改法建议"拼进优化器 prompt（用 `_OPTIMIZER_SYSTEM_D`），要求优先用推荐药方 | 见文件顶部说明 |
| 检查表自填 | 达标轮后自动生成 `checklist_auto.md`，按 `checklist-template.md` 结构填实「实际」列与「结果」勾选 | `generate_checklist()` |

启动时每轮会打印分类结果，例如：
```
[D 档分类] case_1:过长→限长+截断示例+预填充锁定; case_4:过长→限长+截断示例+预填充锁定
```

### 与 WorkBuddy 内测的关系（诚实边界）

- `references/tier-tests/d_tier_test_record.md` 在 WorkBuddy 内用「失败类型分类 → 定向改法 → 检查表自填」跑通闭环（通过率 2/4 → 3/4 → 4/4）。
- 但 WorkBuddy 内执行器 / 裁判 / 优化器同家族，且**无真实跨模型漂移数据**——分类器只在已知 4 组上贴标签，检查表是**回填结论**而非 D 档**自主发现**新约束。
- 要验证"自适应替代人工适配"，必须用本脚手架 `--d-mode` 配**跨家族** `JUDGE_MODEL` + **足量 unseen 用例集**（输入不同、结构同）一起跑：只针对已知 4 组优化会过拟合，那不是真自适应。
- 已知局限：分类器只认"输出表现"，认不出"门控逻辑配置错误"（如澄清门过触发会被误归"格式崩"），需优化器自行识别修复。

---

## 9. 中心合入评审与落盘（§6，真机跑完 --multi 后）

`--multi` 跑完所有目标后，各 `skill/adaptations/<target>/` 已有 `SKILL.md` + `adaptation_manifest.json`。方法学 §6 的「中心」负责把这些扇出结果合入主文件，工具已就位（离线、无需 key）：

- `scripts/merge_candidates.py --root skill/adaptations --out skill/adaptations/_merged/merged_review.json`：套红队门禁 + 棘轮规则，逐目标判 `merge / revert`，产出 `merged_review.json`。
- `scripts/apply_merge.py --review ...`：对 `verdict=merge` 目标生成独立变体 SKILL.md（默认仅 `_merged/` 草稿；`--apply` 提升各子目录；`--apply-main --target X` 覆盖主 `skill/SKILL.md` 且自动备份）。

完整流程与诚实边界见 `skill/references/running-real-adaptation.md` §11。
