# 真机适配运行手册（API 接入 Runbook）

> 路线 A 核心交付的「最后一块垫脚石」。本手册不依赖 API 即可阅读，但所有命令需要你先配置 `OPENAI_API_KEY`。
> 配套：`scripts/run_loop.py`、`skill/references/cross-model-adaptation-methodology.md`、
> `skill/security/redteam-cases.md`、`skill/references/model-quirks.md`、`skill/adaptations/README.md`。

---

## 0. 这份手册解决什么

脚手架、方法学 SOP、DeepSeek 适配范例、一致性回归测试都已就位。唯一卡在 API 上的，是路线 A 真正的核心交付——**真机跨模型适配 + 红队门禁实测**。

本手册把「拿到 key 后怎么跑」一次讲清：配什么、命令怎么写、产物怎么读、真机数据回来后怎么回灌校准 `model-quirks.md`。让你拿到 key 当天就能开跑，不用再摸索 endpoint / 温度 / manifest 字段。

---

## 1. 前置依赖

```bash
pip install -r requirements.txt
```

仓库提供 `requirements.txt`（含 `openai`、`python-dotenv`），一键安装即可（`run_loop.py` 顶部 docstring 也注明了）。

---

## 2. 配置 .env

仓库提供 `.env.example`，复制为 `.env` 并填入：

```bash
cp .env.example .env
```

| 字段 | 作用 | 说明 |
|---|---|---|
| `OPENAI_API_KEY` | API key | 取决于 `BASE_URL` 用哪家网关 |
| `BASE_URL` | OpenAI 兼容基地址（全局默认） | 可用 `OPENAI_BASE_URL_<TARGET>` 按目标覆盖（见 §3） |
| `MODEL` | 单目标默认模型 | `--multi` 模式下被 `--targets` 覆盖 |
| `JUDGE_MODEL` | 独立裁判模型 | C 档 / 红队裁判用；留空 = 同 `MODEL` 自评 |

> ⚠️ **密钥安全**：确认 `.env` 已被 `.gitignore` 排除（若未排除，追加一行 `.env` 再提交）。不要把含真实 key 的 `.env` 推上仓库。

---

## 3. 多目标网关与目录约定（已修复，原「关键架构限制」已解决）

`run_loop.py` 现已支持**每目标独立网关**与**目录名自动 sanitize**，无需 patch 脚本：

1. **每目标 base_url**：默认用全局 `BASE_URL`；若存在环境变量 `OPENAI_BASE_URL_<TARGET 大写，非字母数字转义为 _>`，则该目标模型调用改用此网关。
   - 例：`OPENAI_BASE_URL_GEMINI=https://generativelanguage.googleapis.com/v1beta/openai/` 仅对 `gemini` 目标生效；`OPENAI_BASE_URL_GOOGLE_GEMINI_2_5_PRO` 对 `google/gemini-2.5-pro` 生效。
2. **目录名自动 sanitize**：`--targets` 的值仍原样传给 API 的 `model` 字段，但作为产物目录名时，`/ \ :` 会被替换为 `_`，保证平级。
   - 例：`google/gemini-2.5-pro` → 目录 `skill/adaptations/google_gemini-2.5-pro/`（不再嵌套）。manifest 中 `target_dir` / `base_url_resolved` 记录实际取值。

> 注：`API_KEY` 仍是全局单一（一个 key 对应你配置的网关）。若多目标需要不同 key，仍建议用「分家族单网关」跑法（见下）；若走 OpenRouter 这类单 key 多模型网关，可直接用每目标 base_url 切到不同前缀。

### 推荐跑法：分家族单网关（零改脚本、目录干净）

每次只跑一个目标家族，对应配好该家族的 `BASE_URL` + `KEY`，目录天然平级：

