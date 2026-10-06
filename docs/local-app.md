# Local upload application

Implemented milestone: a responsive upload/results page, bounded persistent job queue, separate video-processing subprocess, H.264 annotated playback/download, elbow-angle PNG, and JSON report. This is the local development interface. The public application uses the separate authenticated AWS architecture described in [AWS operations](aws-deployment.md).

## Run in the existing Linux/WSL Python 3.12 environment

```bash
conda activate pushup-verifier
python -m pip install -r requirements/app.lock.txt
python -m uvicorn pushup.web:app --host 127.0.0.1 --port 8000 --workers 1
```

Open http://127.0.0.1:8000 on the same computer. The local URL is not reachable from a phone on another device. The deployed CloudFront website provides public/mobile access; do not expose this unauthenticated preview with a tunnel or bind it publicly. Place the Full model at `models/pose_landmarker_full.task` before uploading. `PUSHUP_MODEL` overrides its location; `PUSHUP_DATA` overrides the private job directory (default `results/web-jobs`). Use only one server instance/worker per job directory. Ctrl+C stops the server and active job process group on Linux; interrupted jobs are marked failed. Queued jobs persist across restarts.

MOV/MP4, up to 200 MiB and 120 seconds, maximum input pixel area 4096×2160. The processor rotates/transcodes phone footage to a maximum dimension of 1280 and 30 fps, strips audio, then runs the existing extractor and verifier. This normalization can alter model outputs; uploaded-video predictions are not guaranteed to be numerically identical to original-resolution CLI runs.

The tested candidate uses the frozen 140-degree configuration, temporal mode, separate alignment, and partial starts. The chart shows raw elbow measurements with 90/140-degree lines; decisions are temporal. The counters distinguish top-anchored completed movements from accepted/rejected form. Unassessable segments and partial returns remain visible. The output report records model/config hashes, library versions, and processing duration.

## Operational boundaries

- One processing job at a time; up to three uploading/queued/processing jobs. Uploads stream directly into generated job directories, never user-supplied paths. Size limit is enforced during streaming, and upload time is bounded.
- A job has a 20-minute outer timeout and individual processing commands have 10-minute limits. Source uploads are deleted after completion/failure. Successful intermediate normalized/render videos are deleted; diagnostic CSVs/logs remain with the job until deletion/expiry.
- Completed/failed job directories are cleaned after 24 hours when the worker next checks retention. Expiry is not exact while the server is stopped or busy. The user can delete completed/failed results immediately.
- Job IDs are random capability-like local URLs, not authenticated ownership. Host/origin checks and no public bind reduce local-preview exposure but are not substitutes for cloud authentication. Never use this server as the public production API.
- Restarted in-progress uploads/jobs become failed; there is no automatic retry. This avoids silently duplicating work. The deployed cloud application uses Step Functions instead of this local queue.

## Container packaging

```bash
docker compose -f docker/compose.yaml up --build
```

The compose service publishes only to local loopback, mounts the local model read-only, uses a named job volume, runs as a non-root user, and limits CPU/memory/process count. The image build context excludes videos, observations, models, credentials, and Git data. Docker Desktop's Linux engine must be running. Direct WSL processing, the learning container, and the deployed cloud worker have been exercised. See [Docker builds](../docker/README.md) for the separate image configurations. The pinned lock is an installed Linux/Python 3.12 snapshot, not a cross-platform lock or a hash-verified supply-chain guarantee.

## Verification performed

- 52 existing verifier tests pass; 7 web-app tests cover queue bounds, invalid input, origin/host checks, artifact allowlisting, deletion, retention and restart recovery.
- Direct end-to-end processing and a real HTTP upload both processed the pilot3B clip. The HTTP job produced five completions, three accepted and two rejected, with no uncertainty. Processing took approximately 58 seconds on this local environment; this is not an AWS latency estimate.
- All three result endpoints returned downloadable artifacts; browser video reached ready state 4 with approximately 18 seconds duration. The results UI and chart rendered; a phone-width check found no horizontal document overflow.
- Browser file-picker automation did not complete, so the upload was exercised through HTTP instead. The public AWS application has since been tested through manual browser uploads and result playback.

```bash
python -m unittest discover -s tests -v
python -m unittest discover -s app_tests -v
```

The portable worker is also directly runnable:

```bash
python -m pushup.process data/raw/your_video.MOV --side right --model models/pose_landmarker_full.task --output results/new-job
```

Use a fresh output directory. See [AWS deployment and operations](aws-deployment.md) for the public application.
