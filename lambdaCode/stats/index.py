import json
import boto3
import time

# Create a CloudWatch Logs client
client = boto3.client('logs')

def stats(event, context):
    # Define the log group and query
    log_group_name = '/aws/stepfunctions/FeedbackStateMachineLogs'  # Example log group
    query = """
    fields @timestamp, @message
    | filter details.name = "HandleReport" and (type = "TaskStateEntered" or type = "TaskStateExited")
    | parse @message '{"details":{"name":"*"}}' as phase_name
    | stats min(event_timestamp) as start_time, max(event_timestamp) as end_time by phase_name
    | display phase_name, (end_time - start_time)/1000 as duration_seconds
    """

    # Start the CloudWatch Logs Insights query
    start_query_response = client.start_query(
        logGroupName=log_group_name,
        startTime=int(time.time() - 3600) * 1000,  # Lookback period (e.g., last 1 hour)
        endTime=int(time.time()) * 1000,
        queryString=query
    )

    # Get the query ID to retrieve results later
    query_id = start_query_response['queryId']

    # Wait for the query to finish
    print(f"Started query with ID: {query_id}")
    response = None
    while response == None or response['status'] == 'Running':
        print("Waiting for query to complete...")
        time.sleep(1)  # Wait for 1 second before checking the status
        response = client.get_query_results(
            queryId=query_id
        )

    # Process the results if the query has finished
    if response['status'] == 'Complete':
        results = response['results']
        if results:
            # Extract the duration from the results
            duration = results[0][1]['value']  # The duration is in the second column (index 1)
            print(f"Duration for HandleReport phase: {duration} seconds")

            # Return the result (could be used further down the pipeline or saved to S3)
            return {
                'status': 'success',
                'phase': 'HandleReport',
                'duration_seconds': duration
            }
        else:
            return {
                'status': 'failure',
                'message': 'No results found for HandleReport'
            }
    else:
        return {
            'status': 'failure',
            'message': f"Query failed with status {response['status']}"
        }