```bash
# DeepSeek（官方兼容层）
# .env: BASE_URL=https://api.deepseek.com  OPENAI_API_KEY=sk-...  MODEL=deepseek-chat
python scripts/run_loop.py --multi --targets deepseek \
    --base-skill skill/SKILL.md \
    --redteam-cases skill/security/redteam-cases.md \
    --workspace skill/adaptations --rounds 3

# Claude（Anthropic OpenAI 兼容层，需对应 key / 端点）
# .env: BASE_URL=https://api.anthropic.com/v1  OPENAI_API_KEY=sk-ant-...  MODEL=claude-3-7-sonnet-latest
python scripts/run_loop.py --multi --targets claude \
    --base-skill skill/SKILL.md \
    --redteam-cases skill/security/redteam-cases.md \
    --workspace skill/adaptations --rounds 3

# Gemini（AI Studio OpenAI 兼容层）
# .env: BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/  OPENAI_API_KEY=...  MODEL=gemini-2.5-pro
python scripts/run_loop.py --multi --targets gemini \
    --base-skill skill/SKILL.md \
    --redteam-cases skill/security/redteam-cases.md \
    --workspace skill/adaptations --rounds 3
```

三个命令跑完，`skill/adaptations/{gemini,claude,deepseek}/` 各有干净产物。

### 备选跑法：OpenRouter 一次混跑（需接受目录嵌套或后续 patch）

若用 OpenRouter（一个 key + 一个 `BASE_URL` 覆盖多家），可一次列出多目标：

```bash
# .env: BASE_URL=https://openrouter.ai/api/v1  OPENAI_API_KEY=sk-or-...
python scripts/run_loop.py --multi \
    --targets google/gemini-2.5-pro anthropic/claude-3.7-sonnet deepseek/deepseek-chat \
    --base-skill skill/SKILL.md \
    --redteam-cases skill/security/redteam-cases.md \
    --workspace skill/adaptations --rounds 3
```

注意：产物目录现在**自动平级**（如 `skill/adaptations/google_gemini-2.5-pro/`），不再嵌套；如需不同网关，可对每个目标设 `OPENAI_BASE_URL_<TARGET>`（见 §3）。OpenRouter 单 key 多模型场景下，`API_KEY` 共用、各 target 的 `model` 字段区分模型即可。

---

## 4. 单目标档位（B / C / D）跑法

`--multi` 之外，也可对单模型单独迭代（更细调试）：

```bash
# B 档（自裁判）：只填 MODEL
python scripts/run_loop.py --candidate skill/SKILL.md --rounds 5

# C 档（双模型 · 独立裁判）：--judge-model 填不同于 MODEL 的模型
python scripts/run_loop.py --candidate skill/SKILL.md --judge-model <裁判模型> --rounds 5

# D 档（自适应 · 失败类型驱动定向改法 + 检查表自填）
python scripts/run_loop.py --candidate skill/SKILL.md --judge-model <裁判模型> --d-mode --rounds 5
```

产物落在 `--out`（默认 `output/`）：`best_candidate.md`、`history.json`、`checklist_auto.md`（仅 D 档）。

---

## 5. 读产物

`--multi` 在 `skill/adaptations/<target>/` 产出：

- `SKILL.md`：本轮最优候选（起始 = 基础版，真适配后覆盖）
- `adaptation_manifest.json`：本目标结果（字段见 `skill/adaptations/README.md`「manifest 字段说明」）
- `loop/`：`candidate_roundN.md` / `report_roundN.json` / `redteam_details.json`（过程产物）
- `skill/adaptations/multi_summary.json`：全部目标汇总

manifest 关键字段：

| 字段 | 含义 |
|---|---|
| `best_score` | 4 组回归最高通过率（0–1） |
| `redteam_violations` | 红队违规 id 列表（空 = 无违规） |
| `redteam_gate_pass` | 红队门禁是否通过 |
| `merge_allowed` | 是否允许合入主文件（= 门禁通过） |

---

## 6. 红队门禁解读

