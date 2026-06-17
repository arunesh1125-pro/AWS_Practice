import json
import os
import boto3

def lambda_handler(event, context):
    print("SAM Local Execution Engine Initiated.")
    
    # Safely handle localized invocation events or standard API Gateway inputs
    body = event.get('body', '{}')
    if isinstance(body, str):
        try:
            body_data = json.loads(body)
        except json.JSONDecodeError:
            body_data = {"input": body}
    else:
        body_data = body

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps({
            "status": "Online",
            "message": "Hello from SAM CLI Local Sandbox Context!",
            "received_payload": body_data
        })
    }
