"""Plan or execute isolated provider runs through the existing experiment runner."""
import argparse
import datetime
import json
import pathlib
import subprocess
import sys
import yaml
from dotenv import load_dotenv

ROOT = pathlib.Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env", override=True)
PROVIDERS = yaml.safe_load((ROOT / "config/providers.yaml").read_text())["providers"]
p = argparse.ArgumentParser()
p.add_argument("--phase", choices=("smoke", "calibration", "main"), required=True)
p.add_argument("--providers", nargs="+", choices=PROVIDERS, default=list(PROVIDERS))
p.add_argument("--execute", action="store_true")
p.add_argument("--resume", action="store_true")
p.add_argument("--run-id", help="Stable run ID; required when resuming")
a = p.parse_args()
defaults = {"smoke": (0, 1, 1), "calibration": (0, 20, 1), "main": (0, 100, 3)}
manifests = {
    "smoke": ROOT / "data/problem_manifest_smoke.csv",
    "calibration": ROOT / "data/problem_manifest_calibration.csv",
    "main": ROOT / "data/problem_manifest_checkpoint.csv",
}
start, end, samples = defaults[a.phase]
if a.resume and not a.run_id:
    raise SystemExit("--resume requires the original --run-id")
stamp = a.run_id or datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
plan = []
for provider in a.providers:
    run_dir = ROOT / "runs/final_experiment" / provider / a.phase / stamp
    cmd = [sys.executable, str(ROOT / "scripts/run_prompt_replication.py"),
           "--start", str(start), "--end", str(end), "--samples", str(samples),
           "--modes", "cot", "tdd", "--output-dir", str(run_dir)]
    cmd += ["--question-ids-file", str(manifests[a.phase])]
    if a.resume:
        cmd.append("--resume")
    if a.execute:
        cmd.append("--execute")
    item = {"provider": provider, "model": PROVIDERS[provider]["model"],
            "phase": a.phase, "run_dir": str(run_dir), "command": cmd}
    plan.append(item)
    print(json.dumps(item, indent=2))
    if a.execute:
        subprocess.run([sys.executable, str(ROOT / "scripts/prepare_provider.py"),
                        "--provider", provider], cwd=ROOT, check=True)
        subprocess.run(cmd, cwd=ROOT, check=True)
if not a.execute:
    print("Dry run only: no run directories created and no provider called.")
