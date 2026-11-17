"""Recover and verify a shared question-ID manifest from existing outputs."""
import argparse
import csv
import json
import pathlib

p = argparse.ArgumentParser()
p.add_argument("outputs", nargs="+")
p.add_argument("--output", required=True)
a = p.parse_args()
sets = []
for name in a.outputs:
    rows = json.loads(pathlib.Path(name).read_text())
    ids = [str(row["question_id"]) for row in rows]
    if len(ids) != len(set(ids)):
        raise SystemExit(f"Duplicate question IDs in {name}")
    sets.append(set(ids))
if any(value != sets[0] for value in sets[1:]):
    raise SystemExit("Input output files do not contain identical question IDs")
out = pathlib.Path(a.output)
out.parent.mkdir(parents=True, exist_ok=True)
with out.open("w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["question_id"])
    writer.writerows([value] for value in sorted(sets[0]))
print(f"Wrote {len(sets[0])} verified IDs to {out}")
