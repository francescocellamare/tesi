import json
import boto3
from urllib.parse import urlencode

def redirect_to_step_functions(lambda_arn, statemachine_name, execution_name):
    lambda_arn_tokens = lambda_arn.split(":")
    partition = lambda_arn_tokens[1]
    region = lambda_arn_tokens[3]
    account_id = lambda_arn_tokens[4]

    print(f"partition={partition}")
    print(f"region={region}")
    print(f"accountId={account_id}")

    execution_arn = f"arn:{partition}:states:{region}:{account_id}:execution:{statemachine_name}:{execution_name}"
    print(f"executionArn={execution_arn}")

    url = f"https://console.aws.amazon.com/states/home?region={region}#/executions/details/{execution_arn}"
    return {
        "statusCode": 302,
        "headers": {
            "Location": url
        }
    }

def lambda_handler(event, context):
    print(f"Event= {json.dumps(event)}")
    query_params = event.get('query', {})
    action = query_params.get('action')
    task_token = query_params.get('taskToken')
    statemachine_name = query_params.get('sm')
    execution_name = query_params.get('ex')

    stepfunctions = boto3.client('stepfunctions')

    if action == "approve":
        message = {"Status": "Approved!"}
    elif action == "reject":
        message = {"Status": "Rejected!"}
    elif action == "manual":
        message = {"Status": "Manual!"}
    else:
        print("Unrecognized action. Expected: approve, reject.")
        return {
            "statusCode": 400,
            "body": json.dumps({"Status": "Failed to process the request. Unrecognized Action."})
        }

    try:
        stepfunctions.send_task_success(
            taskToken=task_token,
            output=json.dumps(message)
        )
        return redirect_to_step_functions(context.invoked_function_arn, statemachine_name, execution_name)
    except Exception as e:
        print(f"Error: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"Error": str(e)})
        }
