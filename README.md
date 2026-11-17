# TDD-Agent LiveCodeBench Replication

This repository contains code for a partial replication of the TDD prompting experiment from **TDD-Agent (EMNLP 2026)**.

The experiment compares two prompting strategies on the same LiveCodeBench programming problems:

- **CoT (`cot`)** — chain-of-thought baseline
- **TDD (`tdd`)** — test-driven-development prompting condition

The goal is to determine whether TDD-style prompting improves functional correctness on coding problems compared with the CoT baseline.

The original TDD-Agent implementation is used for prediction rather than reimplemented in this repository.

> Confirmatory experiment note (2026-11-14): the original 100-task checkpoint is pilot evidence
> only. New calibration and main runs live under `runs/final_experiment/` and must never be pooled
> with the checkpoint.

## Confirmatory design

- Models: `gpt-6-luna`, `deepseek-flash`, and `claude-haiku-5-5`.
- Conditions: upstream `cot` and `tdd` prompt modes.
- Calibration: 20 fixed tasks x 3 models x 2 conditions x 1 attempt.
- Main: 100 frozen tasks x 3 models x 2 conditions x 3 attempts.
- Problem IDs: `data/problem_manifest_checkpoint.csv`, recovered identically from both pilot files.
- Smoke and calibration use tracked one- and twenty-ID subsets of that same frozen manifest.
- Dataset: `livecodebench/code_generation_lite`, `release_v6`.
- Evaluator commit: `28fef95ea8c9f7a547c8329f2cd3d32b92c1fa24`.
- TDD-Agent commit: `bb08c6b05426c63e75633e4eda9f873ae44fb652` plus the tracked patch.

This is a test-first versus code-first prompting comparison, not an executable test-and-repair
TDD loop.

## Secure provider setup

Copy `.env.example` to the ignored `.env` and enter keys locally. Never place credentials in YAML,
source files, logs, screenshots, or chat. `scripts/init_env.py` creates a local-only LiteLLM master
key without displaying it. `scripts/prepare_provider.py` writes only the environment-variable name
to the ignored upstream config; it never copies a provider credential.

Model details, limits, pricing, and official documentation links are recorded in
`docs/model_verification.md`.

## Commands

```bash
source .venv/bin/activate
bash scripts/test.sh

# Plans only: no directories and no API requests
python scripts/run_model_matrix.py --phase smoke
python scripts/run_model_matrix.py --phase calibration
python scripts/run_model_matrix.py --phase main

# Paid execution requires an explicit --execute
python scripts/run_model_matrix.py --phase smoke --providers openai --execute
```

Anthropic uses the isolated `.proxy-venv` LiteLLM process configured by
`config/litellm_config.yaml`. The local proxy master key authenticates only local callers; the
Anthropic provider key remains in the environment.

Start the local-only adapter in a separate terminal before an Anthropic run:

```bash
set -a
source .env
set +a
.proxy-venv/bin/litellm --config config/litellm_config.yaml --host 127.0.0.1 --port 4000
```

The proxy health endpoint can be checked without making a provider request at
`http://127.0.0.1:4000/health/liveliness`.

Generated code is evaluated with the network-disabled Docker runner:

```bash
bash scripts/build_evaluator_image.sh
# One-time: create the ignored 100-task bundle from the pinned release's Arrow cache.
python scripts/freeze_evaluator_bundle.py \
  --arrow-dir "$HOME/.cache/huggingface/datasets/livecodebench___code_generation_lite/release_latest-version_tag=release_v6/0.0.0/4c038560f391c4c05fdf7fd7ae61ae0e6dbd8672f8fe5b95597b78a8dc40a417"
python scripts/evaluate_isolated.py runs/RUN/cot.json --execute --release_version release_v6
```

The container has no network, a read-only root filesystem, dropped Linux capabilities, resource
limits, and runs as the invoking WSL user. It mounts the ignored frozen benchmark bundle read-only;
only the selected run directory is writable. The bundle includes private tests and must never be
committed. Its expected SHA-256 is
`06a57c02146164a89d76db21401dd809245c22602cb6d7c406708b8c619c9463`.
Evaluator JSON can be converted with `scripts/build_attempts.py`, combined with
`scripts/combine_attempts.py`, and analyzed with `scripts/analyze_results.py`.

## Original Study

Paper:

https://aclanthology.org/2026.emnlp-main.1845/

Authors' code:

https://github.com/Natt1e/TDD-Agent

LiveCodeBench:

https://github.com/LiveCodeBench/LiveCodeBench

---

## Experiment Design

Both conditions are evaluated on the exact same LiveCodeBench problems.

For every task:

