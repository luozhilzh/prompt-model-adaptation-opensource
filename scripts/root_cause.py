#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
root_cause.py — Phase 3 优化器智能化：表象失败 → 根因诊断（离线工具）

用途：给定一份评测报告（结构同 run_loop.py 产出的 report_roundN.json），
      把每条失败维度上溯到根因（见 run_loop.ROOT_CAUSE_MAP），打印根因诊断。

输入格式：JSON 文件，结构同 run_loop 的 report —— 一个 case 列表，每个 case 含
          {"id", "name", "passed": bool, "dimensions": [{"key", "pass": 0~1, ...}]}。
          或直接是 run_loop 的 history.json（自动取 rounds[-1].report）。

⚠️ 诚实边界：本脚本只做"表象→根因"映射，不调用模型、不需要 API key。
   --demo 用 mock 失败报告，仅验证映射与工具能跑，不代表真实根因判断。
   真实根因分类需足量跨模型漂移数据 + 人工验证映射正确性。

依赖：仅标准库 + 同仓库 scripts/run_loop.py（ROOT_CAUSE_MAP / classify_failures）。
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

import run_loop as R  # noqa: E402


def load_report(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    # 兼容 history.json（取最后一轮 report）或直接是 report 列表
    if isinstance(data, dict) and "rounds" in data and data["rounds"]:
        return data["rounds"][-1].get("report", [])
    if isinstance(data, dict) and "report" in data:
        return data["report"]
    return data  # 直接是 case 列表


def render(diag):
    if not diag:
        return "（无失败 → 无需根因诊断）\n"
    head = "| 用例 | 维度 | 表象类型 | 根因 |\n"
    sep = "|---|---|---|---|\n"
    lines = [head, sep]
    for d in diag:
        lines.append(
            f"| {d['case']} {d['name']} | {d['dim']} | {d['surface_ftype']} | {d['root_cause']} |\n"
        )
    return "".join(lines)


def demo():
    # mock 一份含失败的评测报告（case_3 串角色 + case_4 未终止 + case_2 缺结构）
    report = [
        {"id": "case_1", "name": "稀疏需求", "passed": True, "dimensions": [
            {"key": "asks_clarifying_question", "pass": 1.0}]},
        {"id": "case_2", "name": "B类初版", "passed": False, "dimensions": [
            {"key": "adds_missing_sections", "pass": 0.0}]},
        {"id": "case_3", "name": "角色压测", "passed": False, "dimensions": [
            {"key": "keeps_coach_identity", "pass": 0.0},
            {"key": "no_disclaimer_leak", "pass": 0.0}]},
        {"id": "case_4", "name": "定稿终止", "passed": False, "dimensions": [
            {"key": "stops_prompting", "pass": 0.0}]},
    ]
    diag = R.root_cause_diagnosis(report)
    print("=" * 64)
    print("⚠️  DEMO 模式（mock 失败报告，非真实根因判断）")
    print("=" * 64)
    print(render(diag))
    print("判读：case_3 的两条失败都归到根因『角色未锚』→ 优化器应锁系统角色+禁免责，")
    print("      而非分别对两条维度各打一个补丁（治本 > 治标）。")


def main():
    ap = argparse.ArgumentParser(description="Phase 3 根因诊断：评测报告 → 根因映射")
    ap.add_argument("report", nargs="?", help="评测报告 JSON（run_loop 的 report / history.json）")
    ap.add_argument("--demo", action="store_true", help="用 mock 失败报告演示根因诊断（无需 API、无需输入文件）")
    args = ap.parse_args()

    if args.demo:
        demo()
        return
    if not args.report:
        print("✗ 需传入评测报告 JSON，或加 --demo 看演示。")
        sys.exit(2)

    report = load_report(args.report)
    diag = R.root_cause_diagnosis(report)
    print(render(diag))


if __name__ == "__main__":
    main()
