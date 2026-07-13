# DeepSeek 适配工作区

目标模型：**DeepSeek**（如 `deepseek-chat` / `deepseek-reasoner`）。

- 模型特性与适配注意点见 `skill/references/model-quirks.md`（DeepSeek 相关段落）。
- 本目录由 `scripts/run_loop.py --multi --targets deepseek ...` 自动填充，请勿手动编辑中间产物。
- 适配产物写入本目录 `SKILL.md`；开始前其为 `skill/SKILL.md` 基础版的副本。
- **红队门禁未通过前不得合入主文件**：见 `adaptation_manifest.json` 的 `redteam_gate_pass` / `merge_allowed`。
- 与 `gemini/`、`claude/` 完全隔离，互不读取。
- 适配依据：模型特性见 `skill/references/model-quirks.md`（DeepSeek 偏长、易"好心加戏"、R1 有独立思考区），定向改法见 `skill/references/cross-model-adaptation-methodology.md` 与 `checklist-template.md`。