1. The task is provided to the CoT prompting condition.
2. The task is independently provided to the TDD prompting condition.
3. Each condition produces one generated solution.
4. The generated solutions are evaluated using LiveCodeBench's execution-based evaluation.
5. Functional correctness is measured using **pass@1**.

Each condition is launched in a separate Python process and writes to a separate output file. No conversation IDs or model responses are shared between the two conditions.

### Primary independent variable

Prompting strategy:

- `cot`
- `tdd`

### Primary dependent variable

LiveCodeBench **pass@1**.

### Controlled variables

The two conditions use the same:

- model
- task set
- API provider
- number of samples per task
- generation limits
- benchmark evaluator

---

## Repository Structure

```text
tdd_agent_replication_kit/
│
├── README.md
├── .gitignore
│
├── scripts/
│   ├── setup.sh
│   ├── prepare.py
│   ├── run_prompt_replication.py
│   ├── summarize_outputs.py
│   └── eval_subset.py
│
├── config/
│   └── local_model.yaml        # generated locally; NOT committed
│
├── upstream/                   # cloned TDD-Agent repo; NOT committed
├── official_livecodebench/     # cloned LiveCodeBench repo; NOT committed
└── runs/                       # experiment outputs; NOT committed
```

### Scripts

`setup.sh`  
Creates the Python environment and installs the upstream TDD-Agent implementation.

`prepare.py`  
Creates the local API configuration using the `OPENAI_API_KEY` environment variable.

`run_prompt_replication.py`  
Runs the official TDD-Agent LiveCodeBench prediction script independently for the CoT and TDD conditions.

`summarize_outputs.py`  
Checks generated output files for missing or invalid model responses. This does not evaluate correctness.

`eval_subset.py`  
Evaluates only the LiveCodeBench question IDs contained in a generated output file while using the official LiveCodeBench grading functions.

---

# Environment

The experiment was run using:

- Windows with WSL2
- Ubuntu 22.04
- Python 3.12
- Git
- OpenAI-compatible API
- Hugging Face `datasets`
- LiveCodeBench
- TDD-Agent

The experiment does not require a local GPU because model inference is performed through an API.

---

# Setup

## 1. Clone this repository

```bash
git clone https://github.com/abhi-sathvika/tdd-vs-cot-livecodebench.git
cd tdd-vs-cot-livecodebench
```

## 2. Install Python 3.12

On Ubuntu 22.04:

```bash
sudo apt update
sudo apt install -y software-properties-common

sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update

sudo apt install -y \
    python3.12 \
    python3.12-venv \
    python3.12-dev
```

Verify:

```bash
python3.12 --version
```

## 3. Create the virtual environment

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

Upgrade pip:

```bash
python -m pip install --upgrade pip setuptools
```

## 4. Clone the original TDD-Agent implementation

```bash
git clone https://github.com/Natt1e/TDD-Agent.git upstream
```

Record the exact version:

```bash
cd upstream
git rev-parse HEAD
cd ..
```

Install it:

```bash
python -m pip install -e ./upstream
```

Install additional dependencies:

```bash
python -m pip install PyYAML pandas
```

The version of Hugging Face `datasets` used for this replication must support the custom LiveCodeBench dataset loader:

```bash
python -m pip install "datasets==3.6.0"
```

## 5. Allow the LiveCodeBench dataset loader

The TDD-Agent version used in this replication requires the Hugging Face LiveCodeBench custom dataset loader.

In:

```text
upstream/LiveCodeBench/predict.py
```

change:

```python
tasks = load_dataset(dataset_name, version_tag=release)
```

to:

```python
tasks = load_dataset(
    dataset_name,
    version_tag=release,
    trust_remote_code=True,
)
```

This is a compatibility change required by the installed Hugging Face `datasets` version.

---

# API Configuration

## OpenAI API key

Do not store an API key in the repository.

In WSL:

```bash
read -s -p "Enter OpenAI API key: " OPENAI_API_KEY
echo
export OPENAI_API_KEY
```

Verify that it is available:

```bash
python -c "import os; print(bool(os.getenv('OPENAI_API_KEY')))"
```

The output should be:

```text
True
```

Generate the local model configuration:

```bash
python scripts/prepare.py --model <MODEL_ID>
```

Replace `<MODEL_ID>` with the model used for the experiment.

The generated file is:

```text
config/local_model.yaml
```

This file contains an API credential and is intentionally excluded from Git.

### Token-limit compatibility

The model used in this replication requires:

```yaml
max_completion_tokens: 4096
```

rather than:

```yaml
max_tokens: 4096
```

The committed `prepare.py` should therefore generate the parameter supported by the selected model.

---

# Hugging Face

LiveCodeBench is downloaded through the Hugging Face Hub.

A Hugging Face token is optional for public datasets but can increase rate limits.

If desired:

```bash
read -s -p "Enter Hugging Face token: " HF_TOKEN
echo
export HF_TOKEN
```

