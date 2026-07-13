# 跨模型适配工作区（skill/adaptations/）

> Phase 1（路线 A · 负责任跨模型适配方法论）的产出与隔离根目录。
> 本目录由 `scripts/run_loop.py --multi` 自动填充；手动编辑前请先读本节。

## 目录约定

```
skill/adaptations/
├── README.md                      # 本文件：工作区契约
├── gemini/                        # 目标模型：Gemini 适配产物（隔离）
│   ├── SKILL.md                   #   适配后的 SKILL.md（起始=基础版，真适配后覆盖）
│   ├── adaptation_manifest.json   #   本目标适配结果：best_round / redteam_gate_pass / merge_allowed
│   └── loop/                      #   自优化闭环过程产物（candidate_roundN.md / report_roundN.json / redteam_details.json）
├── claude/                        # 目标模型：Claude（同上结构）
├── deepseek/                      # 目标模型：DeepSeek（同上结构）
└── multi_summary.json             # 全部目标汇总
```

每个目标模型一个独立子目录，**互不读取对方文件**，避免并发适配时抢写同一份 SKILL.md。

## 子 Agent 写入契约（并发模式）

真正的高墙钟并发由 WorkBuddy 子 Agent 扇出实现：每个目标模型认领一个子 Agent，
各自跑单目标模式（`run_loop.py --candidate <基础版> ...`）写入自己的目录。中心（你/主 Agent）
只做：**读取各 manifest → 红队门禁复核 → 合并或 revert**。

工单输入（结构化的，不是一句"去适配 X"）：
- `base_skill`：基础版 `skill/SKILL.md` 路径
- `target_model`：目标模型名（如 gemini-2.5-pro）
- `eval_set`：`skill/references/tier-tests/`（共享只读）
- `hard_invariants`：安全拒绝 / 澄清门 / 终止条件 / Safety & Integrity Constraints 不可移除
- `ratchet_baseline`：当前各档通过率基线

工单输出（必须真实跑出，不能嘴说）：
- `adapted_skill_path`：本目录 `SKILL.md`
- `report`：改动说明 + 目标模型特性依据
- `pass_rates`：4 组回归通过率
- `violations`：红队集违规清单（空=无）
- `ratchet_delta`：相对基线增量

## 合入 / 棘轮规则（硬不变量中的硬不变量）

当且仅当 **`ratchet_delta > 0` 且 `violations` 为空** 时，该目标适配产物才允许：
- 合入主文件（覆盖 `skill/SKILL.md` 的目标模型变体），或
- 作为该模型的独立变体保留（推荐，避免覆盖基础版）。

否则自动 revert，工单带失败原因重发。任一红队违规 = 本轮适配作废。

## manifest 字段说明（adaptation_manifest.json）

| 字段 | 含义 |
|---|---|
| `target` | 目标模型名 |
| `best_round` | 自优化闭环中达到最高分的轮次 |
| `best_score` | 4 组回归最高通过率（0–1） |
| `redteam_violations` | 红队集违规用例 id 列表（空=无违规） |
| `redteam_gate_pass` | 红队门禁是否通过（空违规=True） |
| `merge_allowed` | 是否允许合入主文件（= 红队门禁通过） |
| `adapted_skill_path` | 本目录适配产物路径 |
| `loop_dir` | 闭环过程产物目录 |
| `note` | 备注（无 API 时标注"脚手架：未真实适配"） |

## 诚实边界

- 无真实 OpenAI 兼容 API 时，`--multi` 仅能产出"基础版副本 + 红队门禁逻辑跑通"的脚手架；
  真实跨模型适配（不同模型的不同失败模式 → 不同定向改法）需要配置 `OPENAI_API_KEY` 后运行。
- 红队门禁证明的是"适配产物没弱化安全"，不证明"在真实模型上绝对安全"——终局需在目标模型实跑。
- 本目录产物是**执行结果**，可入仓库；讨论性文档（路线/专家视角等）按 `.gitignore` 排除。
