import json
import boto3
import io
import re
import zipfile

s3_client = boto3.client('s3')


def createReport(event, context):
    try:
        print("Starting createReport function.")
        
        print(event)
        # Extract bucket and folder names from the event
        s3_Bucket_Name = event["bucketname"]
        s3_Folder = event["key"]
        print(f"Processing S3 bucket: {s3_Bucket_Name}, folder: {s3_Folder}")

        # List objects in the specified S3 folder
        objects = s3_client.list_objects_v2(
            Bucket=s3_Bucket_Name,
            Prefix=s3_Folder
        )
        print("Bucket found")
        print(objects)
        parsed_results = []

        if len(objects['Contents']) > 1:
            # fetching the first object in deployoutp
            s3_Filename = objects['Contents'][1]['Key']
            print(f"Found file: {s3_Filename} in the folder.")

            # Fetch the object from S3 and read its content
            object = s3_client.get_object(Bucket=s3_Bucket_Name, Key=s3_Filename)
            body = object['Body']
            content = body.read()

            # Unzip the object and check for 'report.txt'
            print("Unzipping the file to find 'report.txt'.")
            with zipfile.ZipFile(io.BytesIO(content)) as zip_file:
                if 'report.txt' in zip_file.namelist():
                    with zip_file.open('report.txt') as report_file:
                        report_content = report_file.read().decode('utf-8')
                        print("Found 'report.txt' and reading its content.")
                        print(f"Content: {report_content}")
                else:
                    print("'report.txt' not found in the ZIP file.")
                    raise Exception("'report.txt' not found in the ZIP file.")

            # Parse the report.txt content
            print("Parsing the 'report.txt' content.")
            lines = report_content.splitlines()[5:]  # Skip the first 5 lines
            
            if len(lines) > 0:
                # Parse each line to extract actions and paths
                for line in lines:
                    if line.strip():
                        action, path = line.split(maxsplit=1)
                        parsed_results.append({"path": path, "action": action})

                # Clean up the S3 object after processing
                print(f"Deleting the processed file: {s3_Filename} from S3.")
                s3_client.delete_object(
                    Bucket=s3_Bucket_Name,
                    Key=s3_Filename
                )
            else:
                print("git show didn't show changes (ie. it's a merge)")

        else:
            print("Commit report.txt not found")
            
        # Process the failed test results if available
        s3_key_failedTest = 'build-artifacts/FeedbackBuildArtifacts.zip'
        print(f"Looking for failed test results in {s3_key_failedTest}.")
        test_results = []

        try:
            report = s3_client.get_object(
                Bucket=s3_Bucket_Name,
                Key=s3_key_failedTest
            )
            print(f"{s3_key_failedTest} found")
            body = report['Body']
            content = body.read()

            # Process the failed test results
            with zipfile.ZipFile(io.BytesIO(content)) as zip_file:
                for file in zip_file.namelist():
                    if ".txt" in file:
                        with zip_file.open(file) as fp:
                            file_content = fp.read().decode('utf-8')
                            print(f"Parsing file: {file}.")
                            parsed_content = parse_file(file_content)
                            if parsed_content.get("TestFailures"):
                                print(f"Found failed tests in {file}.")
                                for failure in parsed_content["TestFailures"]:
                                    parsed_results.append(parse_error(failure))
                            test_results.append(parsed_content)

            # Clean up the failed test file
            print(f"Deleting the failed test file: {s3_key_failedTest} from S3.")
            s3_client.delete_object(
                Bucket=s3_Bucket_Name,
                Key=s3_key_failedTest
            )

        except s3_client.exceptions.NoSuchKey:
            print(f"Failed test file '{s3_key_failedTest}' not found.")
            test_results = []

        # Return results as a structured response
        print("Returning the structured results.")
        return {
            'statusCode': 200,
            'body': {
                'testReport': test_results,
                'commitReport': parsed_results
            }
        }

    except Exception as err:
        print(f"Error: {err}")
        return {
            'statusCode': 500,
            'body': {
                'error': str(err)
            }   
        }


def parse_error(error):
    # Extract the path for the test failure
    print(f"Parsing error for test: {error['test']}")
    path = "src/test/java"
    tmp = error["test"].split(".")
    for i in range(len(tmp) - 1):
        path += f"/{tmp[i]}"
    path += '.java'
    return {
        "path": path,
        "action": f"{tmp[len(tmp) - 1]} with error: {error['error']}"
    }

def parse_file(file_content):
    parsed_data = {}

    # Parse the test set name
    test_set_match = re.search(r"Test set:\s+([\w\.]+)", file_content)
    if test_set_match:
        parsed_data["TestSet"] = test_set_match.group(1)

    # Parse test statistics
    stats_match = re.search(
        r"Tests run:\s+(\d+),\s+Failures:\s+(\d+),\s+Errors:\s+(\d+),\s+Skipped:\s+(\d+),\s+Time elapsed:\s+([\d\.]+)\s+s", 
        file_content
    )
    if stats_match:
        parsed_data["TestsRun"] = int(stats_match.group(1))
        parsed_data["Failures"] = int(stats_match.group(2))
        parsed_data["Errors"] = int(stats_match.group(3))
        parsed_data["Skipped"] = int(stats_match.group(4))
        parsed_data["TimeElapsed"] = float(stats_match.group(5))
        
    # Parse failed tests if any
    if parsed_data.get("Failures", 0) or parsed_data.get("Errors", 0) > 0:
        failure_pattern = re.compile(
            r"^([\w\.\s]+?)\s--\s+Time elapsed:\s+[\d\.]+\s+s\s+<<<\s+(ERROR|FAILURE)!\n(.+?)\n", 
            re.MULTILINE
        )
        matches = failure_pattern.findall(file_content)
        parsed_data["TestFailures"] = [
            {"test": match[0].strip(), "error": match[2].strip()} for match in matches
        ]
        
    return parsed_data
