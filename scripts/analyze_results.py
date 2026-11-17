import argparse, csv, json, math, pathlib, random, statistics
from collections import defaultdict

def mean(xs): return sum(xs)/len(xs) if xs else float("nan")

def bootstrap_ci(values, reps=10000, seed=20261114):
    rng = random.Random(seed)
    n = len(values)
    sims = sorted(mean([values[rng.randrange(n)] for _ in range(n)]) for _ in range(reps))
    return sims[int(.025*reps)], sims[min(reps-1, int(.975*reps))]

def signflip_p(values, reps=20000, seed=20261114):
    rng = random.Random(seed)
    obs = abs(mean(values))
    ge = 0
    n = len(values)
    for _ in range(reps):
        s = mean([v if rng.random() < .5 else -v for v in values])
        if abs(s) >= obs - 1e-15: ge += 1
    return (ge+1)/(reps+1)

def holm(pvals):
    order = sorted(range(len(pvals)), key=lambda i:pvals[i])
    out = [0.0]*len(pvals)
    running = 0.0
    m = len(pvals)
    for rank, idx in enumerate(order):
        val = min(1.0, (m-rank)*pvals[idx])
        running = max(running, val)
        out[idx] = running
    return out

p=argparse.ArgumentParser()
p.add_argument("--input", required=True)
p.add_argument("--output", default="results/analysis")
p.add_argument("--bootstrap-reps", type=int, default=10000)
p.add_argument("--permutation-reps", type=int, default=20000)
a=p.parse_args()

rows=list(csv.DictReader(open(a.input, newline="")))
required={"problem_id","model","condition","attempt","status","passed"}
if not rows or not required.issubset(rows[0]):
    raise SystemExit(f"CSV must include columns: {sorted(required)}")
models=sorted({r["model"] for r in rows})
conditions={"cot","tdd"}
if not conditions.issubset({r["condition"] for r in rows}):
    raise SystemExit("Both cot and tdd conditions are required.")

# Per problem/model/condition aggregate only valid evaluated attempts.
vals=defaultdict(list); conservative=defaultdict(list); tech=defaultdict(int); total=defaultdict(int)
for r in rows:
    key=(r["model"],r["condition"],r["problem_id"])
    total[key]+=1
    conservative[key].append(int(r["passed"]) if r["passed"] in {"0","1"} else 0)
    if r["status"]=="technical_error" or r["passed"]=="":
        tech[(r["model"],r["condition"])]+=1
        continue
    if r["status"]!="evaluated" or r["passed"] not in {"0","1"}:
        raise SystemExit(f"Invalid row status/outcome: {r}")
    vals[key].append(int(r["passed"]))

# Descriptive rates and paired problem-level differences.
report={"input":a.input,"models":{},"overall":{},"notes":[
    "Technical errors are excluded from correctness denominators and reported separately.",
    "Uncertainty resamples whole problem IDs; attempts within a problem are not treated as independent clusters.",
    "Model-specific permutation p-values are Holm-adjusted."
]}
model_diffs={}
for m in models:
    rates={}
    per_problem={}
    for c in ["cot","tdd"]:
        allv=[x for (mm,cc,pid),xs in vals.items() if mm==m and cc==c for x in xs]
        matching=[r for r in rows if r["model"]==m and r["condition"]==c]
        def numeric(field):
            return [float(r[field]) for r in matching if r.get(field) not in (None,"")]
        costs=numeric("cost_usd"); latencies=numeric("latency_seconds")
        inputs=numeric("input_tokens"); outputs=numeric("output_tokens")
        attempts_total=sum(v for (mm,cc,pid),v in total.items() if mm==m and cc==c)
        rates[c]={"passed":sum(allv),"evaluated":len(allv),
                  "pass_rate":mean(allv) if allv else None,
                  "technical_errors":tech[(m,c)],
                  "attempts_total":attempts_total,
                  "conservative_pass_rate":sum(allv)/attempts_total if attempts_total else None,
                  "input_tokens_total":sum(inputs) if inputs else None,
                  "output_tokens_total":sum(outputs) if outputs else None,
                  "cost_usd_total":sum(costs) if costs else None,
                  "latency_seconds_mean":mean(latencies) if latencies else None}
    pids=sorted({pid for (mm,cc,pid) in vals if mm==m and cc in conditions})
    for pid in pids:
        cvals=vals.get((m,"cot",pid),[])
        tvals=vals.get((m,"tdd",pid),[])
        if cvals and tvals:
            per_problem[pid]=mean(tvals)-mean(cvals)
    diffs=list(per_problem.values())
    model_diffs[m]=diffs
    if diffs:
        lo,hi=bootstrap_ci(diffs,a.bootstrap_reps,seed=20261114+len(m))
        pv=signflip_p(diffs,a.permutation_reps,seed=20261114+len(m))
        effect=mean(diffs)
    else:
        lo=hi=pv=effect=None
    report["models"][m]={"rates":rates,"paired_problem_count":len(diffs),
                         "tdd_minus_cot_pp":effect*100 if effect is not None else None,
                         "cluster_bootstrap_95ci_pp":[lo*100,hi*100] if lo is not None else None,
                         "signflip_p":pv}
