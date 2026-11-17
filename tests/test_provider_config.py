import pathlib
import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]

def test_provider_config_has_no_secrets():
    text = (ROOT / "config/providers.yaml").read_text()
    assert "sk-" not in text
    cfg = yaml.safe_load(text)["providers"]
    assert set(cfg) == {"openai", "deepseek", "anthropic"}
    assert all(item.get("api_key_env") for item in cfg.values())
    assert all("api_key" not in item for item in cfg.values())

def test_selected_model_ids():
    cfg = yaml.safe_load((ROOT / "config/providers.yaml").read_text())["providers"]
    assert cfg["openai"]["model"] == "gpt-6-luna"
    assert cfg["deepseek"]["model"] == "deepseek-flash"
    assert cfg["anthropic"]["model"] == "claude-haiku-5-5"
