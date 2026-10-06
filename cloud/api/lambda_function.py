import base64
import json
import os
import re
import time
import uuid
from botocore.exceptions import ClientError

import boto3
from botocore.config import Config


table = boto3.resource("dynamodb").Table(os.environ["JOBS_TABLE"])
s3 = boto3.client("s3", config=Config(signature_version="s3v4"))
bucket = os.environ["UPLOAD_BUCKET"]

workflows = boto3.client("stepfunctions")
workflow_arn = os.environ["PROCESS_WORKFLOW_ARN"]

MAX_BYTES = 200 * 1024 * 1024
VIDEO_TYPES = {
    "video/mp4": "mp4",
    "video/quicktime": "mov",
    "video/webm": "webm",
}


def response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Cache-Control": "no-store",
        },
        "body": json.dumps(body),
    }


def is_tester(claims):
    groups = claims.get("cognito:groups", [])

    if isinstance(groups, str):
        groups = [
            part.strip("\"'")
            for part in re.split(r"[\s,\[\]]+", groups)
            if part
        ]

    return "pushup-testers" in groups


def create_job(event, owner_id):
    try:
        body = event.get("body") or ""
        if event.get("isBase64Encoded"):
            body = base64.b64decode(body, validate=True).decode("utf-8")

        if len(body) > 4096:
            return response(400, {"message": "Request is too large."})

        data = json.loads(body)
        if not isinstance(data, dict):
            raise ValueError()

    except (ValueError, UnicodeError):
        return response(400, {"message": "Invalid JSON request."})

    size = data.get("size")
    content_type = data.get("content_type")
    side = data.get("side")

    if type(size) is not int or not 1 <= size <= MAX_BYTES:
        return response(400, {
            "message": "Choose a nonempty video no larger than 200 MiB."
        })

    if not isinstance(content_type, str) or content_type not in VIDEO_TYPES:
        return response(400, {
            "message": "Choose an MP4, MOV, or WebM video."
        })

    if side not in ("left", "right"):
        return response(400, {"message": "Choose left or right camera side."})

    job_id = str(uuid.uuid4())
    extension = VIDEO_TYPES[content_type]
    key = f"inputs/uploads/{owner_id}/{job_id}/source.{extension}"

    # S3 enforces the declared file size and content type.
    upload = s3.generate_presigned_post(
        Bucket=bucket,
        Key=key,
        Fields={"Content-Type": content_type},
        Conditions=[
            {"Content-Type": content_type},
            ["content-length-range", size, size],
        ],
        ExpiresIn=300,
    )

    table.put_item(
        Item={
            "job_id": job_id,
            "owner_id": owner_id,
            "status": "awaiting_upload",
            "input_key": key,
            "size_bytes": size,
            "content_type": content_type,
            "side": side,
            "created_at": int(time.time()),
        },
        ConditionExpression="attribute_not_exists(job_id)",
    )

    return response(201, {
        "job_id": job_id,
        "status": "awaiting_upload",
        "upload": upload,
        "upload_expires_in": 300,
    })

def confirm_upload(event, owner_id):
    job_id = (event.get("pathParameters") or {}).get("job_id", "")

    try:
        uuid.UUID(job_id)
    except (ValueError, TypeError):
        return response(400, {"message": "Invalid job ID."})

    job = table.get_item(
        Key={"job_id": job_id},
        ConsistentRead=True,
    ).get("Item")

    # Do not reveal another user's job.
    if not job or job.get("owner_id") != owner_id:
        return response(404, {"message": "Job not found."})

    if job["status"] == "ready":
        return response(200, {"job_id": job_id, "status": "ready"})

    if job["status"] != "awaiting_upload":
        return response(409, {
            "message": "This job is no longer awaiting an upload."
        })

    try:
        uploaded = s3.head_object(
            Bucket=bucket,
            Key=job["input_key"],
        )
    except ClientError as error:
        code = error.response["Error"]["Code"]

        if code != "ExecutionAlreadyExists":
            print(json.dumps({
                "event": "start_execution_failed",
                "error_code": code,
                "message": error.response["Error"].get("Message", ""),
            }))
            return response(503, {
                "message": "Could not start processing. Please try again."
            })

        raise

    if (
        uploaded["ContentLength"] != job["size_bytes"]
        or uploaded.get("ContentType") != job["content_type"]
    ):
        return response(409, {
            "message": "Uploaded file does not match the job."
        })

    try:
        table.update_item(
            Key={"job_id": job_id},
            UpdateExpression=(
                "SET #status = :ready, verified_at = :now, "
                "input_etag = :etag"
            ),
            ConditionExpression=(
                "owner_id = :owner AND #status = :awaiting"
            ),
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={
                ":ready": "ready",
                ":awaiting": "awaiting_upload",
                ":owner": owner_id,
                ":now": int(time.time()),
                ":etag": uploaded["ETag"],
            },
        )
    except ClientError as error:
        if error.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return response(409, {
                "message": "Job status changed. Please try again."
            })
        raise

    return response(200, {"job_id": job_id, "status": "ready"})

def owned_job(event, owner_id):
    job_id = (event.get("pathParameters") or {}).get("job_id", "")

    try:
        uuid.UUID(job_id)
    except (ValueError, TypeError):
        return None

    job = table.get_item(
        Key={"job_id": job_id},
        ConsistentRead=True,
    ).get("Item")

    if not job or job.get("owner_id") != owner_id:
        return None

    return job


