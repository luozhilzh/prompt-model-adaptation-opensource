## 改动类型 / Type of change

- [ ] 新增目标模型 / New model target
- [ ] 方法学或文档 / Methodology or docs
- [ ] 脚本或测试 / Script or test
- [ ] 其他 / Other

## 改动说明 / What & why

<!-- 简述做了什么、为什么。Keep it short and concrete. -->

## 自检（提交前必过）/ Pre-submit checklist

- [ ] `python scripts/test_phase0.py` 全绿（含一致性回归）/ all green
- [ ] 棘轮 delta ≥ 0 且红队零违反（如涉及适配产物）/ ratchet + red-team satisfied
- [ ] `model-quirks.md` 与一致性测试已同步（如新增 / 改名目标）/ model-quirks synced
- [ ] `Safety & Integrity Constraints` 未被删 / 弱 / safety invariants intact
- [ ] 中英文 README 已同步（如涉及）/ README zh+en synced
- [ ] 无密钥文件入库 / no secrets committed (`.env` is locally excluded)

## 关联 / Related

<!-- 关联 issue / 方法论章节 / Related issue or methodology section -->
