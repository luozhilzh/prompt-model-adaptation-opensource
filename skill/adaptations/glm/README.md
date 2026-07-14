# GLM 适配工作区

目标模型：**GLM**（如 `glm-4.5` / `glm-4.6` / `glm-4.7` / `glm-5.x`）。

- 模型特性与适配注意点见 `skill/references/model-quirks.md`（GLM 相关段落）。
- 本目录由 `scripts/run_loop.py --multi --targets glm ...` 自动填充，请勿手动编辑中间产物。
- 适配产物写入本目录 `SKILL.md`；开始前其为 `skill/SKILL.md` 基础版的副本。
- **红队门禁未通过前不得合入主文件**：见 `adaptation_manifest.json` 的 `redteam_gate_pass` / `merge_allowed`。
- 与 `gemini/`、`claude/`、`deepseek/`、`qwen/`、`hunyuan/` 完全隔离，互不读取。
- 适配依据：模型特性见 `skill/references/model-quirks.md`，定向改法见 `skill/references/cross-model-adaptation-methodology.md` 与 `checklist-template.md`。
- 五步法适配范例见 `skill/references/demo-glm-adaptation.md`（国产模型 extras 范例集）。
