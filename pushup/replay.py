"""Replay saved pose observations through either decision method."""

import argparse
import csv
import json
from pathlib import Path
from .engine import Config, Verifier


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", type=Path)
    parser.add_argument("--mode", choices=["immediate", "temporal"], default="temporal")
    parser.add_argument("--config", type=Path, default=Path(__file__).resolve().parents[1] / "config/default.json")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    verifier = Verifier(Config(**json.loads(args.config.read_text(encoding="utf-8"))), args.mode)
    with args.csv.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        required = {"timestamp", "elbow_angle", "body_angle", "confidence"}
        if not required.issubset(reader.fieldnames or []):
            parser.error(f"CSV requires {sorted(required)}")
        rows = 0
        for row in reader:
            verifier.update(float(row["timestamp"]),
                            float(row["elbow_angle"]) if row["elbow_angle"].strip() else None,
                            float(row["body_angle"]) if row["body_angle"].strip() else None,
                            float(row["confidence"]))
            rows += 1
    if not rows:
        parser.error("Observation CSV contains no frames")
    report = {"input": str(args.csv), "observation_count": rows, **verifier.finish()}
    payload = json.dumps(report, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + "\n", encoding="utf-8")
    print(payload)


if __name__ == "__main__":
    main()
