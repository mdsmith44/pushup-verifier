# AWS deployment handoff — not yet provisioned

The user does not yet have an AWS account. The local upload pipeline is implemented and tested; AWS infrastructure and public authentication are not deployed. Proposed region: `us-west-2` (Oregon). Proposed budget target: $25/month for low-volume portfolio use, subject to an itemized estimate and user approval before resource creation. This is not a cost guarantee or hard cap.

## Proposed public architecture

1. CloudFront and a private S3 origin serve the responsive frontend over HTTPS.
2. Cognito sign-in restricts the initial beta to invited users. API Gateway/Lambda validates tokens and checks job ownership; no public anonymous processing initially.
3. The API creates a job in DynamoDB and issues a short-lived S3 presigned upload policy constrained to a generated per-user/job key and maximum size. Upload success is verified before job dispatch. A filename alone never supplies a storage path.
4. A bounded durable dispatcher/orchestrator starts an ECS Fargate task using the same portable processing container. Use a task role limited to required object prefixes and status updates. Store model/config versions in the image or a private versioned model object verified by hash. No GPU initially.
5. The task writes video/chart/report results into a private result prefix and updates job state. Ownership-checked API endpoints issue short-lived result URLs. Lifecycle rules remove uploads/results, with explicit deletion support.
6. CloudWatch records operational logs and errors without video content. Monitor failed jobs, queue age, processing duration and monthly cost. Restrict concurrency, per-user job quotas, input sizes and task runtime in addition to budgets.

The local SQLite queue, unauthenticated result URLs, and local file upload endpoint are development conveniences and must not be deployed unchanged as this public service. An S3 task adapter, authenticated API/frontend integration, infrastructure-as-code, and cloud integration tests remain to implement after account setup. AWS Step Functions supports waiting for ECS/Fargate tasks via `ecs:runTask.sync`; job concurrency/idempotency/retry limits must be explicitly designed, not assumed.

## Cost review before provisioning

Benchmark a 2-vCPU/4-GB x86 task as a starting point, then revise based on measured memory/runtime. Estimate costs for 100 short jobs/month plus image pulls, ECR storage, S3 storage/requests, downloads/CloudFront, Lambda/API/DynamoDB, orchestration, logs, and any public IPv4/networking charges. Avoid an always-running worker, load balancer, and NAT gateway unless their costs are deliberately approved. Public-subnet tasks with no inbound rules are one cost-conscious option requiring review; private endpoints/NAT have different fixed costs.

AWS Budgets alerts can be delayed and do not enforce a hard spend ceiling. Pair the proposed $25 alert budget with application quotas, bounded concurrency, task timeouts, and a tested stop/teardown procedure. Do not assume free-tier eligibility or free credits when estimating.

## Account setup handoff

The user should create the account directly with AWS, entering payment/identity information and accepting terms themselves. Enable MFA for the root account and use short-lived federated access for daily deployment; never paste root credentials, access keys, or passwords into chat or commit them. Once the account is ready, configure local authenticated CLI access and review the actual deployment plan/estimate before provisioning.

Official references:

- [AWS account creation](https://docs.aws.amazon.com/accounts/latest/reference/manage-acct-creating.html)
- [S3 presigned uploads](https://docs.aws.amazon.com/AmazonS3/latest/userguide/PresignedUrlUploadObject.html)
- [Step Functions ECS/Fargate integration](https://docs.aws.amazon.com/step-functions/latest/dg/connect-ecs.html)
- [Fargate pricing](https://aws.amazon.com/fargate/pricing/)
- [AWS Budgets behavior and notification delay](https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-managing-costs.html)
