#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ ! -d upstream/.git ]]; then
  git clone https://github.com/Natt1e/TDD-Agent.git upstream
fi
(cd upstream && git rev-parse HEAD) | tee upstream_commit.txt
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e ./upstream
.venv/bin/python -m pip install PyYAML pandas
mkdir -p runs
printf '\nInstalled. Next: source .venv/bin/activate\n'
