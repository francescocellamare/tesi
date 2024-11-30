import re
import boto3
import time
import codecommit
import openaiModule as openai
import os

cloudformation_client = boto3.client('cloudformation')

'''
    State to 

    State input:
    [
    	// Added
    	{
    		Path: "path1",
    		Action: "create"
    	},
    	// Deleted
    	{
    		Path: "path2",
    		Action: "remove"
    	},
    	// Failed -- not here
    	{
    		Path: "path3",
    		Action: "com.example.demo...testfile1: Assertion failed"
    	},
    	// Modified
    	{
    		Path: "path4",
    		Action: "modified"
    	},
    ]
    
    State output:
    {
        "statusCode": 200,
        "body": {
            "message": "Generated x test files",
            "branch": "generated-branch-20241121-133820"
        }
    }
'''
def handleReport(event, context):
    print(f"Event received: {event}")  # Print the event input
    
    taskResult = event['taskResult']['Payload']
    statusCode = taskResult['statusCode']
    body = taskResult['body']
    
    print(f"Task result statusCode: {statusCode}")
    print(f"Task result body: {body}")

    response = cloudformation_client.describe_stacks(StackName=os.environ.get("STACK_NAME"))
    parameters = response['Stacks'][0]['Parameters']
    repository_name = None
    branch_name = None
    
    # retrieve info about the repository
    for param in parameters:
        if param['ParameterKey'] == 'RepositoryName':
            repository_name = param['ParameterValue']
        elif param['ParameterKey'] == 'BranchName':
            # branch_name = param['ParameterValue']
            branch_name = event['branch']

    print(f"Repository name: {repository_name}")
    print(f"Working on branch: {branch_name}")
    
    generated = 0
    deleted = 0
    modified = 0
    fixed = 0
    regexp = '.java$'
    createdTestingBranch = branch_name != 'master'

    if (createdTestingBranch == False):
        # create the new branch name
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        new_branch_name = f"generated-branch-{timestamp}"
    else:
        new_branch_name = branch_name

    print(f"Generated branch name: {new_branch_name}")

    commit_report = body['commitReport']
    # for each item in the state input (so the path, action pair)
    for item in commit_report:
        print(f"Processing commit item: {item}")  # Print each commit item
        
        # look for .java files
        if re.search(regexp, item['path']) == None:
            print(f"Skipping non-Java file: {item['path']}")
            continue
        
        # create the branch at the first execution
        if createdTestingBranch == False:
            print(f"Creating testing branch: {new_branch_name}")
            codecommit.create_testing_branch(repository_name, branch_name, new_branch_name)
            createdTestingBranch = True

        # if the file has been deleted then delete the relative test suite
        if item["action"] == "D":
            print(f"Deleting test suite for file: {item['path']}")
            codecommit.commit_delete(repository_name, new_branch_name, item['path'])
            deleted += 1
            
        elif item["action"] == "A":
            print(f"Fetching new file for action {item['action']}: {item['path']}")
            content = codecommit.client.get_file(
                repositoryName=repository_name, 
                commitSpecifier=branch_name,
                filePath=item['path']
            )

            print(f"Generating test suite for file: {item['path']}")
            testGenerated = openai.create_test_suite(content)
            filePath = item['path'].replace("main", "test")
            filePath = filePath.replace(".java", "Test.java")
            codecommit.commit_response(repository_name, new_branch_name, testGenerated, filePath)
            generated += 1
            
        elif item["action"] == "M":
            print('Modify action detected')
            # retrieve the source code file
            contentSourceCode = codecommit.client.get_file(
                repositoryName=repository_name,
                commitSpecifier=branch_name,
                filePath=item['path']
            )
            
            testFilePath = item['path'].replace("main", "test")
            testFilePath = testFilePath.replace(".java", "Test.java")
            # retrieve the test code file
            contentTestCode = codecommit.client.get_file(
                repositoryName=repository_name,
                commitSpecifier=branch_name,
                filePath=testFilePath
            )
            
            testUpdated = openai.update_test_suite(contentSourceCode, contentTestCode, None)
            
            filePath = item['path'].replace("main", "test")
            filePath = filePath.replace(".java", "Test.java")
            codecommit.commit_response(repository_name, new_branch_name, testUpdated, filePath)
            modified += 1 
        else:
            print('Test fixing action detected')
            sourceCodePath = item['path'].replace("/test/", "/main/")
            sourceCodePath = sourceCodePath.replace("Test.java", ".java")
            contentSourceCode = codecommit.client.get_file(
                repositoryName=repository_name,
                commitSpecifier=branch_name,
                filePath=sourceCodePath
            )
            
            
            contentTestCode = codecommit.client.get_file(
                repositoryName=repository_name,
                commitSpecifier=branch_name,
                filePath=item['path']
            )
        
            testUpdated = openai.update_test_suite(contentSourceCode, contentTestCode, item['action'])
            
            codecommit.commit_response(repository_name, new_branch_name, testUpdated, item['path'])
            fixed += 1 
    
    print(f"Generated {generated} -- Deleted {deleted} -- Modified {modified} -- Fixed {fixed}")
    
    nextEvent = {
        "statusCode": 200,
        "body": {
            "message": f"Generated {generated} -- Deleted {deleted} -- Modified {modified} -- Fixed {fixed}",
            "branch": new_branch_name 
        }
    }
    
    print(f"Returning next event: {nextEvent}")
    return nextEvent
