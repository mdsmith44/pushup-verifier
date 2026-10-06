import base64
import json
import os
import re
import time
import uuid

import boto3
from botocore.config import Config


table = boto3.resource("dynamodb").Table(os.environ["JOBS_TABLE"])
s3 = boto3.client("s3", config=Config(signature_version="s3v4"))
bucket = os.environ["UPLOAD_BUCKET"]

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

    return response(404, {"message": "Route not found."})