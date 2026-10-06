import json
import re


def response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Cache-Control": "no-store",
        },
        "body": json.dumps(body),
    }


def lambda_handler(event, context):
    # These claims come from API Gateway's JWT authorizer.
    claims = (
        event.get("requestContext", {})
        .get("authorizer", {})
        .get("jwt", {})
        .get("claims", {})
    )

    if claims.get("token_use") != "access" or not claims.get("sub"):
        return response(401, {"message": "Sign-in required."})

    if event.get("routeKey") != "GET /me":
        return response(404, {"message": "Route not found."})

        # API Gateway can represent group membership as a string or a list.
    raw_groups = claims.get("cognito:groups", [])

    if isinstance(raw_groups, str):
        groups = [
            group.strip().strip("\"'")
            for group in re.split(r"[\s,\[\]]+", raw_groups)
            if group.strip().strip("\"'")
        ]
    else:
        groups = raw_groups

    can_process = "pushup-testers" in groups

    return response(200, {
        "user_id": claims["sub"],
        "can_process": can_process
    })