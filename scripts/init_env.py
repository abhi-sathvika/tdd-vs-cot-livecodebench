"""Initialize the ignored .env without ever printing secret values."""
import pathlib
import secrets

root = pathlib.Path(__file__).resolve().parents[1]
path = root / ".env"
names = ["OPENAI_API_KEY", "DEEPSEEK_API_KEY", "ANTHROPIC_API_KEY", "LITELLM_MASTER_KEY"]
values = {name: "" for name in names}
if path.exists():
    for line in path.read_text().splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            key, value = line.split("=", 1)
            if key in values: values[key] = value
if not values["LITELLM_MASTER_KEY"]:
    values["LITELLM_MASTER_KEY"] = "sk-local-" + secrets.token_urlsafe(32)
path.write_text("".join(f"{name}={values[name]}\n" for name in names))
path.chmod(0o600)
print("Initialized .env; local proxy master key is present and was not displayed.")
