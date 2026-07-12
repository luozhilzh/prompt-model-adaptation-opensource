# B 档自优化闭环脚手架（真实外部 API）

本目录提供 `run_loop.py`：对候选提示词**真实调用目标模型**，按 `eval-spec` 评分，把评测报告喂给优化器产出下一版，循环直到 4/4 通过或轮次上限。与 `skill/references/b-tier-test-record.md` 的 WorkBuddy 内测共用同一套评测/优化逻辑，**仅把「子 Agent 执行器」换成真实 `call_model()`**。

> 诚实边界：分数来自真实模型调用，但语义层若用同模型裁判仍有自评偏差；想严谨就填 `JUDGE_MODEL` 上 C 档独立裁判。

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
# 用仓库里的原始候选跑（仓库根目录下）
python scripts/run_loop.py --candidate b_tier_test/candidate_v1.md --rounds 5

# 指定自己的用例 JSON（结构同 run_loop.py 里的 DEFAULT_CASES）
python scripts/run_loop.py --candidate my_prompt.md --cases my_cases.json --rounds 3
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
