"""Create problem-level error summaries from attempt-level main-run data."""
import argparse
import csv
import json
import pathlib
from collections import Counter, defaultdict

p = argparse.ArgumentParser()
p.add_argument("--attempts", required=True)
p.add_argument("--benchmark", required=True)
p.add_argument("--output", required=True)
a = p.parse_args()

attempts = list(csv.DictReader(open(a.attempts, newline="")))
benchmark = {str(x["question_id"]): x for x in json.load(open(a.benchmark))}
out = pathlib.Path(a.output)
out.mkdir(parents=True, exist_ok=True)

groups = defaultdict(list)
for row in attempts:
    groups[(row["model"], row["condition"], str(row["problem_id"]))].append(row)

rows = []
for (model, condition, qid), rs in sorted(groups.items()):
    meta = benchmark[qid]
    evaluated = [r for r in rs if r["status"] == "evaluated" and r["passed"] in {"0", "1"}]
    technical = [r for r in rs if r["status"] == "technical_error"]
    wrong = [r for r in evaluated if r["passed"] == "0"]
    reasons = Counter(r["error_type"] for r in rs if r["status"] == "technical_error")
    rows.append({
        "problem_id": qid, "title": meta.get("question_title", ""),
        "difficulty": meta.get("difficulty", ""), "platform": meta.get("platform", ""),
        "model": model, "condition": condition, "attempts": len(rs),
        "passed": sum(r["passed"] == "1" for r in evaluated),
        "evaluated": len(evaluated), "wrong_answer": len(wrong),
        "technical_failures": len(technical),
        "technical_types": ";".join(f"{k}:{v}" for k, v in sorted(reasons.items())),
        "pass_rate_evaluated": (sum(r["passed"] == "1" for r in evaluated) / len(evaluated)
                                if evaluated else ""),
    })

fields = list(rows[0])
with (out / "problem_level.csv").open("w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(rows)

by = {(r["model"], r["condition"], r["problem_id"]): r for r in rows}
models = sorted({r["model"] for r in rows})
problem_ids = sorted({r["problem_id"] for r in rows}, key=lambda x: int(x))
comparison = []
for model in models:
    for qid in problem_ids:
        c, t = by[(model, "cot", qid)], by[(model, "tdd", qid)]
        comparison.append({
            "model": model, "problem_id": qid, "title": c["title"],
            "difficulty": c["difficulty"], "cot_passed": c["passed"],
            "tdd_passed": t["passed"], "cot_technical": c["technical_failures"],
            "tdd_technical": t["technical_failures"],
            "delta_passes": t["passed"] - c["passed"],
            "delta_conservative_passes": (t["passed"] - t["technical_failures"])
                                      - (c["passed"] - c["technical_failures"]),
        })

with (out / "problem_comparison.csv").open("w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(comparison[0])); w.writeheader(); w.writerows(comparison)

summary = {"rows": len(rows), "models": models, "problems": len(problem_ids),
           "problem_level": rows, "comparison": comparison}
(out / "problem_level.json").write_text(json.dumps(summary, indent=2))

def fmt_problem(qid):
    m = benchmark[qid]
    return f"{qid} — {m.get('question_title','')} ({m.get('difficulty','')})"

lines = ["# Main-run problem-level error analysis", "",
         "This report uses the frozen 100-problem LiveCodeBench release-v6 manifest. "
         "A wrong answer is an evaluated failure; API errors and truncations remain technical failures.", ""]
for model in models:
    lines += [f"## {model}", ""]
    for condition in ("cot", "tdd"):
        rr = [r for r in rows if r["model"] == model and r["condition"] == condition]
        wrong = [r for r in rr if r["wrong_answer"]]
        tech = [r for r in rr if r["technical_failures"]]
        lines += [f"**{condition.upper()}**: {sum(r['passed'] for r in rr)}/"
                  f"{sum(r['evaluated'] for r in rr)} evaluated passes; "
                  f"{sum(r['technical_failures'] for r in rr)} technical failures."]
        if wrong:
            lines.append("Wrong-answer problems: " + ", ".join(fmt_problem(r["problem_id"]) for r in wrong))
        if tech:
            lines.append("Technical-failure problems: " + ", ".join(
                f"{fmt_problem(r['problem_id'])} [{r['technical_types']}]" for r in tech))
        lines.append("")

lines += ["## Cross-model patterns", ""]
for condition in ("cot", "tdd"):
    missed = []
    for qid in problem_ids:
        rs = [by[(m, condition, qid)] for m in models]
        if all(r["passed"] == 0 and r["technical_failures"] == 0 for r in rs):
            missed.append(fmt_problem(qid))
    lines.append(f"Problems with zero evaluated passes for every model in {condition.upper()}: "
                 + (", ".join(missed) if missed else "none") + ".")
lines += ["", "See `problem_level.csv` for one row per model/condition/problem and "
          "`problem_comparison.csv` for paired CoT-versus-TDD counts."]
(out / "error_analysis.md").write_text("\n".join(lines) + "\n")
print(f"Wrote {len(rows)} problem rows and {len(comparison)} paired rows to {out}")
