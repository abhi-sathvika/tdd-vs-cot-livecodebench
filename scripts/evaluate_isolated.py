"""Run the LiveCodeBench evaluator in a locked-down Docker container."""
import argparse
import os
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[1]
p = argparse.ArgumentParser()
p.add_argument("prediction")
p.add_argument("--benchmark-bundle", default="data_private/livecodebench_release_v6_100.json")
p.add_argument("--image", default="tdd-lcb-evaluator:local")
p.add_argument("--execute", action="store_true")
a, extra = p.parse_known_args()
prediction = pathlib.Path(a.prediction).resolve()
if not prediction.exists(): raise SystemExit(f"Missing prediction file: {prediction}")
bundle = pathlib.Path(a.benchmark_bundle)
if not bundle.is_absolute(): bundle = (ROOT / bundle).resolve()
if not bundle.exists(): raise SystemExit(f"Missing frozen benchmark bundle: {bundle}")
cmd = ["docker", "run", "--rm", "--network", "none", "--read-only",
       "--user", f"{os.getuid()}:{os.getgid()}",
       "-e", "HF_DATASETS_OFFLINE=1", "-e", "HF_HUB_OFFLINE=1",
       "--cpus", "2", "--memory", "10g", "--pids-limit", "256",
       "--security-opt", "no-new-privileges", "--cap-drop", "ALL",
       "--tmpfs", "/tmp:rw,noexec,nosuid,size=1g",
       "-v", f"{prediction.parent}:/run:rw",
       "-v", f"{bundle}:/benchmark/frozen.json:ro"]
cmd += [a.image, "--benchmark_bundle", "/benchmark/frozen.json",
        "--custom_output_file", f"/run/{prediction.name}", *extra]
print(" ".join(cmd))
if not a.execute:
    print("Dry run only; no generated code was executed.")
else:
    subprocess.run(cmd, check=True)
