# Reproducibility manifest

Checked: 2026-11-14 (America/Los_Angeles)

- Repository baseline commit: `ac408e` (record the final commit in each run manifest)
- TDD-Agent commit: `bb08c6b05426c63e75633e4eda9f873ae44fb652`
- LiveCodeBench commit: `28fef95ea8c9f7a547c8329f2cd3d32b92c1fa24`
- Dataset: `livecodebench/code_generation_lite`, `release_v6`
- Date/platform filter: 2024-05-01 through 2025-05-01, LeetCode
- Tracked problem-ID manifest: `data/problem_manifest_checkpoint.csv`
- Problem-ID CSV file SHA-256: `51bbf1950d7ec0eb349ec2e9dcb9509a56e7e26e25daf30f8bb2ab063f737294`
- Canonical sorted-ID-list SHA-256: `3bbb1041f53b20f48e74a4c91881cf8d014b787708716a368bab587352b76679`
- Ignored evaluator bundle SHA-256: `06a57c02146164a89d76db21401dd809245c22602cb6d7c406708b8c619c9463`
- Models: `gpt-6-luna`, `deepseek-flash`, `claude-haiku-5-5`
- DeepSeek calibration revision: increase `max_output_tokens` from 4096 to 8192 after 8/40 calibration outputs were truncated at the 4096-token ceiling; rerun validation before main.
- Prompt/config hash, exact generation settings, run date, provider, and model are written to each run's `manifest.json`.
- Evaluation isolation: Docker network disabled, read-only container root, all capabilities dropped, no-new-privileges, CPU/memory/PID limits.

The ignored evaluator bundle contains private benchmark tests. Reproduce it locally from the pinned
release using `scripts/freeze_evaluator_bundle.py`; never commit or distribute it.
