import boto3

client = boto3.client('codecommit')

def create_testing_branch(repository_name, source_branch, new_branch_name):
    try:
        response = client.get_branch(
            repositoryName=repository_name,
            branchName=source_branch
        )
        commit_id = response['branch']['commitId']

        create_response = client.create_branch(
            repositoryName=repository_name,
            branchName=new_branch_name,
            commitId=commit_id
        )
        print(f"Branch '{new_branch_name}' created successfully from '{source_branch}'.")

    except Exception as e:
        print(f"Error creating branch: {str(e)}")


def commit_response(repository_name, branch_name, content, path):
    parent_commit_id = get_parent_commit_id(repository_name, branch_name)

    # filePath = path.replace("main", "test")
    # filePath = filePath.replace(".java", "Test.java")
    commit_response = client.put_file(
        repositoryName=repository_name,
        branchName=branch_name,
        fileContent=content.encode('utf-8'),
        filePath=path,
        fileMode='NORMAL',
        parentCommitId=parent_commit_id,
        commitMessage="generated test",
        name="ChatGPT",
        email="francesco.pio.cellamare28@gmail.com"
    )

    print(f"File {path} committed successfully")

def commit_delete(repository_name, branch_name, path):
    parent_commit_id = get_parent_commit_id(repository_name, branch_name)

    filePath = path.replace("main", "test")
    filePath = filePath.replace(".java", "Test.java")
    try:
        response = client.delete_file(
            repositoryName=repository_name,
            branchName=branch_name,
            filePath=filePath,
            parentCommitId=parent_commit_id,
            commitMessage=f'deleted test suite for {filePath}',
            name="ChatGPT",
            email="francesco.pio.cellamare28@gmail.com"
        )
        print(f"File {filePath} deleted successfully.")
    
    except client.exceptions.FileDoesNotExistException:
        print(f"Error: The file {filePath} does not exist in the repository.")
    
    except Exception as e:
        print(f"Unexpected error while deleting {filePath}: {str(e)}")
        raise e
    
def get_parent_commit_id(repository_name, branch_name):
    branch_response = client.get_branch(
        repositoryName = repository_name,
        branchName = branch_name
    )

    parent_commit_id = branch_response['branch']['commitId']
    return parent_commit_id
