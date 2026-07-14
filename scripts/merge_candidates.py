#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
merge_candidates.py — 子 Agent 扇出后的「中心合入」离线评审（Phase 1 · §6）

对应方法学 cross-model-adaptation-methodology.md §6 与 skill/adaptations/README.md
§合入/棘轮规则。本地 run_loop.py --multi 只做顺序编排与逐目标 manifest；真正的
「并发」在 WorkBuddy 内由子 Agent 扇出，每个目标写自己目录。本脚本扮演「中心」：

    读取各目标 adaptation_manifest.json → 套用红队门禁 + 棘轮规则（均离线、无需 key）
    → 逐目标判定 merge / revert，并产出 merged_review.json + 人话摘要。

判定规则（与契约一致）：
    当且仅当  redteam_gate_pass == True 且 ratchet_delta > 0  时 verdict = merge
    否则 revert（原因：红队未通过 / 棘轮未正向 / 二者兼有）

ratchet_delta = manifest.best_score - baseline[target]；baseline 由各档当前通过率基线
提供（工单输入的 ratchet_baseline），离线 demo 用内嵌基线。

运行：
    python scripts/merge_candidates.py --demo
    python scripts/merge_candidates.py --root skill/adaptations --baseline baseline.json --out merged_review.json

零依赖：仅标准库。不触达 OpenAI SDK / 不需要 OPENAI_API_KEY。
"""

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path


# ---------------------------------------------------------------------------
# 1. 读取各目标 manifest
# ---------------------------------------------------------------------------
def load_manifests(root):
    """读取 root 下所有 */adaptation_manifest.json；损坏的跳过并告警。"""
    root = Path(root)
    manifests = []
    for m in sorted(root.glob("*/adaptation_manifest.json")):
        try:
            manifests.append(json.loads(m.read_text(encoding="utf-8")))
        except Exception as e:  # 损坏的 manifest 不阻断整体评审
            print(f"⚠ 跳过无法解析的 manifest: {m} ({e})", file=sys.stderr)
    return manifests


# ---------------------------------------------------------------------------
# 2. 单目标判定（纯函数，可单测）
# ---------------------------------------------------------------------------
def decide_merge(manifest, baseline_scores):
    """对一份 manifest 套用合入规则，返回判定 dict。

    manifest 需含：target, best_score, redteam_violations, redteam_gate_pass
    baseline_scores: {target: 基线通过率 0-1}
    """
    target = manifest.get("target", "?")
    violations = manifest.get("redteam_violations", [])
    redteam_pass = manifest.get("redteam_gate_pass", len(violations) == 0)
    best = float(manifest.get("best_score", 0.0))
    base = float(baseline_scores.get(target, 0.0))
    delta = round(best - base, 4)

    reasons = []
    if not redteam_pass:
        reasons.append(f"红队门禁未通过（违规: {violations or 'gate_pass=False'}）")
    if delta <= 0:
        reasons.append(f"棘轮未正向（best={best} ≤ baseline={base}, delta={delta}）")

    verdict = "merge" if not reasons else "revert"
    reason = "；".join(reasons) if reasons else f"红队通过且棘轮正向（delta={delta}）"
    return {
        "target": target,
        "redteam_pass": redteam_pass,
        "best_score": best,
        "baseline": base,
        "ratchet_delta": delta,
        "verdict": verdict,
        "reason": reason,
        "adapted_skill_path": manifest.get("adapted_skill_path"),
    }


# ---------------------------------------------------------------------------
# 3. 汇总评审
# ---------------------------------------------------------------------------
def merge_candidates(root, baseline, out=None):
    manifests = load_manifests(root)
    decisions = [decide_merge(m, baseline) for m in manifests]
    merged = sum(1 for d in decisions if d["verdict"] == "merge")
    review = {
        "source_root": str(root),
        "n_targets": len(decisions),
        "n_merge": merged,
        "n_revert": len(decisions) - merged,
        "decisions": decisions,
    }
    if out:
        Path(out).write_text(
            json.dumps(review, ensure_ascii=False, indent=2), encoding="utf-8")
    return review


def _print_summary(review):
    print(f"\n=== 中心合入评审（{review['n_targets']} 目标）===")
    for d in review["decisions"]:
        mark = "✓ 合入" if d["verdict"] == "merge" else "✗ 回退"
        print(f"  {mark} {d['target']:<10} {d['reason']}")
    print(f"汇总：{review['n_merge']} 合入 / {review['n_revert']} 回退")


# ---------------------------------------------------------------------------
# 4. 离线演示
# ---------------------------------------------------------------------------
def _demo():
    tmp = Path(tempfile.mkdtemp(prefix="merge_demo_"))
    baseline = {"gemini": 0.70, "claude": 0.65, "deepseek": 0.60}
    samples = [
        # 1) 通过：红队空 + 棘轮正向
        {"target": "gemini", "best_score": 0.85, "redteam_violations": [],
         "redteam_gate_pass": True, "adapted_skill_path": "skill/adaptations/gemini/SKILL.md"},
        # 2) 红队挂：有违规 → revert
        {"target": "claude", "best_score": 0.80, "redteam_violations": ["RT-03"],
         "redteam_gate_pass": False, "adapted_skill_path": "skill/adaptations/claude/SKILL.md"},
        # 3) 棘轮负：红队过但分数没涨 → revert
        {"target": "deepseek", "best_score": 0.55, "redteam_violations": [],
         "redteam_gate_pass": True, "adapted_skill_path": "skill/adaptations/deepseek/SKILL.md"},
    ]
    for s in samples:
        d = tmp / s["target"]
        d.mkdir(parents=True, exist_ok=True)
        (d / "adaptation_manifest.json").write_text(
            json.dumps(s, ensure_ascii=False, indent=2), encoding="utf-8")
    review = merge_candidates(tmp, baseline, tmp / "merged_review.json")
    _print_summary(review)
    print(f"\n(演示产物在临时目录: {tmp})")
    return review


# ---------------------------------------------------------------------------
# 5. CLI
# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="子 Agent 扇出后的中心合入评审（离线）")
    ap.add_argument("--root", help="adaptations 工作区根目录（含 */adaptation_manifest.json）")
    ap.add_argument("--baseline", help="各目标基线通过率 JSON 文件，如 {\"gemini\":0.7}")
    ap.add_argument("--out", help="merged_review.json 输出路径")
    ap.add_argument("--demo", action="store_true", help="离线演示：合成 3 份 manifest 跑一遍")
    args = ap.parse_args()

    if args.demo:
        _demo()
        return

    if not args.root:
        ap.error("需 --root 或 --demo")

    baseline = {}
    if args.baseline:
        baseline = json.loads(Path(args.baseline).read_text(encoding="utf-8"))

    review = merge_candidates(args.root, baseline, args.out)
    _print_summary(review)
    if args.out:
        print(f"\n已写出评审: {args.out}")


if __name__ == "__main__":
    main()
