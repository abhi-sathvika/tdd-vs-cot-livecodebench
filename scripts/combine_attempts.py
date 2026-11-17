"""Combine compatible attempt CSV files without changing their rows."""
import argparse
import csv
import pathlib

p = argparse.ArgumentParser()
p.add_argument("inputs", nargs="+")
p.add_argument("--output", required=True)
a = p.parse_args()
rows, fields = [], None
for name in a.inputs:
    with open(name, newline="") as f:
        reader = csv.DictReader(f)
        if fields is None: fields = reader.fieldnames
        elif reader.fieldnames != fields: raise SystemExit(f"Header mismatch: {name}")
        rows.extend(reader)
out = pathlib.Path(a.output); out.parent.mkdir(parents=True, exist_ok=True)
with out.open("w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fields); writer.writeheader(); writer.writerows(rows)
print(f"Wrote {len(rows)} rows to {out}")
