import re
import boto3
import time
import codecommit
import openaiModule as openai
import os
import deps

cloudformation_client = boto3.client('cloudformation')

def handleReport(event, context):
    print(f"Event received: {event}")  # Log the entire input event
    
    # Extract task result details
    taskResult = event.get('taskResult', {}).get('Payload', {})
    statusCode = taskResult.get('statusCode', 'Unknown')
    body = taskResult.get('body', {})
    
    print(f"Task result statusCode: {statusCode}")
    print(f"Task result body: {body}")
    
    

    # Get CloudFormation stack information
    try:
        response = cloudformation_client.describe_stacks(StackName=os.environ.get("STACK_NAME"))
        parameters = response['Stacks'][0]['Parameters']
        print("Successfully retrieved CloudFormation stack parameters.")
    except Exception as e:
        print(f"Error fetching CloudFormation stack details: {e}")
        raise
    
    repository_name = None
    branch_name = None

    # Extract repository and branch information
    for param in parameters:
        if param['ParameterKey'] == 'RepositoryName':
            repository_name = param['ParameterValue']
        elif param['ParameterKey'] == 'BranchName':
            branch_name = event.get('branch', param['ParameterValue'])

    print(f"Repository name: {repository_name}")
    print(f"Working on branch: {branch_name}")
    
    generated = deleted = modified = fixed = 0
    regexp = r'.*\.java$'
    createdTestingBranch = branch_name != 'master'
    commit_report = body.get('commitReport', [])

    print(f"Filtering files with regexp: {regexp}")
    filtered_files = [f for f in commit_report if (
            re.match(regexp, f['path']) and
            (
                "controller" in f['path'].lower() or
                "service" in f['path'].lower() or
                "utils" in f['path'].lower()
            )
        )]
    print(f"Filtered files: {filtered_files}")

    if filtered_files:
        # Determine branch name
        if not createdTestingBranch:
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            new_branch_name = f"generated-branch-{timestamp}"
        else:
            new_branch_name = branch_name

        print(f"Generated branch name: {new_branch_name}")
        
        tree = deps.createDepsTree()
        for item in filtered_files:
            print(f"Processing commit item: {item}") 
            
            if not createdTestingBranch:
                print(f"Creating testing branch: {new_branch_name}")
                codecommit.create_testing_branch(repository_name, branch_name, new_branch_name)
                createdTestingBranch = True

            # Handle deleted files
            if item["action"] == "D":
                print(f"Deleting test suite for file: {item['path']}")
                codecommit.commit_delete(repository_name, new_branch_name, item['path'])
                deleted += 1

            # Handle added files
            elif item["action"] == "A":
                print(f"Fetching file for addition: {item['path']}")
                content = codecommit.client.get_file(
                    repositoryName=repository_name, 
                    commitSpecifier=branch_name,
                    filePath=item['path']
                )
                
                contentDeps = []
                print(f"fetching dependencies for {item['path']}")

                if packageToPath(item['path']) in tree.keys():
                    for depsPackage in tree[pathToPackage(item['path'])]:
                        print(f"fetching file {packageToPath(depsPackage)}")
                        contentDeps.append(codecommit.client.get_file(
                            repositoryName=repository_name, 
                            commitSpecifier=branch_name,
                            filePath=packageToPath(depsPackage)
                        ))
                else:
                    print('No dependencies')
                
                
                print(f"Generating test suite for file: {item['path']}")
                testGenerated = openai.create_test_suite_with_deps(content, item['path'], contentDeps)
                filePath = item['path'].replace("main", "test").replace(".java", "Test.java")
                print(f"Committing generated test suite: {filePath}")
                codecommit.commit_response(repository_name, new_branch_name, testGenerated, filePath)
                generated += 1

            # Handle modified files
            elif item["action"] == "M":
                print(f"Handling modification for file: {item['path']}")
                contentSourceCode = codecommit.client.get_file(
                    repositoryName=repository_name,
                    commitSpecifier=branch_name,
                    filePath=item['path']
                )
                
                contentDeps = []
                print(f"fetching dependencies for {item['path']} with list:")

                if packageToPath(item['path']) in tree.keys():
                    for depsPackage in tree[pathToPackage(item['path'])]:
                        print(f"fetching file {packageToPath(depsPackage)}")
                        contentDeps.append(codecommit.client.get_file(
                            repositoryName=repository_name, 
                            commitSpecifier=branch_name,
                            filePath=packageToPath(depsPackage)
                        ))
                else:
                    print('No dependencies')
                    
                testFilePath = item['path'].replace("main", "test").replace(".java", "Test.java")
                contentTestCode = codecommit.client.get_file(
                    repositoryName=repository_name,
                    commitSpecifier=branch_name,
                    filePath=testFilePath
                )
                testUpdated = openai.update_test_suite(contentSourceCode, contentTestCode, None, contentDeps)
                print(f"Committing updated test suite: {testFilePath}")
                codecommit.commit_response(repository_name, new_branch_name, testUpdated, testFilePath)
                modified += 1

            # Handle other cases (e.g., fixing tests)
            else:
                print(f"Handling test fix for file: {item['path']}")
                sourceCodePath = item['path'].replace("/test/", "/main/").replace("Test.java", ".java")
                contentSourceCode = codecommit.client.get_file(
                    repositoryName=repository_name,
                    commitSpecifier=branch_name,
                    filePath=sourceCodePath
                )
                contentDeps = []
                print(f"fetching dependencies for {sourceCodePath}")
                if packageToPath(item['path']) in tree.keys():
                    for depsPackage in tree[pathToPackage(sourceCodePath)]:
                        print(f"fetching file {packageToPath(depsPackage)}")
                        contentDeps.append(codecommit.client.get_file(
                            repositoryName=repository_name, 
                            commitSpecifier=branch_name,
                            filePath=packageToPath(depsPackage)
                        ))
                else:
                    print('No dependencies')
                contentTestCode = codecommit.client.get_file(
                    repositoryName=repository_name,
                    commitSpecifier=branch_name,
                    filePath=item['path']
                )
                testUpdated = openai.update_test_suite(contentSourceCode, contentTestCode, item['action'], contentDeps)
                print(f"are equal {contentTestCode == testUpdated}")
                print(f"Committing fixed test suite for: {item['path']}")
                codecommit.commit_response(repository_name, new_branch_name, testUpdated, item['path'])
                fixed += 1
    else:
        print("No relevant files found to process.")
        new_branch_name = branch_name

    print(f"Summary - Generated: {generated}, Deleted: {deleted}, Modified: {modified}, Fixed: {fixed}")

    nextEvent = {
        "statusCode": 200,
        "body": {
            "message": f"Generated {generated}, Deleted {deleted}, Modified {modified}, Fixed {fixed}",
            "branch": new_branch_name
        }
    }

    print(f"Returning next event: {nextEvent}")
    return nextEvent

def packageToPath(package):
    path = "src/main/java"
    tmp = package.split(".")
    for i in range(len(tmp)):
        path += f"/{tmp[i]}"
    path += '.java'
    return path


def pathToPackage(path):
    package = path.split("src/main/java/")[1].split(".java")[0]
    package = package.replace("/", ".")
    return package
