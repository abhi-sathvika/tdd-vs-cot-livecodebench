# TDD-Agent LiveCodeBench Replication

This repository contains code for a partial replication of the TDD prompting experiment from **TDD-Agent (EMNLP 2026)**.

The experiment compares two prompting strategies on the same LiveCodeBench programming problems:

- **CoT (`cot`)** — chain-of-thought baseline
- **TDD (`tdd`)** — test-driven-development prompting condition

The goal is to determine whether TDD-style prompting improves functional correctness on coding problems compared with the CoT baseline.

The original TDD-Agent implementation is used for prediction rather than reimplemented in this repository.

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
