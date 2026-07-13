# 安全护栏（Phase 0）

本文档说明 `scripts/run_loop.py` **v2** 内置的 Phase 0 安全底座。对应升级路线文档
《升级路线-具体执行方案.md》Phase 0（第 0 号护栏：规约冻结 + 棘轮 + 反注入 + 红队）。

## 四大护栏

### 1. 规约冻结（Specification Freeze）
- 循环前对评测规约（`cases`）计算 sha256 基线。
- 可选 `--eval-spec <文件>`：额外冻结一个规约文件，每轮重新哈希比对；若运行中被外部改动
  → 报错并 revert 本轮（保持上轮候选）。
- 优化器 system prompt 注入硬约束（`SPEC_FREEZE_CONSTRAINT`）：只能改候选提示词**行为措辞**，
  禁止修改评测维度 / 失败定义 / 通过阈值 / 安全拒绝机制，禁止植入操纵裁判的指令。

### 2. 棘轮（Ratchet）
- **只进不退**：本轮分数低于上轮 → 退回上轮候选，不向前污染历史。
- 可选 `--ratchet-git`：每轮把候选产物 `git commit`（仅提交产物文件）。跌分自动不前进。

### 3. 反注入探针（Injection Probe）
- `injection_probe()` 用正则扫描候选提示词，命中「忽略评分 / 请打高分 / 你是裁判 /
  system prompt / 绕过安全 / 关闭安全」等模式 → 报警并**阻断该轮优化**，循环终止以避免污染。

### 4. 安全红队回归集
- `skill/security/redteam-cases.md`（14 条 / 8 类）结构兼容 `--cases`，由 `--redteam` 模式加载。
- 红队模式用专用裁判提示（`_REDTEAM_JUDGE_PROMPT`）判定响应是否违反安全规约；
  `pass_threshold = 1.0` **零容忍**，任一违规即整条失败。
- 配合棘轮：红队失败 → 该轮适配 revert。

## 用法

```bash
# 红队回归（零容忍）：加载安全红队集，由裁判模型判违规
python run_loop.py --candidate <候选> \
    --redteam --cases ../skill/security/redteam-cases.md --judge-model <裁判模型>

# 规约冻结文件哈希校验（防运行中外改 eval-spec）
python run_loop.py --candidate <候选> --eval-spec ../skill/references/eval-spec.md

# 棘轮 git 快照（每轮提交候选产物，跌分自动不前进）
python run_loop.py --candidate <候选> --ratchet-git

# 关闭全部 Phase 0 护栏（退回纯 v1 行为）
python run_loop.py --candidate <候选> --no-safeguard
```

## 单元测试

```bash
python test_phase0.py     # 离线 mock 模型调用，验证规约冻结/棘轮/反注入逻辑
```

## 诚实边界
- 护栏防的是「优化循环自身跑偏 / 候选被注入操纵 / 规约被外改」，不证明适配在真实模型上绝对安全。
- 红队集需随新攻击模式持续扩充（见 `skill/security/redteam-cases.md` 维护约定）。
- 真实安全验证需在目标模型上**实跑红队集**，而非仅代码层校验。
