#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
eval_credibility.py — Phase 2 评测可信度：裁判自洽投票 / 方差报告（离线工具）

用途：给定同一条候选提示词被 K 个裁判（或同一裁判 K 次）打出的 K 份评测报告，
      汇总每条用例的「通过率稳定性」与「维度分均值/标准差」，输出可信度报告。

输入格式：每个 JSON 文件是一份评测报告，结构同 run_loop.py 产出的
          report_roundN.json —— 一个 case 列表，每个 case 含
          {"id", "name", "passed": bool, "dimensions": [{"key", "pass": 0~1, "weight"}]}。

⚠️ 诚实边界：本脚本只做统计汇总，不调用任何模型、不需要 API key。
   真实可信数字需配置 OPENAI_API_KEY 后跑真实评测收集 K 份报告再喂入。
   --demo 用 mock 打分，仅验证报告格式与工具能跑，不代表真实裁判稳定性。

依赖：仅标准库（json / statistics / argparse）。
"""
import argparse
import json
import statistics
import sys
from pathlib import Path


def load_reports(paths):
    reports = []
    for p in paths:
        data = json.loads(Path(p).read_text(encoding="utf-8"))
        # 兼容「外层是 {rounds:[...]}」或「直接是 case 列表」两种形态
        if isinstance(data, dict) and "rounds" in data:
            data = data["rounds"]
        if isinstance(data, dict) and "report" in data:
            data = data["report"]
        reports.append(data)
    return reports


def _dim_scores(case):
    return [float(d.get("pass", 0.0)) for d in case.get("dimensions", [])]


def build_variance_table(reports):
    """按 case id 对齐 K 份报告，算稳定性 + 维度分均值/标准差。"""
    by_id = {}
    order = []
    for rep in reports:
        for case in rep:
            cid = case.get("id") or case.get("name") or str(len(order))
            if cid not in by_id:
                by_id[cid] = {"name": case.get("name", cid), "passed": [], "scores": []}
                order.append(cid)
            by_id[cid]["passed"].append(bool(case.get("passed", False)))
            by_id[cid]["scores"].extend(_dim_scores(case))

    rows = []
    for cid in order:
        rec = by_id[cid]
        k = len(rec["passed"])
        pass_count = sum(1 for x in rec["passed"] if x)
        stability = pass_count / k if k else 0.0
        scores = rec["scores"]
        mu = statistics.fmean(scores) if scores else 0.0
        sigma = statistics.pstdev(scores) if len(scores) > 1 else 0.0
        # 置信：全一致且 pass → 高；有波动 → 低
        if stability == 1.0:
            conf = "高"
        elif stability == 0.0:
            conf = "高（稳定不通过）"
        else:
            conf = "低（需复核）"
        rows.append({
            "id": cid, "name": rec["name"], "pass_count": pass_count, "k": k,
            "stability": stability, "mu": mu, "sigma": sigma, "conf": conf,
        })
    return rows


def render_table(rows):
    head = "| 用例 | K 次 pass 数 | 通过率稳定性 | 维度分均值 μ | 维度分标准差 σ | 置信 |\n"
    sep = "|---|---|---|---|---|---|\n"
    lines = [head, sep]
    for r in rows:
        lines.append(
            f"| {r['id']} {r['name']} | {r['pass_count']}/{r['k']} | "
            f"{r['stability']:.2f} | {r['mu']:.2f} | {r['sigma']:.2f} | {r['conf']} |\n"
        )
    return "".join(lines)


def demo():
    """生成 mock K=4 份报告并打印方差报告（不调用模型）。"""
    # case_1/2/4 稳定通过；case_3 在 4 次里 3 次通过、1 次失败 —— 制造波动演示
    base = {
        "case_1": "稀疏需求", "case_2": "B类初版",
        "case_3": "角色压测", "case_4": "定稿终止",
    }
    flips = {"case_3": False}  # 第 3 份报告里 case_3 翻车
    reports = []
    for i in range(4):
        cases = []
        for cid, name in base.items():
            ok = True
            passed = flips.get(cid, ok) if i == 2 else ok
            # 维度分：通过=1.0，失败=0.3~0.6 随机抖动（mock）
            dim_pass = 1.0 if passed else (0.4 + 0.1 * (i % 3))
            cases.append({
                "id": cid, "name": name, "passed": passed,
                "dimensions": [{"key": "mock_dim", "pass": dim_pass, "weight": 1.0}],
            })
        reports.append(cases)
    rows = build_variance_table(reports)
    print("=" * 64)
    print("⚠️  DEMO 模式（mock 打分，非真实裁判稳定性）")
    print("=" * 64)
    print(render_table(rows))
    print("\n判读：case_3 在 4 次里 3 次通过 → 稳定性 0.75、σ>0 → 置信『低（需复核）』")
    print("      说明单凭一次 pass 不能宣称该用例达标。真实用法传入 K 份 report JSON。")


def main():
    ap = argparse.ArgumentParser(description="Phase 2 评测可信度：K 份裁判报告的方差/稳定性汇总")
    ap.add_argument("reports", nargs="*", help="K 份评测报告 JSON（同候选、不同裁判/种子）")
    ap.add_argument("--demo", action="store_true", help="用 mock 打分演示方差报告（无需 API、无需输入文件）")
    args = ap.parse_args()

    if args.demo:
        demo()
        return
    if not args.reports:
        print("✗ 需传入 K 份报告 JSON，或加 --demo 看演示。")
        sys.exit(2)

    reports = load_reports(args.reports)
    rows = build_variance_table(reports)
    print(render_table(rows))
    low = [r for r in rows if "低" in r["conf"]]
    if low:
        print(f"\n⚠️ {len(low)} 条用例置信低（判分波动），不应单凭一次 pass 宣称达标。")


if __name__ == "__main__":
    main()
