import boto3
from botocore.exceptions import ClientError

region = "ap-south-1"
sqs = boto3.client("sqs", region_name=region)

print("Creating Standard SQS Queue 'ml-jobs'...")
try:
    response = sqs.create_queue(
        QueueName="ml-jobs",
        Attributes={
            "ReceiveMessageWaitTimeSeconds": "20"  # Enables Long Polling at queue level
        }
    )
    print(f"Queue ready! URL: {response['QueueUrl']}")
except ClientError as e:
    print(f"Configuration failed: {e.response['Error']['Message']}")
