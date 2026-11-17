# Frozen confirmatory experiment protocol

Research question: Does test-first (`tdd`) prompting improve functional correctness over
code-first (`cot`) prompting on the same fixed LiveCodeBench problems?

- Models: `gpt-6-luna`, `deepseek-flash`, and `claude-haiku-5-5`.
- Benchmark: `livecodebench/code_generation_lite`, `release_v6`, using the tracked recovered
  100-ID checkpoint manifest.
- Calibration: 20 problems x 3 models x 2 conditions x 1 attempt; excluded from confirmation.
- Main: 100 problems x 3 models x 2 conditions x 3 fresh attempts = 1,800 generations.
- Same task IDs, evaluator, prompt definitions, and within-provider settings for both conditions.
- Primary outcome: full-test-suite correctness among evaluated generations.
- Primary contrast: TDD minus CoT, paired and resampled at the problem level.
- Technical failures are retained and reported separately; sensitivity analysis counts them as
  incorrect. Incorrect generated code is never retried.
- Model-specific tests are secondary and use Holm correction.
- No best-of-three or majority voting.
- This compares test-first with code-first prompting; it is not an executable repair-loop TDD agent.
