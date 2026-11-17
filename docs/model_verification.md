# Provider model verification

Checked: 2026-11-14 (America/Los_Angeles)

No API request was made during verification. The following are public API model IDs in the
providers' official documentation.

## OpenAI

- Model ID: `gpt-6-luna`
- Interfaces: Responses and Chat Completions; structured outputs supported.
- Standard text pricing: $0.10/M input tokens, $0.01/M cached input tokens, $0.50/M output tokens.
- Context window: 1,050,000 tokens. Maximum output: 128,000 tokens.
- Configuration uses `max_completion_tokens`; temperature is omitted for this reasoning model.
- Sources:
  - https://developers.openai.com/api/docs/models/gpt-6-luna
  - https://developers.openai.com/api/docs/pricing

## DeepSeek

- Model ID: `deepseek-flash` (DeepSeek-V4.1-Flash-1017 at time checked).
- Interface: official OpenAI-compatible Chat Completions endpoint.
- Configuration uses `max_tokens`; temperature and JSON response format are documented.
- Context window: 1M tokens. Maximum output: 384K tokens.
- Flash pricing varies by time: cache-miss input $0.15/M off-peak or $0.30/M peak;
  cached input $0.003/M or $0.006/M; output $0.60/M or $1.20/M.
- Sources:
  - https://api-docs.deepseek.com/quick_start/pricing
  - https://api-docs.deepseek.com/api/create-chat-completion

## Anthropic

- Model ID: `claude-haiku-5-5`.
- Native interface: Messages API using required `max_tokens`; temperature is optional.
- Context window: 1M tokens. Maximum output: 128K tokens.
- Listed pricing starts at $0.10/M input tokens and $0.50/M output tokens.
- The existing TDD-Agent client is OpenAI-specific, so the integration uses LiteLLM's local
  OpenAI-compatible adapter while retaining the Anthropic key only in the environment.
- Sources:
  - https://docs.anthropic.com/en/docs/about-claude/models/overview
  - https://docs.anthropic.com/en/api/messages

Documentation pages are dynamic; preserve this date and re-check immediately before calibration
and the main run. Cost approval will use the conservative applicable rate and observed usage.
