import json

def lambda_handler(event, context):
    print("Lambda inside VPC executed successfully!")
    return {
        "statusCode": 200,
        "body": json.dumps({"message": "Hello from inside the VPC!"})
    }