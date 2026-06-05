import boto3
from botocore.exceptions import ClientError

region = "ap-south-1"
sqs = boto3.client("sqs", region_name=region)
queue_name = "production-workload-queue"

print(f"Creating fresh SQS Queue '{queue_name}'...")
try:
    response = sqs.create_queue(QueueName=queue_name)
    print(f"✅ Success! Queue URL: {response['QueueUrl']}")
except ClientError as e:
    print(f"❌ Creation failed: {e.response['Error']['Message']}")
