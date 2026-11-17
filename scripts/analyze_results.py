import argparse, csv, json, math, pathlib, random, statistics
from collections import defaultdict, Counter

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
keys = [(r['problem_id'], r['model'], r['condition'], r['attempt']) for r in rows]
if len(set(keys)) != len(keys):
    raise SystemExit('Duplicate problem/model/condition/attempt rows')
expected = {(pid, m, c, attempt) for pid in {r['problem_id'] for r in rows}
            for m in {r['model'] for r in rows} for c in ('cot', 'tdd')
            for attempt in ('1', '2', '3')}
if set(keys) != expected:
    raise SystemExit('Incomplete or unexpected design: expected three attempts in every problem/model/condition cell')
if any(r['status'] not in ('evaluated', 'technical_error') or
       (r['status'] == 'evaluated' and r['passed'] not in ('0', '1')) or
       (r['status'] == 'technical_error' and r['passed'] != '') for r in rows):
    raise SystemExit('Invalid status/outcome combination')
if a.bootstrap_reps < 1 or a.permutation_reps < 1:
    raise SystemExit('Resampling counts must be positive')
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
report['model_sensitivity_technical_as_failure'] = {}
for m in models:
    ds = [mean(conservative[(m,'tdd',pid)]) - mean(conservative[(m,'cot',pid)])
          for pid in sorted({r['problem_id'] for r in rows})]
    lo, hi = bootstrap_ci(ds, a.bootstrap_reps)
    report['model_sensitivity_technical_as_failure'][m] = {
        'tdd_minus_cot_pp': mean(ds)*100, 'cluster_bootstrap_95ci_pp': [lo*100,hi*100],
        'signflip_p': signflip_p(ds,a.permutation_reps)}
report['overall']['model_contribution_counts'] = dict(Counter(len(v) for v in overall_problem.values()))
report['reliability'] = {m: {c: dict(Counter(r['error_type'] for r in rows
    if r['model']==m and r['condition']==c and r['status']=='technical_error'))
    for c in ('cot','tdd')} for m in models}
report['settings'] = {'seed': 20261114, 'bootstrap_reps': a.bootstrap_reps,
                      'permutation_reps': a.permutation_reps}
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

# Standalone vector figure requires no plotting dependency.
entries = [('Overall', report['overall'])] + [(m,report['models'][m]) for m in models]
svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="800" height="300" viewBox="0 0 800 300">',
       '<rect width="800" height="300" fill="white"/>',
       '<text x="20" y="25" font-size="18">TDD minus CoT: percentage points, 95% bootstrap intervals</text>']
limits = [v for _,x in entries for v in x['cluster_bootstrap_95ci_pp']] + [0]
low, high = min(limits)-1, max(limits)+1
scale = lambda x: 180 + (x-low)/(high-low)*560
svg.append(f'<path d="M {scale(0)} 45 V 230" stroke="gray" stroke-dasharray="4"/>')
for i,(label,x) in enumerate(entries):
    y=65+i*45; lo,hi=x['cluster_bootstrap_95ci_pp']; effect=x['tdd_minus_cot_pp']
    svg.extend([f'<text x="20" y="{y+5}">{label}</text>',
        f'<path d="M {scale(lo)} {y} H {scale(hi)}" stroke="#2463ad" stroke-width="3"/>',
        f'<circle cx="{scale(effect)}" cy="{y}" r="5" fill="#2463ad"/>'])
svg.append(f'<text x="180" y="265">{low:.1f}</text><text x="710" y="265">{high:.1f}</text></svg>')
(out/'effects.svg').write_text(''.join(svg))
lines = ['# TDD versus CoT statistical report', '',
    'Primary policy: exclude technical failures, as prespecified according to investigator confirmation. Pilot and calibration data are excluded.', '',
    'Effects average within-problem TDD minus CoT correctness. Attempts remain clustered by problem; overall effects average available paired models within each problem. Aggregate pass rates use evaluated attempts and can differ from paired effects.', '',
    '| Comparison | Paired problems | Effect (pp) | 95% bootstrap CI | Raw p | Holm p |',
    '|---|---:|---:|---|---:|---:|']
for label,x in entries:
    lo,hi=x['cluster_bootstrap_95ci_pp']
    lines.append(f"| {label} | {x['paired_problem_count']} | {x['tdd_minus_cot_pp']:.2f} | [{lo:.2f}, {hi:.2f}] | {x['signflip_p']:.4f} | {x.get('holm_adjusted_p', '—')} |")
lines += ['', '## Sensitivity and reliability', '',
    'Counting technical failures as unsuccessful attempts gives an overall effect of '
    f"{report['sensitivity_technical_as_failure']['tdd_minus_cot_pp']:.2f} pp. Model-specific estimates and uncertainty are in analysis.json.", '',
    'Excluding truncations estimates correctness conditional on a usable response. Differential failures can affect comparisons.', '',
    '```json', json.dumps(report['reliability'],indent=2), '```', '',
    '## Resources and interpretation', '',
    'Token totals, estimated USD costs, and mean latency by condition are in analysis.json. Costs are estimates, not invoices.', '',
    'The overall result does not establish improved correctness or equivalence. Conclusions apply to this fixed benchmark subset and these three models. Bootstrap intervals and sign-flip tests use different constructions and need not agree at a threshold.', '',
    'Overall model contribution counts: '+str(report['overall']['model_contribution_counts']), '',
    '![Paired effects](effects.svg)']
(out/'report.md').write_text('\n'.join(lines)+'\n')
