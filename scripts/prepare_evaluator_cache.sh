#!/usr/bin/env bash
set -euo pipefail
source_cache="${HOME}/.cache/huggingface"
dataset_cache="${source_cache}/datasets/livecodebench___code_generation_lite"
if [[ ! -d "${source_cache}/modules" || ! -d "${dataset_cache}" ]]; then
  echo "Required cached LiveCodeBench release is missing." >&2
  exit 1
fi
docker volume create tdd-lcb-hf-cache >/dev/null
docker run --rm --entrypoint /bin/sh \
  -v "${source_cache}/modules:/source/modules:ro" \
  -v "${dataset_cache}:/source/dataset:ro" \
  -v "tdd-lcb-hf-cache:/dest:rw" \
  tdd-lcb-evaluator:local -c \
  'mkdir -p /dest/modules /dest/datasets/livecodebench___code_generation_lite && cp -a /source/modules/. /dest/modules/ && cp -a /source/dataset/release_latest-version_tag=release_v6 /dest/datasets/livecodebench___code_generation_lite/ && chmod -R a+rwX /dest'
echo "Prepared isolated evaluator cache volume: tdd-lcb-hf-cache"
