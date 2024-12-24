import boto3

# Create a CodeCommit client
codecommit = boto3.client('codecommit')

def checkPullRequest(event, context):
    try:
        # Print the incoming event for debugging
        print("Received event:", event)
        
        pr_id = event['pullRequestId']
        print(f"Pull Request ID: {pr_id}")
        
        response = codecommit.get_pull_request(
            pullRequestId=pr_id
        )
        
        # Print the response from CodeCommit for debugging
        print("CodeCommit response:", response)
        
        # Extract the PR status and merge status from the response
        pr_status = response['pullRequest']['pullRequestStatus']
        merge_metadata = response['pullRequest']['pullRequestTargets'][0].get('mergeMetadata', {})
        merge_status = merge_metadata.get('isMerged', False)
        
        print(f"PR Status: {pr_status}")
        print(f"Merge Status: {merge_status}")
        
        # Check the status and return appropriate response
        if pr_status == 'CLOSED' and merge_status == True:
            print("PR is merged successfully")
            return {
                'statusCode': 200,
                'body': 'PR merged successfully',
                'result': 'Merged'
            }
        elif pr_status == 'CLOSED' and merge_status == False:
            print("PR is closed but not merged")
            raise Exception("Pull request not approved")
        else:
            print("PR is not merged yet")
            return {
                'statusCode': 400,
                'body': 'PR not merged',
                'result': 'NotMerged'
            }
    except Exception as e:
        # Print the error for debugging
        print(f"Error occurred: {str(e)}")
        
        return {
            'statusCode': 500,
            'body': f'Error checking PR status: {str(e)}',
            'result': 'Error'
        }
