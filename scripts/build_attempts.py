"""Convert prediction and evaluator JSON into attempt-level analysis rows."""
import argparse
import csv
import json
import pathlib
import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
p = argparse.ArgumentParser()
p.add_argument("--provider", required=True)
p.add_argument("--condition", choices=("cot", "tdd"), required=True)
p.add_argument("--predictions", required=True)
p.add_argument("--evaluations", required=True)
p.add_argument("--output", required=True)
a = p.parse_args()
provider = yaml.safe_load((ROOT / "config/providers.yaml").read_text())["providers"][a.provider]
pred = {str(x["question_id"]): x for x in json.loads(pathlib.Path(a.predictions).read_text())}
evaluated = json.loads(pathlib.Path(a.evaluations).read_text())

def error_type(meta):
    code = meta.get("error_code") if isinstance(meta, dict) else None
    message = str(meta.get("error_message", "")).lower() if isinstance(meta, dict) else ""
    if code == -2: return "wrong_answer"
    if code == -3: return "timeout"
    if "syntax" in message or "compile" in message: return "syntax_or_compilation_error"
    if code == -4: return "runtime_error"
    return "evaluation_failure"

def cost(meta):
    inp, out = meta.get("input_tokens"), meta.get("output_tokens")
    if inp is None or out is None: return ""
    if a.provider == "deepseek":
        ir, orate = provider["input_usd_per_million_peak"], provider["output_usd_per_million_peak"]
    elif a.provider == "anthropic":
        ir, orate = provider["input_usd_per_million_from"], provider["output_usd_per_million_from"]
    else:
        ir, orate = provider["input_usd_per_million"], provider["output_usd_per_million"]
    return (inp * ir + out * orate) / 1_000_000

fields = ["problem_id","model","condition","attempt","status","passed","error_type",
          "input_tokens","output_tokens","cost_usd","latency_seconds","finish_reason"]
rows = []
for item in evaluated:
    qid = str(item["question_id"])
    source = pred[qid]
    codes = source.get("code_list", [])
    raw = source.get("raw_response", [])
    metas = item.get("metadata", [{}] * len(item["graded_list"]))
    for i, passed in enumerate(item["graded_list"]):
        emeta = json.loads(metas[i]) if isinstance(metas[i], str) else metas[i]
        rmeta = raw[i].get("response_metadata", {}) if i < len(raw) and isinstance(raw[i], dict) else {}
        malformed = i >= len(codes) or not codes[i] or codes[i] == "Error"
        provider_error = bool(source.get("api_error"))
        finish_reason = rmeta.get("finish_reason", "")
        truncated = finish_reason == "length"
        technical = malformed or truncated or source.get("generation_status") == "technical_error"
        malformed_type = "truncated_response" if truncated else "empty_or_malformed_response"
        rows.append({"problem_id": qid, "model": a.provider, "condition": a.condition,
            "attempt": i + 1, "status": "technical_error" if technical else "evaluated",
            "passed": "" if technical else int(bool(passed)),
            "error_type": "api_error" if provider_error else (malformed_type if malformed else ("api_error" if technical else ("" if passed else error_type(emeta)))),
            "input_tokens": rmeta.get("input_tokens", ""), "output_tokens": rmeta.get("output_tokens", ""),
            "cost_usd": cost(rmeta), "latency_seconds": rmeta.get("latency_seconds", ""),
            "finish_reason": rmeta.get("finish_reason", "")})
out = pathlib.Path(a.output)
out.parent.mkdir(parents=True, exist_ok=True)
with out.open("w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader(); writer.writerows(rows)
print(f"Wrote {len(rows)} attempt rows to {out}")
