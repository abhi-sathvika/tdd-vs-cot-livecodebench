"""Report whether required secrets exist without printing their values."""
import os
for name in ("OPENAI_API_KEY", "DEEPSEEK_API_KEY", "ANTHROPIC_API_KEY"):
    print(f"{name}: {'present' if os.getenv(name) else 'missing'}")
