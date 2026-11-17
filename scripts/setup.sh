#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ ! -d upstream/.git ]]; then
  git clone https://github.com/Natt1e/TDD-Agent.git upstream
fi
(cd upstream && git checkout bb08c6b05426c63e75633e4eda9f873ae44fb652)
if (cd upstream && git apply --check ../patches/tdd_agent_livecodebench.patch); then
  (cd upstream && git apply ../patches/tdd_agent_livecodebench.patch)
fi
(cd upstream && git rev-parse HEAD) | tee upstream_commit.txt
if [[ ! -d official_livecodebench/.git ]]; then
  git clone https://github.com/LiveCodeBench/LiveCodeBench.git official_livecodebench
fi
(cd official_livecodebench && git checkout 28fef95ea8c9f7a547c8329f2cd3d32b92c1fa24)
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e ./upstream
.venv/bin/python -m pip install -r requirements-capstone.txt
mkdir -p runs
printf '\nInstalled. Next: source .venv/bin/activate\n'
