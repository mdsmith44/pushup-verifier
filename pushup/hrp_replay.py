"""Replay reviewed HRP observations; incompatible with legacy angle CSVs."""

import argparse
import csv
import json
from pathlib import Path
from .hrp import HRPVerifier


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", type=Path)
    parser.add_argument("--mode", choices=["immediate", "temporal"], default="temporal")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    verifier = HRPVerifier(mode=args.mode)
    with args.csv.open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        if not {"timestamp", "pose", "technique", "confidence"}.issubset(reader.fieldnames or []):
            parser.error("Requires HRP timestamp,pose,technique,confidence columns; legacy angle CSVs cannot verify HRP")
        count = 0
        for row in reader:
            verifier.update(float(row["timestamp"]), row["pose"], row["technique"], float(row["confidence"]))
            count += 1
    if not count:
        parser.error("No observations")
    payload = json.dumps({"input": str(args.csv), **verifier.finish()}, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + "\n", encoding="utf-8")
    print(payload)


if __name__ == "__main__":
    main()