# Overall paired average across models, first average within model/problem then across models available.
overall_problem=defaultdict(list)
for m,diffs in model_diffs.items():
    # Build keyed values to ensure model contributes paired problem effect
    for pid in sorted({pid for (mm,cc,pid) in vals if mm==m}):
        cvals=vals.get((m,"cot",pid),[]); tvals=vals.get((m,"tdd",pid),[])
        if cvals and tvals: overall_problem[pid].append(mean(tvals)-mean(cvals))
overall_diffs=[mean(v) for v in overall_problem.values() if v]
if overall_diffs:
    lo,hi=bootstrap_ci(overall_diffs,a.bootstrap_reps)
    report["overall"]={"paired_problem_count":len(overall_diffs),
        "tdd_minus_cot_pp":mean(overall_diffs)*100,
        "cluster_bootstrap_95ci_pp":[lo*100,hi*100],
        "signflip_p":signflip_p(overall_diffs,a.permutation_reps)}
else: report["overall"]={"error":"No complete paired problem observations."}
# Sensitivity analysis: count every technical failure as an incorrect generation.
sensitivity=defaultdict(list)
for m in models:
    for pid in sorted({pid for (mm,cc,pid) in conservative if mm==m}):
        cv=conservative.get((m,"cot",pid),[]); tv=conservative.get((m,"tdd",pid),[])
        if cv and tv: sensitivity[pid].append(mean(tv)-mean(cv))
sensitivity_diffs=[mean(x) for x in sensitivity.values() if x]
if sensitivity_diffs:
    lo,hi=bootstrap_ci(sensitivity_diffs,a.bootstrap_reps,seed=20261115)
    report["sensitivity_technical_as_failure"]={"paired_problem_count":len(sensitivity_diffs),
        "tdd_minus_cot_pp":mean(sensitivity_diffs)*100,
        "cluster_bootstrap_95ci_pp":[lo*100,hi*100],
        "signflip_p":signflip_p(sensitivity_diffs,a.permutation_reps,seed=20261115)}
valid_models=[m for m in models if report["models"][m]["signflip_p"] is not None]
adjusted=holm([report["models"][m]["signflip_p"] for m in valid_models])
for m,pv in zip(valid_models,adjusted):
    report["models"][m]["holm_adjusted_p"]=pv

out=pathlib.Path(a.output); out.mkdir(parents=True,exist_ok=True)
(out/"analysis.json").write_text(json.dumps(report,indent=2))
with (out/"summary.csv").open("w",newline="") as f:
    w=csv.writer(f); w.writerow(["model","condition","passed","evaluated","pass_rate","technical_errors","attempts_total"])
    for m in models:
        for c in ["cot","tdd"]:
            x=report["models"][m]["rates"][c]
            w.writerow([m,c,x["passed"],x["evaluated"],x["pass_rate"],x["technical_errors"],x["attempts_total"]])
print(json.dumps(report,indent=2))
print(f"\nSaved {out/'analysis.json'} and {out/'summary.csv'}")
