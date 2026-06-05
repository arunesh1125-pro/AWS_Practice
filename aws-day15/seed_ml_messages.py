import json
import boto3

region = "ap-south-1"
sqs = boto3.client("sqs", region_name=region)
queue_url = sqs.get_queue_url(QueueName="ml-jobs")["QueueUrl"]

print("Injecting sample tasks into 'ml-jobs' queue...")

# Task 1: Success path payload
sqs.send_message(
    QueueUrl=queue_url,
    MessageBody=json.dumps({"jobId": "job-001", "model": "resnet50", "status": "VALID"})
)

# Task 2: Failure path payload
sqs.send_message(
    QueueUrl=queue_url,
    MessageBody=json.dumps({"jobId": "job-002", "model": "vit-large", "status": "CORRUPT"})
)

print("Both tasks successfully staged in queue.")
