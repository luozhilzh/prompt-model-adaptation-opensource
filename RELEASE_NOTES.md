# prompt-model-adaptation v1.0.1

> 发布日期：2026-08-13 ｜ 类型：Patch（发版后元数据/质量修复，向后兼容）｜ 相对版本：v1.0.0
> 作者：luozhi ｜ License：MIT

![version](https://img.shields.io/badge/version-1.0.1-blue)
![license](https://img.shields.io/badge/license-MIT-green)
![cross--tool](https://img.shields.io/badge/cross--tool-WB%20%7C%20Claude%20Code%20%7C%20Cursor%20%7C%20Codex-9cf)

---

## 中文

### 摘要
本版本为**质量与文档修复（发版后补的元数据修正）**：补齐 SKILL.md `version` 字段以对齐已发布的 v1.0.0 tag；新增「跨工具兼容」声明与「触发边界」声明；新增本双语发行说明。无工作流逻辑变更，向后兼容。

### 变更明细

**修复（Fixes）**
- `skill/SKILL.md` frontmatter 新增 `version: 1.0.1`；原 v1.0.0 tag 未含 frontmatter `version` 字段，属元数据缺漏，现已对齐（按发版后补的元数据修正定为 PATCH，并新打 `v1.0.1`）。

**新增（Added）**
- `skill/SKILL.md` 顶部「跨工具兼容」callout（WB / Claude Code / Cursor / Codex / 通用长指令）。
- `skill/SKILL.md`「When to Use」触发边界声明，限定仅「跨模型适配 / 系统提示优化 + 4-case 回归」时触发。
- 仓库根 `RELEASE_NOTES.md`（中英双语发行说明）。

**文档（Docs）**
- 明确 `agent_created` 缺失对**手写** skill 为已知误报（不改），避免伪造来源。

### 已知限制
- `name_directory`：源布局 `skill/` 目录名与 `name: prompt-model-adaptation` 不一致，`scripts/validate` 仍会报该项；部署为 `~/.workbuddy/skills/prompt-model-adaptation/` 后目录名即匹配，源布局按原样保留，**非阻断**。
- 未在真实运行态验证自动触发命中率（需真会话 + 各目标模型 API key）。
- 唯一 WorkBuddy 专属能力在其他工具退化为仅交付提示词属预期行为；本 skill 核心为提示词方法论，跨工具无功能降级。

### ⬆️ 升级指引（从 v1.0.0 → v1.0.1，必读）
> 本版本为**向后兼容**的增量更新，**无需重新生成任何产物**。

1. **拉取源码**：`git pull`
2. **用户级副本（WorkBuddy 默认）**：`cp -r prompt-model-adaptation-opensource/skill ~/.workbuddy/skills/prompt-model-adaptation/`
3. **项目级副本**：`cp -r prompt-model-adaptation-opensource/skill <workspace>/.workbuddy/skills/prompt-model-adaptation/`
4. **其他工具（Claude Code / Cursor / Codex / 通用）**：按 `README.md`「用法三 / 四 / 五」与 `formats/` 重新加载。
5. **验证**：新会话跑一次「把这段提示词适配成 DeepSeek」，确认 Skill 正常触发并产出完整输出包。

### 完整变更文件
- `skill/SKILL.md`（补 `version` + 跨工具 callout + 触发边界）
- `RELEASE_NOTES.md`（新增）

---

## English

### Summary
Quality and documentation fix (post-release metadata correction): added the missing `version` field to `SKILL.md` to align with the published v1.0.0 tag; added a "cross-tool compatible" callout and a "trigger boundary" statement; added these bilingual release notes. No workflow-logic changes; fully backward compatible.

### Changes

**Fixes**
- `skill/SKILL.md` frontmatter now carries `version: 1.0.1`; the original v1.0.0 tag lacked a frontmatter `version` field (a metadata gap), now aligned. Treated as a PATCH post-release metadata correction, with a new `v1.0.1` tag.

**Added**
- `skill/SKILL.md` top "cross-tool compatible" callout (WB / Claude Code / Cursor / Codex / generic long-instruction).
- `skill/SKILL.md` "When to Use" trigger-boundary statement, limited to "cross-model adaptation / system-prompt optimization + 4-case regression".
- Repo-root `RELEASE_NOTES.md` (bilingual release notes).

**Docs**
- Clarified that a missing `agent_created` is a known false positive for **handwritten** skills (do not add).

### Known Limitations
- `name_directory`: source layout dir `skill/` differs from `name: prompt-model-adaptation`; `scripts/validate` still reports it. Deploying as `~/.workbuddy/skills/prompt-model-adaptation/` matches the name — source layout kept as-is, **non-blocking**.
- Automatic-trigger hit rate under real runtime not verified (requires a real session + per-model API keys).
- WB-only capability degrades to prompt-only delivery in other tools (expected); the skill is prompt-methodology at its core, no functional degradation across tools.

### ⬆️ Upgrade (from v1.0.0 → v1.0.1, read this)
> Backward-compatible incremental update — **no regeneration needed**.

1. **Pull source**: `git pull`
2. **User-level copy (WB default)**: `cp -r prompt-model-adaptation-opensource/skill ~/.workbuddy/skills/prompt-model-adaptation/`
3. **Project-level copy**: `cp -r prompt-model-adaptation-opensource/skill <workspace>/.workbuddy/skills/prompt-model-adaptation/`
4. **Other tools**: reload per `README.md` "Usage 3 / 4 / 5" and `formats/`.
5. **Verify**: in a new session, run "adapt this prompt for DeepSeek" and confirm the Skill triggers and emits the full output package.

### Files Changed
- `skill/SKILL.md` (version + cross-tool callout + trigger boundary)
- `RELEASE_NOTES.md` (added)
