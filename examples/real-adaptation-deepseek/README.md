# real-adaptation-deepseek/ — 手写实适配样例（模板）

> 🟢 **REAL (hand-authored) · 非 STUB · 非 empirical**
> - **REAL**：`deepseek/adapted_prompt.md` 是**真实手写**的 DeepSeek 适配提示词（取自作者真实部署经验），不是桩模型伪造。
> - **非 STUB**：与 `../simulated-adaptations/`（桩伪造）区分，可当"成品长啥样"的真实参照。
> - **非 empirical**：**未经** `run_loop.py --multi` 真机跑分，无 `best_score` / 红队 `violations`。指令层自检见 `deepseek/regression_selfcheck.md`；实证升级见下方「升级路径」。

本目录既是**一份真实样例**，也是一个**可复制的模板**：把任意"待适配提示词 + 目标模型"套进同结构，即可产出你自己的适配样例。

---

## 文件地图

| 文件 | 作用 | 模板插槽 |
|---|---|---|
| `base_prompt.md` | 适配**前**基线提示词（教练提示词·优化版） | 换成你的待适配提示词 |
| `deepseek/adapted_prompt.md` | 适配**后**真实成品（DeepSeek 版） | 换成你适配后的成品 |
| `deepseek/model-quirks-observed.md` | 该模型专属癖好 + 定向改法 | 换成目标模型的癖好与改法 |
| `deepseek/regression_selfcheck.md` | 4 组回归用例的规则级自检 | 重跑自检并更新结论 |

---

## 当作模板复用（3 步）

1. **复制本目录**：`cp -r real-adaptation-deepseek real-adaptation-<你的模型>`。
2. **填空**：
   - 把 `base_prompt.md` 换成你的待适配提示词；
   - 把 `deepseek/adapted_prompt.md` 换成你为该模型写的适配版（保留顶部「来源与性质」标注）；
   - 把 `deepseek/model-quirks-observed.md` 改成该模型的真实癖好 + 定向改法（手法名取自 `skill/references/regression-and-techniques.md` §二）；
   - 重跑 `deepseek/regression_selfcheck.md` 的静态校验并更新结论。
3. **（可选）接回仓库**：在 `examples/README.md` 与中英文 `README.md` 目录树增条目；改完跑 `python scripts/test_phase0.py` 确认反漂移门禁 OK。

---

## 升级路径：从"手写实"到"实证"

本样例是**零 key 即可交付的真实内容**。要升级为带 live 指标的实证样例，配置 `OPENAI_API_KEY` 后：

```bash
# 用本目录的 base_prompt.md 作待适配提示词，对 deepseek 真机跑闭环 + 红队门禁
python scripts/run_loop.py --multi \
    --targets deepseek \
    --base-skill examples/real-adaptation-deepseek/base_prompt.md \
    --redteam-cases skill/security/redteam-cases.md \
    --workspace examples/real-adaptation-deepseek/_run --rounds 3
```

跑完可取出 `best_score`（4 组回归最高通过率）与 `redteam_violations`，回填 `regression_selfcheck.md` 的 ⏳ 项；若质量达标，用实证产物替换手写实 `adapted_prompt.md` 即可。详见 `skill/references/running-real-adaptation.md`。

> 注：仓库原生 `--multi` 默认 `--base-skill skill/SKILL.md`（适配方法论自身）。本样例演示"适配任意提示词"的用法——把 `--base-skill` 指向你的提示词文件即可。

---

## 诚实边界

- 手写实适配 ≠ 实证跑分；本目录**没有** `adaptation_manifest.json`、没有 `best_score`、没有 live 红队判定。
- 一切"模型真实行为"结论以 `run_loop.py --multi` 实证为准；本样例只证明"指令层已写入满足回归用例的约束"。
