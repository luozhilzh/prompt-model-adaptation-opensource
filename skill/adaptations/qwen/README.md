# Qwen 适配工作区

目标模型：**Qwen**（如 `qwen2.5` / `qwen3` / `qwen3-max`）。

- 模型特性与适配注意点见 `skill/references/model-quirks.md`（Qwen 相关段落）；注意 Qwen 默认开 thinking（`<think>` 泄漏风险）、严禁 `temperature=0`，详见同文档 Qwen 段落。
- 本目录由 `scripts/run_loop.py --multi --targets qwen ...` 自动填充，请勿手动编辑中间产物。
- 适配产物写入本目录 `SKILL.md`；开始前其为 `skill/SKILL.md` 基础版的副本。
- **红队门禁未通过前不得合入主文件**：见 `adaptation_manifest.json` 的 `redteam_gate_pass` / `merge_allowed`。
- 与 `gemini/`、`claude/`、`deepseek/`、`glm/`、`hunyuan/` 完全隔离，互不读取。
- 适配依据：模型特性见 `skill/references/model-quirks.md`，定向改法见 `skill/references/cross-model-adaptation-methodology.md` 与 `checklist-template.md`。
- 五步法适配范例见 `skill/references/demo-qwen-adaptation.md`（国产模型 extras 范例集）。