- `redteam_gate_pass = (violations 为空)`；任一违规 → 该轮适配作废、棘轮 revert。
- 门禁证明「适配产物没弱化安全」，**不证明在真实模型上绝对安全**——终局仍需在目标模型实跑红队集（本命令即实跑）。
- 14 条 / 8 类清单见 `skill/security/redteam-cases.md`。

---

## 7. 回校准 model-quirks.md（闭环）

真机数据回来后，与 `model-quirks.md` 中对应段落的「经验预测」对比：

- 若实测与预测一致 → 在该段「已实跑校准」处打勾 / 注明实测版本。
- 若不一致（如 DeepSeek 实际不偏长、Claude 实际不吃预填充）→ **直接改对应段落**，并把改动写进 commit message。
- 这一步让「家族经验归纳」升级为「本仓库实测知识」，是路线 A【方法学 → 范例 → 真机】的闭环。

> 完整的逐项回灌清单（跑前自检 → 真机跑 → 提取指标 → 回灌 model-quirks / demo → 回归 → 提交，含风险点）见 **§10**。

---

## 8. 常见排错

| 现象 | 原因 / 处理 |
|---|---|
| `✗ 未找到 OPENAI_API_KEY` | `.env` 未建或未填；确认 `load_dotenv()` 已读到（脚本启动时自动读） |
| `✗ 未安装 openai SDK` | `pip install openai python-dotenv` |
| 429 / 限流 | 降 `--rounds`、错峰、或用更高配额 key；红队门禁每 target 额外 14 次调用 |
| 模型名报错（404 model not found） | `--targets` / `MODEL` 与 `BASE_URL` 网关命名不一致；查网关文档 |
| 目录嵌套（`google/gemini-2.5-pro`） | 用了含 `/` 的完整 ID，见 §3 备选跑法 |
| judge 解析失败（score 兜底 0.5） | 裁判模型返回非 JSON；一般模型不稳，重试或换 `JUDGE_MODEL` |
| `BASE_URL` 默认值 | 脚本默认 `https://api.openai.com/v1`（OpenAI 家族可直接用）；多家族用 `OPENAI_BASE_URL_<TARGET>` 覆盖（见 §3） |

---

## 9. 诚实边界

- 无真实 API 时 `--multi` 只产出「基础版副本 + 红队门禁逻辑跑通」的脚手架；本手册所有真机命令需你自备 key。
- `model-quirks.md` 中 Gemini / Claude 段为公开行为归纳、非本仓库实测，以真机数据校准为准。
- 红队门禁通过 ≠ 绝对安全；适配产物合入前仍建议人工过一遍 `Safety & Integrity Constraints`。

---

## 10. 真机跑分 SOP + 回灌清单（Replay Checklist）

拿到 `OPENAI_API_KEY` 后，按本清单一次跑通，并把「家族级预测」替换为「真机实测」。全流程分 6 步，建议严格按顺序走，避免漏回灌。

### 步骤 0：跑前自检（Pre-flight）

- [ ] `.env` 已建且 `OPENAI_API_KEY` / `BASE_URL` / `MODEL` 填妥（见 §2）
- [ ] 目标家族网关变量已设 `OPENAI_BASE_URL_<TARGET>`（多家族时，见 §3）
- [ ] `python -c "import openai, dotenv"` 无报错（依赖见 §1）
- [ ] `python scripts/test_phase0.py` 全绿（一致性门禁基线）
- [ ] `python scripts/simulate_run.py` 跑通（桩模拟对照基线）

### 步骤 1：跑真机（Run）

选 §3 推荐「分家族单网关」逐个跑（目录最干净、互不污染）：

```bash
# 例：DeepSeek（其余家族改 .env 后同理）
# .env: BASE_URL=https://api.deepseek.com  OPENAI_API_KEY=sk-...  MODEL=deepseek-chat
python scripts/run_loop.py --multi --targets deepseek \
    --base-skill skill/SKILL.md \
    --redteam-cases skill/security/redteam-cases.md \
    --workspace skill/adaptations --rounds 3
# 依次改 .env 跑 claude / gemini
```

