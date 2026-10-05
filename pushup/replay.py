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
    parser.add_argument("--separate-alignment", action="store_true", help="Experimental: track with arm confidence; report missing alignment separately. Requires --include-confidence extraction.")
    parser.add_argument("--partial-start", action="store_true", help="Experimental: report an initial descent/return without a verified starting top as unassessable")
    args = parser.parse_args()
    verifier = Verifier(Config(**json.loads(args.config.read_text(encoding="utf-8"))), args.mode, separate_alignment=args.separate_alignment, partial_start=args.partial_start)
    with args.csv.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        required = {"timestamp", "elbow_angle", "body_angle", "confidence"}
        if args.separate_alignment:
            required |= {f'{joint}_{kind}' for joint in ('shoulder','elbow','wrist','hip','ankle') for kind in ('visibility','presence')}
            required.add('observation_status')
        if not required.issubset(reader.fieldnames or []):
            parser.error(f"CSV requires {sorted(required)}")
        rows = 0
        for row in reader:
            confidence = float(row['confidence'])
            body = float(row['body_angle']) if row['body_angle'].strip() else None
            if args.separate_alignment:
                if row['observation_status'] == 'measured':
                    components = {joint: [float(row[f'{joint}_{kind}']) for kind in ('visibility','presence')] for joint in ('shoulder','elbow','wrist','hip','ankle')}
                    if any(not 0 <= score <= 1 for values in components.values() for score in values):
                        parser.error('Joint confidence must be finite and within [0, 1]')
                    scores = {joint: min(values) for joint, values in components.items()}
                    confidence = min(scores[j] for j in ('shoulder','elbow','wrist'))
                    if min(scores[j] for j in ('shoulder','hip','ankle')) < verifier.config.min_confidence:
                        body = None
                else:
                    confidence, body = 0, None
            verifier.update(float(row["timestamp"]),
                            float(row["elbow_angle"]) if row["elbow_angle"].strip() else None,
                            body, confidence)
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
