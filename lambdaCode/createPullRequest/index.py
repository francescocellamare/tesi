import boto3
import os

def createPullRequest(event, context):
    print("Function createPullRequest invoked.")
    codecommit_client = boto3.client('codecommit')
    print("CodeCommit client initialized.")
    
    repository_name = os.environ.get('REPOSITORY_NAME')
    print(f"Repository name from environment: {repository_name}")
    
    branch_name = event.get('branch')
    print(f"Branch name from event: {branch_name}")
    
    try:
        print("Attempting to create a pull request...")
        response = codecommit_client.create_pull_request(
            title='Pull request StepFunction',
            description='The pipeline generated tests and ended correctly',
            targets=[
                {
                    'repositoryName': repository_name,
                    'sourceReference': branch_name,
                    'destinationReference': 'master'
                },
            ]
        )
        print("Pull request created successfully.")
        print(f"Response: {response}")
        
        return {
            'statusCode': 200
        }
    except Exception as err:
        print(f"Error while creating pull request: {err}")
        return {
            'statusCode': 500,
            'body': {
                'error': str(err)
            }
        }
