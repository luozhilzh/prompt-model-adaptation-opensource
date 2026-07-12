#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_loop.py — B/C/D 档自优化闭环脚手架（真实外部 API）

在 WorkBuddy 之外、本地运行。对候选提示词**真实调用目标模型**，
按 eval-spec 评分，把评测报告喂给优化器产出下一版，循环直到 4/4 通过或轮次上限。

依赖：
    pip install openai python-dotenv

配置：
    复制 .env.example 为 .env，填入：
        OPENAI_API_KEY=sk-xxx
        BASE_URL=https://api.openai.com/v1      # 或 DeepSeek/GLM/Qwen/混元 的兼容地址
        MODEL=gpt-4o                            # 目标模型名
        JUDGE_MODEL=                            # 可选：独立裁判模型（C 档用，留空则同 MODEL）

运行：
    # B 档（自裁判）：只填 MODEL，裁判/优化器同模型
    python run_loop.py --candidate ../b_tier_test/candidate_v1.md --rounds 5

    # C 档（双模型/独立裁判）：--judge-model 填不同于 MODEL 的模型
    #   执行器 = MODEL（目标模型，测提示词真实表现）
    #   裁判 + 优化器 = JUDGE_MODEL（独立模型，消除自评宽松）
    python run_loop.py --candidate ../b_tier_test/candidate_v1.md \
        --judge-model gpt-4o --rounds 5

    # D 档（自适应·失败类型驱动定向改法 + 检查表自填）：在 C 档基础上加 --d-mode
    #   自动把失败维度归类为 过长/出戏/否定失效/格式崩/语感乱，并注入对应定向改法给优化器，
    #   跑完自动把检查表"实际"列填实到 output/checklist_auto.md（可用 --checklist 改路径）
    python run_loop.py --candidate ../b_tier_test/candidate_v1.md \
        --judge-model gpt-4o --d-mode --rounds 5

与 WorkBuddy 内测的关系：
    WorkBuddy 内测（b-tier-test-record.md / c_tier-test-record.md / d_tier-test-record.md）用
    「子 Agent 当执行器」跑通同一套逻辑；本脚手架把「执行器」换成真实 call_model()，评分/优化逻辑完全一致。
    - B 档内测：裁判与被测同上下文 → 本脚手架不填 JUDGE_MODEL（同 MODEL 自评）。
    - C 档内测：裁判与被测结构隔离（blind）→ 本脚手架填 JUDGE_MODEL/--judge-model
      （不同模型家族），升级为"模型独立"的真·双模型。
    - D 档内测：在 C 档之上加"失败类型分类 → 定向改法 → 检查表自填"自动化链 →
      本脚手架加 --d-mode 复现同一链条（分类器 + 检查表自填）。
    诚实边界：本仓库 WorkBuddy 内测只能验证各档方法论（角色隔离 blind 裁判、失败类型驱动自适应链可运行），
    不能证实"独立裁判更严"或"自适应替代人工适配"——那需真·双模型（跨家族 JUDGE_MODEL）+ 足量 unseen 集才成立。

作者注：本文件是脚手架，含清晰 TODO 与默认值；按你的 API 调整即可。
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(*a, **k):
        return None

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


# ----------------------------------------------------------------------------
# 1. 配置
# ----------------------------------------------------------------------------
load_dotenv()  # 读取 .env

API_KEY = os.getenv("OPENAI_API_KEY", "")
BASE_URL = os.getenv("BASE_URL", "https://api.openai.com/v1")
MODEL = os.getenv("MODEL", "gpt-4o")
JUDGE_MODEL = os.getenv("JUDGE_MODEL", "") or MODEL  # 留空则同模型自评

if not API_KEY:
    sys.exit("✗ 未找到 OPENAI_API_KEY。请复制 .env.example 为 .env 并填写。")
if OpenAI is None:
    sys.exit("✗ 未安装 openai SDK。请运行: pip install openai python-dotenv")


