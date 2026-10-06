# AWS deployment and operations

The [public application](https://dg05a9no1enlg.cloudfront.net/) is deployed in **us-east-2 (Ohio)**. Google and email/password accounts can upload and process videos without manual tester approval. Anonymous visitors can view the published sample.

## Deployed resources

| Resource | Identifier |
|---|---|
| CloudFront distribution | `E1FSJSR2TLVG9` |
| Website bucket | `mdsmith44-pushup-verifier-site` |
| Private processing bucket | `mdsmith44-pushup-verifier-dev` |
| HTTP API | `fe20wvd7l2` |
| Cognito user pool | `us-east-2_kED1hCUkT` |
| Public Cognito app client | `1fo6v4t111g1urebnkenv648hp` |
| Lambda function / execution role | `pushup-api` / `pushup-api-role` |
| DynamoDB job table | `pushup-jobs-dev` |
| Standard Step Functions workflow | `pushup-process-dev` |
| ECS task definition | `pushup-worker:2` |
| ECR worker image | `pushup-verifier:v3` |

These identifiers describe the tested deployment; update them when deploying a new revision. The repository contains application code, workflow definition, and retention configuration, rather than a complete infrastructure-as-code stack.

## Processing flow

1. CloudFront serves the website from its private S3 origin. Cognito uses authorization code with PKCE and a public app client without a client secret.
2. API Gateway authorizes JWTs. Lambda checks access-token claims and ownership using the authenticated user's subject, not an email supplied by the browser.
3. `POST /jobs` creates a job and returns a temporary upload form. `POST /jobs/{job_id}/confirm` verifies the uploaded object's size/type and records its ETag.
4. `POST /jobs/{job_id}/start` starts the workflow. A conditional DynamoDB claim allows one processing job at a time. Busy users retry; this is not a multi-job cloud queue.
5. The workflow copies the verified input conditionally on its recorded ETag, then runs the Fargate worker with 2 vCPUs and 4 GB memory. Worker and workflow limits are 15 and 20 minutes respectively.
6. The workflow checks the exit code, marks success/failure, and releases the processing slot. `GET /jobs/{job_id}` returns ownership-checked temporary links to the video, chart, and report. `GET /me` supplies account status.

Public-subnet workers have no inbound security-group rules and use task roles for object access. The local unauthenticated web server is a development interface and is not the public API.

## Website updates

From the repository root in the configured Linux/WSL environment:

```bash
npm ci
npm run build:auth
aws s3 sync site/ s3://mdsmith44-pushup-verifier-site/ --profile pushup --region us-east-2
aws cloudfront create-invalidation --distribution-id E1FSJSR2TLVG9 --paths '/*' --profile pushup --no-cli-pager
```

Edit `site-src/auth.js`, then rebuild the generated `site/static/auth.js`. Keep the published sample assets available in `site/` when syncing. Authenticate the configured AWS profile again if its session has expired.

## Worker and workflow updates

Build the worker from the root context using `docker/Dockerfile.worker`; see [Docker builds](../docker/README.md). Push the intended image to ECR, register an ECS task-definition revision, and update both the workflow's task definition and any IAM resource restrictions to that revision. A local image build alone does not change the deployed worker.

Validate the saved workflow before updating it:

```bash
aws stepfunctions validate-state-machine-definition \
  --definition file://cloud/process-workflow.json \
  --type STANDARD --region us-east-2 --profile pushup --no-cli-pager
```

Update the existing workflow with the validated definition using its ARN from the AWS console. Save Lambda changes in `cloud/api/lambda_function.py` as well as deploying them to `pushup-api`.

## Retention and recovery

`cloud/s3-lifecycle.json` expires `inputs/uploads/` and `inputs/verified/` after 1 day, and `outputs/jobs/` after 7 days. S3 deletion is asynchronous; these rules do not remove the model or original pilot input outside those prefixes. Result URLs expire after 10 minutes and can be renewed while artifacts remain. DynamoDB job-record expiry and explicit cloud result deletion remain future work.

The `_processing_slot` record is idle when it contains only `job_id`. Normal success/failure paths release its ownership fields. An aborted execution, workflow timeout, or failed cleanup can leave a lock. Check the execution and confirm that its ECS worker has stopped before repairing a stale lock; do not clear it while a task might still be running.

The browser can reconnect to its saved job after refreshing the same tab. Worker launch failures, failed processing, unavailable results, and busy-slot responses have distinct recovery paths; do not restart processing blindly after an uncertain response. The API retains execution identity to help avoid duplicate launches.

## Checks and remaining work

Manual checks exercised Google and email sign-in, upload/confirmation, processing, annotated playback, chart/report downloads, refresh reconnection, and expired-result messaging. Unsigned API calls return 401; another account cannot retrieve a user's job. The worker output matched the mixed validation clip's five completions, three accepted and two rejected.

One-job concurrency and timeouts bound individual processing, but are not a monthly spending cap. Per-user quotas, broader automated cloud integration checks, and recovery improvements remain planned. Research validation is still limited; see [research findings](research-overview.md).