No benchmark data needs to be manually downloaded or committed to this repository.

---

# Running the Experiment

## Dry run

A dry run creates the experiment manifest without making paid API calls:

```bash
python scripts/run_prompt_replication.py \
    --start 0 \
    --end 10
```

## 10-task pilot

```bash
python scripts/run_prompt_replication.py \
    --start 0 \
    --end 10 \
    --samples 1 \
    --execute
```

## 100-task experiment

The checkpoint experiment used 100 paired tasks:

```bash
python scripts/run_prompt_replication.py \
    --start 0 \
    --end 100 \
    --samples 1 \
    --execute
```

The runner creates a timestamped directory:

```text
runs/<TIMESTAMP>_0_100/
```

containing:

```text
manifest.json
cot.json
cot.log
tdd.json
tdd.log
```

The `manifest.json` records the upstream commit, task range, modes, sample count, and exact commands used for the experiment.

---

# Validate Generated Outputs

Before correctness evaluation, check that the API produced valid outputs:

```bash
python scripts/summarize_outputs.py \
    runs/<RUN_ID>/cot.json \
    runs/<RUN_ID>/tdd.json
```

For the 100-task checkpoint experiment, output validation found:

```text
CoT: 100 tasks, 5 empty/error generations
TDD: 100 tasks, 7 empty/error generations
```

Generation errors are retained rather than silently removed.

---

# Install the LiveCodeBench Evaluator

Clone the official LiveCodeBench repository:

```bash
git clone \
    https://github.com/LiveCodeBench/LiveCodeBench.git \
    official_livecodebench
```

Install it:

```bash
python -m pip install -e ./official_livecodebench
```

The evaluator version used during setup required a legacy Anthropic SDK dependency:

```bash
python -m pip install "anthropic<1"
```

This dependency is needed by imports in the LiveCodeBench codebase even though the experiment itself does not use an Anthropic model.

---

# Evaluate Correctness

The official LiveCodeBench custom evaluator expects predictions for its entire benchmark. Since this experiment evaluates a subset of tasks, `scripts/eval_subset.py` filters the benchmark to exactly the question IDs contained in the prediction file and then calls the official LiveCodeBench grading functions.

Run from the LiveCodeBench repository directory so its relative resource paths resolve correctly:

```bash
cd official_livecodebench
```

Evaluate CoT:

```bash
python ../scripts/eval_subset.py \
    --custom_output_file \
    ../runs/<RUN_ID>/cot.json
```

Evaluate TDD:

```bash
python ../scripts/eval_subset.py \
    --custom_output_file \
    ../runs/<RUN_ID>/tdd.json
```

The evaluator produces files such as:

```text
cot_subset_eval.json
tdd_subset_eval.json
```

---

# Current Checkpoint Results

For the first 100 matched LiveCodeBench tasks with one sample per task:

| Condition | Tasks Passed | pass@1 |
| --------- | -----------: | -----: |
| CoT       |     87 / 100 |   0.87 |
| TDD       |     88 / 100 |   0.88 |

The two conditions therefore differed by **1 percentage point** in aggregate pass@1.

Task-level comparison:

- 84 tasks were passed by both methods.
- 9 tasks were failed by both methods.
- 4 tasks were passed only by TDD.
- 3 tasks were passed only by CoT.

These checkpoint results should be interpreted as a partial replication rather than a full reproduction of all experiments in the original paper.

---

# Reproducibility Notes

- CoT and TDD are run in independent Python processes.
- Both conditions receive the same task range.
- No conversation ID is shared between conditions.
- API credentials are excluded from version control.
- The exact upstream TDD-Agent Git commit is stored in each run manifest.
- Model failures and invalid generations are retained rather than silently discarded.
- The official LiveCodeBench grading functions are used for correctness evaluation.
- This repository reproduces the LiveCodeBench prompting comparison, not every experiment from the TDD-Agent paper.

---

### AI Contributions
We used ChatGPT to assist with planning the experimental setup, developing and debugging parts of the replication workflow, troubleshooting environment and dependency issues, and understanding the LiveCodeBench evaluation process. AI assistance was also used to help interpret experimental results and identify possible directions for further investigation.

### Human Contributions
Our team selected the research paper, defined the scope of the replication, configured the experimental environment, executed the experiments, and evaluated the generated solutions. We also analyzed the results, compared the prompting strategies, and determined the limitations and next steps of our investigation.

---

# Files That Must Not Be Committed

The following contain generated data, third-party repositories, environments, or secrets:

```text
.venv/
.proxy-venv/
upstream/
official_livecodebench/
runs/
data_private/
results/analysis/
config/local_model.yaml
.env
__pycache__/
```

API keys must never be committed to the repository.
