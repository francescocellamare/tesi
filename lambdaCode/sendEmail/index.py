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
        No test report found for execution {execution_name} due to a compilation error. Try to fix it and approve the request otherwise reject.
        """
        
    branch = execution_context['Execution']['Input']['branch']
        
    commit_info = get_last_commit_link('SpringProjectRepository', branch)
    
    email_message += f"""
    Execution: {execution_name}
    StateMachine: {statemachine_name}
    Commit: {commit_info['commit_url']}

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


def get_last_commit_link(repo_name, branch_name):
    # Initialize the CodeCommit client
    codecommit = boto3.client('codecommit')
    
    try:
        # Get the default branch name for the repository
        repo_info = codecommit.get_repository(repositoryName=repo_name)

        # Get the last commit ID from the default branch
        branch_info = codecommit.get_branch(
            repositoryName=repo_name,
            branchName=branch_name
        )
        last_commit_id = branch_info['branch']['commitId']

        # Construct the URL to the commit page
        # repo_clone_url_http = repo_info['repositoryMetadata']['cloneUrlHttp']
        # repo_base_url = repo_clone_url_http.replace(".git", "")
        repo_base_url = "https://eu-south-1.console.aws.amazon.com/codesuite/codecommit/repositories/"
        commit_url = f"{repo_base_url}{repo_name}/browse/{last_commit_id}?region=eu-south-1"
        return {
            "last_commit_id": last_commit_id,
            "commit_url": commit_url
        }

    except Exception as e:
        print(f"Error retrieving last commit info: {e}")
        return None