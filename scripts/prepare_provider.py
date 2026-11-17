"""Prepare a secret-free local model config for the pinned TDD-Agent client."""
import argparse
import pathlib
import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
providers = yaml.safe_load((ROOT / "config/providers.yaml").read_text())["providers"]
parser = argparse.ArgumentParser()
parser.add_argument("--provider", required=True, choices=providers)
args = parser.parse_args()
item = providers[args.provider]
kwargs = {item["token_parameter"]: int(item["max_output_tokens"])}
if item.get("temperature_supported") and item.get("temperature") is not None:
    kwargs["temperature"] = item["temperature"]
if item.get("reasoning_effort") is not None:
    kwargs["reasoning_effort"] = item["reasoning_effort"]
base_url = item["base_url"]
api_key_env = item["api_key_env"]
if args.provider == "anthropic":
    base_url = "http://127.0.0.1:4000/v1"
    api_key_env = "LITELLM_MASTER_KEY"
payload = {"model": {"provider": args.provider, "model_name": item["model"],
    "base_url": base_url, "api_key_env": api_key_env, "model_kwargs": kwargs}}
out = ROOT / "config/local_model.yaml"
out.write_text(yaml.safe_dump(payload, sort_keys=False))
out.chmod(0o600)
print(f"Prepared secret-free local config for {args.provider}: {out}")