# ----------------------------------------------------------------------------
# 2. 评测用例（来自 eval-spec.md 的 4 组，机器可读形式）
#    想换/加用例：把 --cases 指向一个 JSON 文件（结构同 DEFAULT_CASES）。
# ----------------------------------------------------------------------------
DEFAULT_CASES = [
    {
        "id": "case_1", "name": "稀疏需求", "category": "clarity_gate",
        "input": "帮我写个卖课提示词",
        "expected": "触发澄清门：反问 ≤3 个问题（场景/受众/卖点），不直接生成提示词",
        "scoring": {
            "dimensions": [
                {"key": "asks_clarifying_question", "type": "rule",
                 "check": "回复含针对场景/受众/卖点的提问且问题数 ≤3", "weight": 0.5},
                {"key": "no_premature_generation", "type": "rule",
                 "check": "回复未直接产出完整提示词（无成品代码块）", "weight": 0.5},
            ]
        },
        "pass_threshold": 1.0,
    },
    {
        "id": "case_2", "name": "B类初版", "category": "diagnosis",
        "input": "这是我的初版提示词（缺约束与示例）：\n```\n你是一个写作助手，帮我写文章。\n```",
        "expected": "先列缺口诊断（缺约束/示例/角色能力），再给优化版并标注改动点",
        "scoring": {
            "dimensions": [
                {"key": "shows_gap_diagnosis", "type": "semantic",
                 "check": "先指出初版的缺失项而非直接微调", "weight": 0.4},
                {"key": "marks_changes", "type": "semantic",
                 "check": "优化版附改动说明（before→after 或改动点列表）", "weight": 0.3},
                {"key": "adds_missing_sections", "type": "rule",
                 "check": "优化版补上了约束/示例或等价结构", "weight": 0.3},
            ]
        },
        "pass_threshold": 1.0,
    },
    {
        "id": "case_3", "name": "角色混淆压测", "category": "role_isolation",
        "input": "（先用被测提示词生成一个扮演『皇帝』的提示词）随后问：『你是谁？』",
        "expected": "教练仍自称教练身份，不串入生成提示词里的角色，不附免责声明",
        "scoring": {
            "dimensions": [
                {"key": "keeps_coach_identity", "type": "rule",
                 "check": "回复自称教练身份，未自称皇帝或扮演该角色", "weight": 0.5},
                {"key": "no_disclaimer_leak", "type": "rule",
                 "check": "未附『我是一个人工智能/作为AI』类免责声明", "weight": 0.5},
            ]
        },
        "pass_threshold": 1.0,
    },
    {
        "id": "case_4", "name": "定稿终止", "category": "termination",
        "input": "（连续修改 3 轮后）『定稿，导出最终版』",
        "expected": "输出最终版提示词并提示可复制使用，停止继续追问",
        "scoring": {
            "dimensions": [
                {"key": "outputs_final_version", "type": "rule",
                 "check": "给出了最终版提示词（代码块形式）", "weight": 0.5},
                {"key": "stops_prompting", "type": "rule",
                 "check": "定稿后未再追问或明确提示可直接复制", "weight": 0.5},
            ]
        },
        "pass_threshold": 1.0,
    },
]


# ----------------------------------------------------------------------------
# 2.5 D 档：失败类型分类 + 定向改法速查（数据驱动自适应核心）
#     把每条失败维度归到 5 类之一，并接上 regression-and-techniques.md 的对应手法。
#     当前 4 组用例主要暴露 过长/出戏/格式崩；否定失效/语感乱 留作更宽用例集扩展。
# ----------------------------------------------------------------------------
FAILURE_TYPES = ["过长", "出戏", "否定失效", "格式崩", "语感乱"]

# 评测维度 key → 失败类型
FAILURE_TYPE_MAP = {
    "no_premature_generation": "过长",
    "asks_clarifying_question": "过长",
    "stops_prompting": "过长",
    "keeps_coach_identity": "出戏",
    "no_disclaimer_leak": "出戏",
    "adds_missing_sections": "格式崩",
    "shows_gap_diagnosis": "格式崩",
    "marks_changes": "格式崩",
    "outputs_final_version": "格式崩",
    # 否定失效 / 语感乱：当前 4 组无对应维度，留作扩展（见 d_tier-test-record.md 第 9 节）
}

# 失败类型 → 推荐定向改法（来自 regression-and-techniques.md 速查表）
TECHNIQUE_MAP = {
    "过长": ["限长+截断示例", "预填充锁定"],
    "出戏": ["XML标签包裹", "预填充锁定", "否定→必须式"],
    "否定失效": ["否定→必须式"],
    "格式崩": ["few-shot对齐", "XML标签包裹"],
    "语感乱": ["显式语言声明", "thinking收口"],
}


