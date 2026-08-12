# simulated-adaptations/ — 桩模型示例产物（STUB）

本目录由 `scripts/simulate_run.py` 生成，**全部为桩模型伪造**，仅用于验证 Phase 1 多目标编排脚手架能端到端跑通、产物结构正确。

- 每个 `<target>/` 含 `adaptation_manifest.json`、`SKILL.md`、`loop/`（评分 / 优化 / 红队记录）。
- `multi_summary.json` 为多目标汇总。
- 所有产物带「模拟 · 非真适配」水印；红队门禁 / 棘轮 / 隔离工作区均为**真实逻辑跑通**。

> ⚠️ **切勿将此处产物当作真实跨模型适配结果。** 真实适配需配置 `OPENAI_API_KEY` 后运行 `run_loop.py --multi`（见 `skill/references/running-real-adaptation.md`）。
