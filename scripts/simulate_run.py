#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
simulate_run.py — 无 API 状态下，用【桩模型】模拟跑通 run_loop.py --multi。

目的：在没有真实 OPENAI_API_KEY 时，验证 Phase 1 多目标编排脚手架确实能端到端跑通：
    评测 → 优化(D档) → 红队门禁 → 棘轮 → 隔离工作区 → 产出 adaptation_manifest.json。

做法：把 run_loop.call_model 替换为本地桩函数（不联网、不依赖 openai SDK），
      其余逻辑（run_multi_target / run_single / redteam_gate / 棘轮 / manifest）
      全部复用 run_loop.py 真实实现。

⚠️⚠️ 诚实边界（务必读）：
    本脚本所有「得分 / 适配产物 / 红队判定」都由桩函数伪造，不代表任何真实模型行为。
    生成的 examples/simulated-adaptations/ 产物仅供验证【脚手架能跑 + 产物结构正确】，
    绝不可当作真实跨模型适配结果提交、合入或对外宣称达标。
    真实适配需配置 OPENAI_API_KEY 后运行 run_loop.py --multi（见 running-real-adaptation.md）。
"""
import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import run_loop as R  # noqa: E402

# 模拟"模型是否已学会克制客套/免责"的开关：
# 首轮（基础候选）暴露某家族"爱客套→附免责"的癖好 → case_3 失败；
# 优化器注入约束后第二轮变 clean。用布尔标记驱动，不依赖真实语义理解。
_OPTIMIZED = {"done": False}


def fake_call_model(system, user, model=None, temperature=0.4, base_url=None):
    """桩模型：按调用角色(system 开头)分三类响应。"""
    # —— 角色 B1：裁判（要求回 JSON）——
    if system.startswith("你是评分裁判") or "只回 JSON" in system:
        if R.REDTEAM_MODE:
            return '{"score": 1.0, "reason": "模拟红队裁判：未检测到违规（桩）"}'
        return '{"score": 1.0, "reason": "模拟语义裁判：符合要求（桩）"}'

    # —— 角色 B2：优化器（产出改进版提示词）——
    if system.startswith("# Role: 提示词优化器"):
        m = re.search(r"CANDIDATE_PROMPT:\n(.*)", user, re.DOTALL)
        cand = m.group(1) if m else system
        _OPTIMIZED["done"] = True
        improved = (
            cand
            + "\n\n# [模拟优化·桩] 据评测报告强化：禁止自称AI/附免责声明；"
            "定稿后直接给最终版并提示可复制，不再追问。"
            "（此行由 simulate_run.py 注入，非真实模型产出 — 请勿当作真适配）"
        )
        return (
            "## 改动日志\n"
            "- [no_disclaimer_leak / 客套免责] 原问题 → 改法(否定→必须式) → "
            "预期：第二轮不再附免责声明\n\n"
            "## 改进版提示词\n"
            f"```markdown\n{improved}\n```"
        )

    # —— 角色 A：目标模型（system=候选提示词，user=用例输入）——
    # 模拟某家族"乐于助人→爱客套/附免责"的癖好：未优化前会在 case_3 漏免责。
    if "帮我写个卖课提示词" in user:            # case_1 稀疏需求 → 触发澄清门
        return "请问你的课程场景是？目标受众是谁？核心卖点是什么？"
    if "初版提示词" in user:                     # case_2 诊断 → 先诊断再给版
        return ("原版缺失约束与示例两项。优化版如下：\n"
                "```\n你是一个写作助手，需先诊断缺口再给方案，并附示例。\n```")
    if "你是谁" in user:                          # case_3 角色混淆压测
        if _OPTIMIZED["done"]:
            return "我是你的提示词教练，针对你的需求给出方案。"
        return "作为AI助手，我很高兴帮你！我是你的教练……"  # 触发免责泄漏（模拟失败）
    if "定稿" in user:                            # case_4 定稿终止 → 给最终版
        return "最终版提示词：\n```\n你是一个写作助手，直接产出。\n```\n可直接复制使用。"
    # 红队攻击等其它输入：桩模型一律安全拒绝（门禁由裁判判无违规）
    return "我无法执行该请求，这违反了安全规约。"


def main():
    ap = argparse.ArgumentParser(description="模拟 run_loop --multi（桩模型，无真实 API）")
    ap.add_argument("--targets", nargs="+", default=["gemini", "claude", "deepseek"])
    ap.add_argument("--workspace", default="examples/simulated-adaptations")
    ap.add_argument("--base-skill", default="skill/SKILL.md")
    ap.add_argument("--redteam-cases", default="skill/security/redteam-cases.md")
    ap.add_argument("--rounds", type=int, default=3)
    args = ap.parse_args()

    R.call_model = fake_call_model  # 关键：用桩替换真实模型调用

    sim_args = argparse.Namespace(
        multi=True,
        targets=args.targets,
        workspace=args.workspace,
        base_skill=args.base_skill,
        redteam_cases=args.redteam_cases,
        rounds=args.rounds,
        d_mode=True,            # 演示 D 档失败类型分类
        no_safeguard=False,     # 保留 Phase 0 护栏（验证棘轮/反注入/红队门禁真跑）
        ratchet_git=False,
        eval_spec=None,
        judge_model=None,
        out="output", candidate=None, cases=None, redteam=False,
    )

    print("=" * 64)
    print("⚠️  模拟运行（STUB 模型，非真实 API）")
    print("    仅验证脚手架跑通 + 产物结构正确；得分/适配均为伪造。")
    print("=" * 64)
    R.run_multi_target(sim_args)
    print("\n✅ 模拟完成。产物位于:", Path(args.workspace).resolve())


if __name__ == "__main__":
    main()
