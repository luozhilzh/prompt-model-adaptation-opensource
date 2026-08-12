# examples/ — 示例与脚手架产物

本目录存放**可运行的示例产物**，与 `skill/`（运行时载荷）分离，方便浏览与对照。

- `simulated-adaptations/` — 由 `scripts/simulate_run.py` 用**桩模型**生成的示例产物。
  ⚠️ **STUB · 非真实适配**：里面的得分 / 适配 / 红队判定全部由桩函数伪造，仅用于证明 Phase 1 多目标编排脚手架能端到端跑通、产物结构正确，**不代表任何真实模型的适配质量**。请勿当作真适配提交、合入或对外宣称达标。详见 `simulated-adaptations/README.md`。
- `real-adaptation-deepseek/` — **手写实适配样例（模板）**。
  🟢 **REAL (hand-authored) · 非 STUB · 非 empirical**：`deepseek/adapted_prompt.md` 是作者真实部署 DeepSeek 写出的适配提示词（真实内容，非桩伪造），可作为"成品长啥样"的参照；但**未经** `run_loop.py --multi` 真机跑分，无 `best_score` / 红队 `violations`。含 `base_prompt.md`（前）、`deepseek/adapted_prompt.md`（后）、`deepseek/model-quirks-observed.md`（癖好+改法）、`deepseek/regression_selfcheck.md`（4 案例规则级自检）。详见 `real-adaptation-deepseek/README.md`。
- **真机端到端示例（real adaptation）**：待配置 `OPENAI_API_KEY` 后生成。运行
  ```bash
  python scripts/run_loop.py --multi \
      --targets <模型> \
      --base-skill skill/SKILL.md \
      --redteam-cases skill/security/redteam-cases.md \
      --workspace skill/adaptations --rounds 3
  ```
  即可在 `skill/adaptations/` 产出各目标的真实隔离适配产物（见 `skill/references/running-real-adaptation.md`）。届时把 `skill/adaptations/<target>/SKILL.md` 复制为 `examples/real-adaptation/<target>.md` 即可作为对照样本。
