import argparse
from pathlib import Path

import boto3
from pushup.process import process


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--bucket", required=True)
    parser.add_argument("--input-key", required=True)
    parser.add_argument("--model-key", required=True)
    parser.add_argument("--work-dir", type=Path, required=True)
    parser.add_argument("--side", choices=("left", "right"), required=True)
    parser.add_argument("--output-prefix", required=True)
    args = parser.parse_args()

    # Use a new directory to avoid overwriting a previous run.
    args.work_dir.mkdir(parents=True, exist_ok=False)

    s3 = boto3.client("s3")

    downloads = [
        (args.model_key, args.work_dir / "model.task"),
        (args.input_key, args.work_dir / "input.mov"),
    ]

    for key, destination in downloads:
        print(f"Downloading {key}...", flush=True)
        s3.download_file(args.bucket, key, str(destination))
        print(
            f"Saved {destination.name}: "
            f"{destination.stat().st_size:,} bytes",
            flush=True,
        )

    print("Processing video...", flush=True)

    report = process(
        source=(args.work_dir / "input.mov").resolve(),
        output=(args.work_dir / "output").resolve(),
        model=(args.work_dir / "model.task").resolve(),
        side=args.side,
    )

    print(f"Processing complete: {report['counts']}", flush=True)

    artifacts = {
        "annotated.mp4": "video/mp4",
        "chart.png": "image/png",
        "report.json": "application/json",
    }

    prefix = args.output_prefix.strip("/")

    for filename, content_type in artifacts.items():
        local_path = args.work_dir / "output" / filename
        key = f"{prefix}/{filename}"

        print(f"Uploading {key}...", flush=True)

        s3.upload_file(
            str(local_path),
            args.bucket,
            key,
            ExtraArgs={"ContentType": content_type},
        )

    print(
        f"Results saved to s3://{args.bucket}/{prefix}/",
        flush=True,
    )


if __name__ == "__main__":
    main()