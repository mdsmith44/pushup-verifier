import json
from pathlib import Path

path = Path("cloud/process-workflow.json")
workflow = json.loads(path.read_text())
states = workflow["States"]

if "AcquireProcessingSlot" in states:
    raise SystemExit("Processing limit is already added.")

states["CheckJob"]["Choices"][0]["Next"] = "AcquireProcessingSlot"

states["AcquireProcessingSlot"] = {
    "Type": "Task",
    "Resource": "arn:aws:states:::dynamodb:updateItem",
    "Parameters": {
        "TableName": "pushup-jobs-dev",
        "Key": {"job_id": {"S": "_processing_slot"}},
        "UpdateExpression": "SET slot_owner = :execution, active_job = :job",
        "ConditionExpression": "attribute_not_exists(slot_owner)",
        "ExpressionAttributeValues": {
            ":execution": {"S.$": "$$.Execution.Id"},
            ":job": {"S.$": "$.job_id"},
        },
    },
    "ResultPath": None,
    "Catch": [{
        "ErrorEquals": ["DynamoDB.ConditionalCheckFailedException"],
        "ResultPath": "$.slot_error",
        "Next": "ProcessingBusy",
    }],
    "Next": "ClaimJob",
}

states["ProcessingBusy"] = {
    "Type": "Fail",
    "Error": "ProcessingBusy",
    "Cause": "Another video is being processed. Try again later.",
}

def release_slot(next_state):
    return {
        "Type": "Task",
        "Resource": "arn:aws:states:::dynamodb:updateItem",
        "Parameters": {
            "TableName": "pushup-jobs-dev",
            "Key": {"job_id": {"S": "_processing_slot"}},
            "UpdateExpression": "REMOVE slot_owner, active_job",
            "ConditionExpression": "slot_owner = :execution",
            "ExpressionAttributeValues": {
                ":execution": {"S.$": "$$.Execution.Id"},
            },
        },
        "ResultPath": None,
        "Next": next_state,
    }

states["ClaimJob"]["Catch"] = [{
    "ErrorEquals": ["States.ALL"],
    "ResultPath": "$.claim_error",
    "Next": "ReleaseSlotAfterClaimFailure",
}]

states["MarkCompleted"].pop("End", None)
states["MarkCompleted"]["Next"] = "ReleaseSlotAfterSuccess"
states["MarkFailed"]["Next"] = "ReleaseSlotAfterFailure"

states["ReleaseSlotAfterSuccess"] = release_slot("ProcessingSucceeded")
states["ReleaseSlotAfterFailure"] = release_slot("ProcessingFailed")
states["ReleaseSlotAfterClaimFailure"] = release_slot("JobUnavailable")

states["ProcessingSucceeded"] = {"Type": "Succeed"}

path.write_text(json.dumps(workflow, indent=2) + "\n")
print("Added the single-job processing limit.")