# Docker builds

Run these commands from the repository root. Docker Desktop must have its Linux engine running, and the local interfaces require `models/pose_landmarker_full.task`.

## Local upload interface

```bash
docker compose -f docker/compose.yaml up --build
```

Open http://127.0.0.1:8000. This configuration runs as a non-root user, mounts the model read-only, and stores jobs in the existing `pushup-verifier_jobs` named volume. CPU, memory, and process limits apply. Stop with Ctrl+C; avoid `down --volumes` if you want to preserve local jobs.

## Learning interface

```bash
docker compose -f docker/compose.learning.yaml up --build
```

Open http://127.0.0.1:8002. This variant uses the worker image with the local web server command, stores jobs in `results/docker-learning/web-jobs`, and mounts `demo/pilot3B` read-only. It retains the `pushup-learning` Compose project name.

## Cloud worker image

```bash
docker build -f docker/Dockerfile.worker -t pushup-verifier:worker .
```

The final dot is the repository-root build context. The worker includes the processing code, configuration, and AWS dependencies. ECS supplies the `python -m pushup.cloud_worker` command and job-specific arguments through the workflow. Building locally does not update the deployed ECR image or ECS task definition; those require a separate deployment.

Both Dockerfiles use dependency files in `requirements/`. `.dockerignore` excludes recordings, results, models, credentials, and Git history from the build context.

## File moves

| Previous root file | Current location |
|---|---|
| `Dockerfile` | `docker/Dockerfile.local` |
| `Dockerfile.learning` | `docker/Dockerfile.worker` |
| `compose.yaml` | `docker/compose.yaml` |
| `compose.learning.yaml` | `docker/compose.learning.yaml` |
| `docker_hello.py` | `examples/docker_hello.py` |

The hello script remains an early learning example. The worker Dockerfile keeps the synthetic replay command as its default; Compose and ECS override it for their respective workloads.
