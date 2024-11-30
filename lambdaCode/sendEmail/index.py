import json
import boto3
import urllib.parse
import os
import io
import zipfile
import re

'''
    State input: {
        ExecutionContext: {
            ...
        },
        APIGatewayEndpoint: string,
        TestResult: {
            ...
        }
    }

'''
def sendEmail(event, context):
    print("Loading function")
    print(f"event= {json.dumps(event)}")
    print(f"context= {context}")

    # Extract details from the event
    execution_context = event.get('ExecutionContext', {})
    print(f"executionContext= {execution_context}")

    execution_name = execution_context.get('Execution', {}).get('Name', 'UnknownExecutionName')
    print(f"executionName= {execution_name}")

    statemachine_name = execution_context.get('StateMachine', {}).get('Name', 'UnknownStateMachineName')
    print(f"statemachineName= {statemachine_name}")

    task_token = execution_context.get('Task', {}).get('Token', '')
    print(f"taskToken= {task_token}")

    apigw_endpoint = event.get('APIGatewayEndpoint', 'https://example.com')
    print(f"apigwEndpoint= {apigw_endpoint}")

    # Generate approval and rejection endpoints
    approve_endpoint = f"{apigw_endpoint}/execution?action=approve&ex={execution_name}&sm={statemachine_name}&taskToken={urllib.parse.quote(task_token)}"
    print(f"approveEndpoint= {approve_endpoint}")

    reject_endpoint = f"{apigw_endpoint}/execution?action=reject&ex={execution_name}&sm={statemachine_name}&taskToken={urllib.parse.quote(task_token)}"
    print(f"rejectEndpoint= {reject_endpoint}")

    # Define the SNS topic for sending emails
    email_sns_topic = os.environ.get("SNS_TOPIC_ARN")
    print(f"emailSnsTopic= {email_sns_topic}")
    
    email_message = ''
    test_report = event['Report']['testReport']
    if test_report:
        for item in test_report:
            email_message += f"""
            Test Set: {item["TestSet"]}

            Test Summary:
            Tests Run: {item["TestsRun"]}
            Failures: {item["Failures"]}
            Errors: {item["Errors"]}
            Skipped: {item["Skipped"]}
            Time Elapsed: {item["TimeElapsed"]} seconds\n
            """                     
            if 'TestFailures' in item and item['TestFailures']:
                email_message += "Failing report:\n"
                for item in item['TestFailures']:
                    email_message += f"test {item['test']}: {item['error']}\n"

    else:
        email_message += f"""
        No test report found for execution {execution_name}.
        """
    
    email_message += f"""
    Execution: {execution_name}
    StateMachine: {statemachine_name}

    Approval required for the execution. Please review the results below:

    Approve: {approve_endpoint}
    Reject: {reject_endpoint}
    """

    # Send the message using SNS
    sns = boto3.client('sns')
    try:
        response = sns.publish(
            TopicArn=email_sns_topic,
            Subject="Required approval from AWS Step Functions",
            Message=email_message
        )
        print(f"MessageID is {response['MessageId']}")
        
        return {
            'statusCode': 200,
            'message': 'email sent'
        }
    except Exception as e:
        print(f"Error: {e}")
        raise e