def execution_details(execution_arn):
    try:
        return workflows.describe_execution(executionArn=execution_arn)
    except ClientError as error:
        if error.response["Error"]["Code"] == "ExecutionDoesNotExist":
            return None
        raise


def start_job(event, owner_id):
    job = owned_job(event, owner_id)

    if not job:
        return response(404, {"message": "Job not found."})

    job_id = job["job_id"]

    if job["status"] in ("processing", "completed"):
        return response(200, {
            "job_id": job_id,
            "status": job["status"],
        })

    if job["status"] != "ready":
        return response(409, {
            "message": "This job is not ready for processing."
        })

    previous_arn = job.get("last_start_execution")
    previous = execution_details(previous_arn) if previous_arn else None

    if previous and previous["status"] == "RUNNING":
        return response(202, {"job_id": job_id, "status": "starting"})

    slot = table.get_item(
        Key={"job_id": "_processing_slot"},
        ConsistentRead=True,
    ).get("Item", {})

    if slot.get("slot_owner"):
        return response(409, {
            "message": "Another video is processing. Please try again later."
        })

    if previous_arn and previous is None:
        # Retry an execution that was reserved but might not have started.
        execution_arn = previous_arn
        name = execution_arn.rsplit(":", 1)[1]
    else:
        name = f"job-{job_id}-{uuid.uuid4().hex}"
        execution_arn = (
            workflow_arn.replace(":stateMachine:", ":execution:")
            + ":" + name
        )

    values = {
        ":owner": owner_id,
        ":ready": "ready",
        ":execution": execution_arn,
    }

    condition = "#status = :ready AND owner_id = :owner"

    if previous_arn:
        condition += " AND last_start_execution = :previous"
        values[":previous"] = previous_arn
    else:
        condition += " AND attribute_not_exists(last_start_execution)"

    try:
        table.update_item(
            Key={"job_id": job_id},
            UpdateExpression="SET last_start_execution = :execution",
            ConditionExpression=condition,
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues=values,
        )
    except ClientError as error:
        if error.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return response(409, {
                "message": "Job status changed. Refresh before trying again."
            })
        raise

    try:
        workflows.start_execution(
            stateMachineArn=workflow_arn,
            name=name,
            input=json.dumps({
                "job_id": job_id,
                "owner_id": owner_id,
            }),
        )
    except ClientError as error:
        if error.response["Error"]["Code"] != "ExecutionAlreadyExists":
            return response(503, {
                "message": "Could not start processing. Please try again."
            })

    return response(202, {"job_id": job_id, "status": "starting"})

def get_job(event, owner_id):
    job = owned_job(event, owner_id)

    if not job:
        return response(404, {"message": "Job not found."})

    job_id = job["job_id"]
    status = job["status"]

    body = {
        "job_id": job_id,
        "status": status,
    }

    # A start request can be accepted before the workflow claims the job.
    if status == "ready" and job.get("last_start_execution"):
        execution = execution_details(job["last_start_execution"])

        if execution and execution["status"] == "RUNNING":
            body["status"] = "starting"
        elif execution and execution["status"] != "SUCCEEDED":
            body["message"] = (
                "Processing did not start. You can try again."
            )

    # Detect interrupted workflows without automatically unlocking workers.
    if status == "processing" and job.get("execution_arn"):
        execution = execution_details(job["execution_arn"])

        if execution and execution["status"] in (
            "FAILED", "TIMED_OUT", "ABORTED",
        ):
            body["status"] = "failed"
            body["message"] = (
                "Processing was interrupted. Please contact the site owner."
            )

    if status == "failed":
        body["message"] = (
            "Video processing failed. Please contact the site owner."
        )

    if status == "completed":
        prefix = f"outputs/jobs/{owner_id}/{job_id}"

        artifacts = {
            "video": ("annotated.mp4", "inline"),
            "chart": ("chart.png", "inline"),
            "report": ("report.json", "attachment"),
        }

        body["results"] = {}

        for kind, (filename, disposition) in artifacts.items():
            body["results"][kind] = s3.generate_presigned_url(
                "get_object",
                Params={
                    "Bucket": bucket,
                    "Key": f"{prefix}/{filename}",
                    "ResponseContentDisposition": (
                        f'{disposition}; filename="{filename}"'
                    ),
                },
                ExpiresIn=600,
            )

        body["results_expires_in"] = 600

    return response(200, body)

def lambda_handler(event, context):
    claims = (
        event.get("requestContext", {})
        .get("authorizer", {})
        .get("jwt", {})
        .get("claims", {})
    )

    if claims.get("token_use") != "access" or not claims.get("sub"):
        return response(401, {"message": "Sign-in required."})

    can_process = is_tester(claims)
    route = event.get("routeKey")

    if route == "GET /me":
        return response(200, {
            "user_id": claims["sub"],
            "can_process": can_process,
        })

    if route == "POST /jobs":
        if not can_process:
            return response(403, {
                "message": "Video processing is limited to approved testers."
            })

        return create_job(event, claims["sub"])

    if route == "POST /jobs/{job_id}/confirm":
        if not can_process:
            return response(403, {
                "message": "Video processing is limited to approved testers."
            })

        return confirm_upload(event, claims["sub"])

    if route == "POST /jobs/{job_id}/start":
        if not can_process:
            return response(403, {
                "message": "Video processing is limited to approved testers."
            })

        return start_job(event, claims["sub"])

    if route == "GET /jobs/{job_id}":
        return get_job(event, claims["sub"])

    return response(404, {"message": "Route not found."})