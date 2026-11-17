#!/usr/bin/env python3
"""Create an untracked, minimal LiveCodeBench bundle for the frozen IDs.

Reads Arrow record batches with memory mapping so the 4.2 GB release is never
materialized as Python objects.  The output contains private tests and must not
be committed; only its checksum belongs in reproducibility metadata.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path

import pyarrow as pa
import pyarrow.compute as pc


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--manifest", default="data/problem_manifest_checkpoint.csv")
    p.add_argument("--arrow-dir", required=True)
    p.add_argument("--output", default="data_private/livecodebench_release_v6_100.json")
    a = p.parse_args()
    with open(a.manifest, newline="") as f:
        wanted = {str(r["question_id"]) for r in csv.DictReader(f)}
    if not wanted:
        raise SystemExit("Problem manifest is empty")

    found = {}
    for path in sorted(Path(a.arrow_dir).glob("*.arrow")):
        with pa.memory_map(str(path), "r") as source:
            reader = pa.ipc.open_stream(source)
            for batch in reader:
                mask = pc.is_in(batch.column("question_id"), value_set=pa.array(sorted(wanted)))
                for row in batch.filter(mask).to_pylist():
                    qid = str(row["question_id"])
                    if qid in found:
                        raise SystemExit(f"Duplicate question_id in dataset: {qid}")
                    found[qid] = row
    missing = wanted - found.keys()
    extra = found.keys() - wanted
    if missing or extra:
        raise SystemExit(f"Bundle mismatch: missing={sorted(missing)}, extra={sorted(extra)}")

    out = Path(a.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps([found[qid] for qid in sorted(found)], separators=(",", ":")))
    digest = hashlib.sha256(out.read_bytes()).hexdigest()
    print(f"Wrote {len(found)} frozen problems to {out}")
    print(f"SHA256 {digest}")


if __name__ == "__main__":
    main()