三个目标跑完，确认 `skill/adaptations/{gemini,claude,deepseek}/SKILL.md` 已生成且**非基础副本**（内容经红队门禁迭代过）。

### 步骤 2：读真机指标（Extract）

从各目标 `adaptation_manifest.json` 提取：

- `best_score`：4 组回归最高通过率（0–1）
- `redteam_violations` / `redteam_gate_pass`：门禁结果（须全空 / `true`，否则该目标未过门禁，禁止回灌）
- loop 日志（`loop/report_roundN.json`）中的优化轮次、命中红队类别与修复动作
- 实际部署温度（run_loop 透传值，核对是否落在 `model-quirks.md` 建议区间）

### 步骤 3：回灌 model-quirks.md（Calibrate quirks）

对照真机指标，更新 `skill/references/model-quirks.md` 三家族段：

- **温度区间**：用实测最优温度替换经验区间（保留区间形式，便于后续适配复用）。
- **弱点列**：与预测一致 → 标注「✅ 已 `--multi` 实测（YYYY-MM-DD，通过率 X）」；不一致 → 改为实测结论并删去原预测。
- **适配要点**：某条在真机失效 → 降级 / 删除并备注原因；有效 → 打勾。
- 移除该段「非本仓库实测」的全局免责，或改为「部分实测」。
- 同步更新 §9 诚实边界中「非实测」的表述（改为「Gemini / Claude / DeepSeek 段已由 `--multi` 实测校准」）。

### 步骤 4：回灌三份 demo 范例（Calibrate demos）

对 `demo-{gemini,claude,deepseek}-adaptation.md`：

- **第 1 步「已知癖好 / 弱点」列**：与真机一致 → 标「✅ 已实测验证」；不一致 → 改实测结论。
- **约束块 A–E**：某定向改法在真机被证无效 / 过度 → 标「⚠️ 真机下调」或重写；有效 → 保留。
- **末尾新增「实测记录」小节**：日期、目标模型、通过率、轮次、关键发现（1–3 条）。
- **DeepSeek 注意**：若用 `deepseek-reasoner`，确认约束经 **user 提示** 传入（见 demo D 块备注），非 system 角色——否则 R1 会忽略。

### 步骤 5：回归验证（Regression）

- `python scripts/test_phase0.py` 必须仍全绿（重点 `test_targets_have_model_quirks_section`、`test_readme_references_resolve`）。
- `python scripts/simulate_run.py` 桩模拟仍跑通（对照基线未破坏）。
- `git diff --stat` 仅预期文件改动，无意外文件。

### 步骤 6：提交（Commit）

按项目约定手动提交（不自动）：

```bash
git add skill/adaptations/ skill/references/model-quirks.md skill/references/demo-*-adaptation.md
git commit -m "feat: 真机 --multi 跑通并回灌校准三家族范例与 model-quirks"
```

### 回灌风险点（Watch-outs）

| 风险 | 现象 | 处理 |
|---|---|---|
| R1 不用 system prompt | DeepSeek-R1 经 system 角色传约束被忽略 / 行为异常 | 约束改放 user 提示（demo D 块已标注） |
| Gemini thinking 冗余 | 回复出现显式逐步推理、拉长输出 | 收紧 E 块「无需显式逐步推理」；确认网关未强制 CoT |
| Claude 礼貌式回退 | 改用 please 式后通过率下降 | 回退直接指令式（demo D 块已标注） |
| 温度漂移 | 真机最优温度偏离建议区间 | 以实测为准更新 model-quirks，并在 commit 注明 |

### 模拟产物处理

- `skill/adaptations_sim/` 保留作「无 API 快速验证」对照；本手册 §0 已注明其为模拟非真适配。
- 可选：将真机 `SKILL.md` 复制覆盖 `adaptations_sim/<target>/`（去「模拟」水印）作 golden 样本，便于无 key 时对照。