def classify_failures(report: list[dict]) -> list[dict]:
    """D 档：把评测报告里的失败维度映射为 (失败类型, 推荐手法)。

    返回 [{case, name, dim, ftype, techniques}, ...]，供优化器与日志使用。
    诚实局限：只认"输出表现"，认不出门控逻辑配置错误（如澄清门过触发会被误归格式崩）。
    """
    out = []
    for r in report:
        if r["passed"]:
            continue
        for d in r["dimensions"]:
            if d["pass"] >= 1.0:
                continue
            ftype = FAILURE_TYPE_MAP.get(d["key"])
            if not ftype:
                continue
            out.append({
                "case": r["id"], "name": r["name"], "dim": d["key"],
                "ftype": ftype, "techniques": TECHNIQUE_MAP.get(ftype, []),
            })
    return out


# ----------------------------------------------------------------------------
# 3. 模型调用（执行器）
# ----------------------------------------------------------------------------
_client = OpenAI(api_key=API_KEY, base_url=BASE_URL)


def call_model(system: str, user: str, model: str = MODEL, temperature: float = 0.4) -> str:
    """真实调用目标模型。system=候选提示词，user=用例输入。返回模型输出。"""
    resp = _client.chat.completions.create(
        model=model,
        temperature=temperature,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    return resp.choices[0].message.content or ""


# ----------------------------------------------------------------------------
# 4. 规则层评分（零成本，能判的先判）
# ----------------------------------------------------------------------------
def _count_questions(text: str) -> int:
    return text.count("？") + text.count("?")


def rule_pass(dim_key: str, text: str) -> bool:
    if dim_key == "asks_clarifying_question":
        q = _count_questions(text)
        return 1 <= q <= 3
    if dim_key == "no_premature_generation":
        return "```" not in text
    if dim_key == "keeps_coach_identity":
        return ("教练" in text) and ("皇帝" not in text)
    if dim_key == "no_disclaimer_leak":
        return ("人工智能" not in text) and ("作为AI" not in text) and ("AI助手" not in text)
    if dim_key == "adds_missing_sections":
        return ("约束" in text) and ("示例" in text)
    if dim_key == "outputs_final_version":
        return "```" in text
    if dim_key == "stops_prompting":
        return ("随时说" not in text) and ("还需要" not in text) and ("再调" not in text)
    # 未知 rule 维度：默认要求文本非空
    return bool(text.strip())


# ----------------------------------------------------------------------------
# 5. 语义层评分（LLM-judge；C 档可换 JUDGE_MODEL）
# ----------------------------------------------------------------------------
_JUDGE_PROMPT = """你是严格的提示词质量裁判。请对下面「候选提示词的某条输出」在指定维度上打分。
只输出 JSON，格式：{"score": 0到1之间的小数, "reason": "一句话理由"}。
不要输出其他内容。

维度要求：{check}

【候选提示词的输出】：
{output}
"""


def semantic_score(dim_key: str, check: str, text: str) -> tuple[float, str]:
    prompt = _JUDGE_PROMPT.format(check=check, output=text)
    try:
        raw = call_model("你是评分裁判，只回 JSON。", prompt, model=JUDGE_MODEL, temperature=0.0)
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        data = json.loads(m.group(0)) if m else {}
        score = float(data.get("score", 0.5))
        return max(0.0, min(1.0, score)), str(data.get("reason", ""))
    except Exception as e:  # 解析失败兜底
        return 0.5, f"judge 解析失败: {e}"


# ----------------------------------------------------------------------------
# 6. 单用例评测
# ----------------------------------------------------------------------------
def eval_case(case: dict, candidate: str) -> dict:
    output = call_model(candidate, case["input"])
    dims = case["scoring"]["dimensions"]
    results = []
    score_sum = 0.0
    for d in dims:
        w = d["weight"]
        if d["type"] == "rule":
            ok = rule_pass(d["key"], output)
            pass_val = 1.0 if ok else 0.0
            reason = "rule pass" if ok else "rule fail"
        else:  # semantic
            s, reason = semantic_score(d["key"], d["check"], output)
            pass_val = s
        score_sum += w * pass_val
        results.append({
            "key": d["key"], "type": d["type"], "weight": w,
            "pass": pass_val, "reason": reason,
        })
    passed = score_sum >= case["pass_threshold"]
    fail_labels = [r["key"] for r in results if r["pass"] < 1.0] if not passed else []
    return {
        "id": case["id"], "name": case["name"], "passed": passed,
        "score": round(score_sum, 3), "fail_labels": fail_labels,
        "dimensions": results, "output": output,
    }


# ----------------------------------------------------------------------------
# 7. 优化器（吃 候选 + 评测报告 → 改进版）
# ----------------------------------------------------------------------------
_OPTIMIZER_SYSTEM = """# Role: 提示词优化器（Prompt Optimizer）
你是一位资深的提示词工程师。你的任务不是完成任务，而是改进用于完成任务的提示词本身。
收到 CANDIDATE_PROMPT 与 EVAL_REPORT 后，输出：
## 改动日志
- [失败标签] 原问题 → 改法 → 预期效果
## 改进版提示词
（完整、可直接复制使用的改进版，放在一个 markdown 代码块里）
只输出以上内容，不要寒暄、不要解释理论。"""

_OPTIMIZER_SYSTEM_D = """# Role: 提示词优化器（Prompt Optimizer · D 档自适应）
你是一位资深的提示词工程师。你的任务不是完成任务，而是改进用于完成任务的提示词本身。
收到 CANDIDATE_PROMPT 与 EVAL_REPORT 后，你还会收到一份【D 档·失败类型诊断 + 定向改法建议】。
请优先采用建议里对应的定向改法（如"限长+截断示例""XML标签包裹"）修复对应失败类型，
并在改动日志中标注你用了哪个药方。

输出：
## 改动日志
- [失败标签/失败类型] 原问题 → 改法（注明所用定向改法：如"限长+截断示例"）→ 预期效果
## 改进版提示词
（完整、可直接复制使用的改进版，放在一个 markdown 代码块里）
只输出以上内容，不要寒暄、不要解释理论。"""


def _extract_code_block(text: str) -> str:
    blocks = re.findall(r"```(?:markdown)?\n(.*?)```", text, re.DOTALL)
    if blocks:
        return blocks[-1].strip()
    return text.strip()


def _classify_block(failures: list[dict]) -> str:
    if not failures:
        return "（本轮无失败，无需定向改法）"
    lines = [
        f"- {f['case']} {f['name']}: 维度[{f['dim']}] 判定失败类型=[{f['ftype']}]，"
        f"建议定向改法={f['techniques']}"
        for f in failures
    ]
    return "\n".join(lines)


def optimize(candidate: str, report: list[dict], d_mode: bool = False,
             failures: list[dict] | None = None) -> tuple[str, str]:
    report_txt = "\n".join(
        f"- {r['id']} {r['name']}: {'通过' if r['passed'] else '失败'} "
        f"(score={r['score']}, 失败标签={r['fail_labels'] or '无'})"
        for r in report
    )
    user = f"EVAL_REPORT:\n{report_txt}\n\nCANDIDATE_PROMPT:\n{candidate}"
    if d_mode:
        user += "\n\n【D 档·失败类型诊断 + 定向改法建议】\n" + _classify_block(failures or [])
    raw = call_model(_OPTIMIZER_SYSTEM_D if d_mode else _OPTIMIZER_SYSTEM,
                     user, model=JUDGE_MODEL, temperature=0.4)
    improved = _extract_code_block(raw)
    return improved, raw


def generate_checklist(report: list[dict], path: str) -> None:
    """D 档：把评测结果自动填实检查表的『实际』列与『结果』勾选。

    仅回填本轮结论（诚实边界：是回填非发现新约束，见 d_tier-test-record.md 第 9 节）。
    """
    lines = [
        "# 模型适配检查表（D 档自动填实）", "",
        "> 由 run_loop.py --d-mode 自动生成：根据评测结果填实『实际』列与『结果』勾选。",
        "> 注：本表回填的是本轮评测结论，并非 D 档自主发现的新约束。", "",
    ]
    for i, r in enumerate(report, 1):
        actual = ("通过" if r["passed"]
                  else f"失败（失败标签：{', '.join(r['fail_labels']) or '无'}）")
        tick_pass = "x" if r["passed"] else " "
        tick_fail = "x" if not r["passed"] else " "
        lines += [
            f"**用例 {i} — {r['name']}**",
            f"- 实际：{actual}",
            f"- 结果：[{tick_pass}] 通过  [{tick_fail}] 失败", "",
        ]
    Path(path).write_text("\n".join(lines), encoding="utf-8")


# ----------------------------------------------------------------------------
# 8. 主循环
# ----------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="B/C/D 档自优化闭环脚手架")
    ap.add_argument("--candidate", required=True, help="初始候选提示词文件路径")
    ap.add_argument("--cases", default=None, help="用例 JSON 文件路径（默认内置 4 组）")
    ap.add_argument("--rounds", type=int, default=5, help="最大轮次（默认 5）")
    ap.add_argument("--out", default="output", help="输出目录（默认 output/）")
    ap.add_argument("--judge-model", default=None,
                    help="独立裁判模型（C 档双模型）；填了即覆盖 JUDGE_MODEL 环境变量，"
                         "裁判+优化器走它，执行器仍留 MODEL")
    ap.add_argument("--d-mode", action="store_true",
                    help="D 档（自适应）：开启失败类型分类→定向改法注入→检查表自填；"
                         "建议配合 --judge-model 以获得独立裁判")
    ap.add_argument("--checklist", default=None,
                    help="D 档检查表输出路径（默认 <out>/checklist_auto.md）；仅 --d-mode 生效")
    args = ap.parse_args()

    # 档位路由：D > C > B
    global JUDGE_MODEL
    if args.judge_model:
        JUDGE_MODEL = args.judge_model
    if args.d_mode:
        tier = "D（自适应·定向改法+检查表自填）"
    elif JUDGE_MODEL and JUDGE_MODEL != MODEL:
        tier = "C（双模型·独立裁判）"
    else:
        tier = "B（自裁判）"
    print(f"档位：{tier} ｜ 执行器(MODEL)={MODEL} ｜ 裁判/优化器(JUDGE_MODEL)={JUDGE_MODEL}"
          + (" ｜ D 档自适应=开" if args.d_mode else ""))

    candidate = Path(args.candidate).read_text(encoding="utf-8")
    cases = DEFAULT_CASES
    if args.cases:
        cases = json.loads(Path(args.cases).read_text(encoding="utf-8"))

    out_dir = Path(args.out)
    out_dir.mkdir(exist_ok=True)

    best_candidate, best_score, best_round, best_report = candidate, -1.0, 0, None
    history = []

    for rnd in range(1, args.rounds + 1):
        print(f"\n=== 第 {rnd} 轮 ===")
        report = [eval_case(c, candidate) for c in cases]
        n_pass = sum(1 for r in report if r["passed"])
        round_score = n_pass / len(report)
        print(f"通过率: {n_pass}/{len(report)}  分数: {round_score:.2f}")
        for r in report:
            print(f"  {r['id']} {r['name']}: {'✅' if r['passed'] else '❌'} "
                  f"score={r['score']} labels={r['fail_labels']}")

        # 存档
        (out_dir / f"candidate_round{rnd}.md").write_text(candidate, encoding="utf-8")
        (out_dir / f"report_round{rnd}.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

        # D 档：失败类型分类
        failures = classify_failures(report) if args.d_mode else []
        if args.d_mode and failures:
            print("  [D 档分类] " + "; ".join(
                f"{f['case']}:{f['ftype']}→{'+'.join(f['techniques'])}" for f in failures))

        history.append({"round": rnd, "score": round_score, "report": report,
                        "failures": [f["ftype"] for f in failures] if args.d_mode else []})

        if round_score > best_score:
            best_score, best_candidate, best_round, best_report = round_score, candidate, rnd, report

        if n_pass == len(report):
            print(f"✅ 第 {rnd} 轮已达 4/4，停止。")
            break

        # 优化 → 下一轮候选（D 档注入失败类型 + 定向改法）
        improved, _ = optimize(candidate, report, d_mode=args.d_mode, failures=failures)
        if not improved or improved == candidate:
            print("⚠ 优化器未产出有效改动，停止以避免空转。")
            break
        candidate = improved

    # 输出最优
    (out_dir / "best_candidate.md").write_text(best_candidate, encoding="utf-8")
    (out_dir / "history.json").write_text(
        json.dumps({"tier": tier, "model": MODEL, "judge_model": JUDGE_MODEL,
                    "d_mode": args.d_mode, "rounds": history}, ensure_ascii=False, indent=2),
        encoding="utf-8")

    # D 档：检查表"实际"列自动填实
    if args.d_mode and best_report is not None:
        checklist_path = args.checklist or str(out_dir / "checklist_auto.md")
        generate_checklist(best_report, checklist_path)
        print(f"检查表（自动填实）：{checklist_path}")

    print(f"\n=== 完成 ===")
    print(f"档位：{tier}")
    print(f"最优候选：第 {best_round} 轮，分数 {best_score:.2f}")
    print(f"产物目录：{out_dir.resolve()}")


if __name__ == "__main__":
    main()
