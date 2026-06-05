import json
import time
import boto3
from botocore.exceptions import ClientError

region = "ap-south-1"
sqs = boto3.client("sqs", region_name=region)
iam = boto3.client("iam")
sts = boto3.client("sts")

account_id = sts.get_caller_identity()["Account"]

# 1. Create Target SQS Queue
print("Creating SQS Queue 'model-events-queue'...")
queue_url = sqs.create_queue(QueueName="model-events-queue")["QueueUrl"]
queue_arn = sqs.get_queue_attributes(
    QueueUrl=queue_url, AttributeNames=["QueueArn"]
)["Attributes"]["QueueArn"]
import json
import time
import boto3
from botocore.exceptions import ClientError

region = "ap-south-1"
sqs = boto3.client("sqs", region_name=region)
iam = boto3.client("iam")
sts = boto3.client("sts")

account_id = sts.get_caller_identity()["Account"]

# 1. Create Target SQS Queue
print("Creating SQS Queue 'model-events-queue'...")
queue_url = sqs.create_queue(QueueName="model-events-queue")["QueueUrl"]
queue_arn = sqs.get_queue_attributes(
    QueueUrl=queue_url, AttributeNames=["QueueArn"]
)["Attributes"]["QueueArn"]

# 2. Create IAM Role for Lambda
role_name = "SNSLambdaExecutionRole"
trust_policy = {
    "Version": "2012-10-17",
    "Statement": [{"Effect": "Allow", "Principal": {"Service": "lambda.amazonaws.com"}, "Action": "sts:AssumeRole"}],
}

try:
    role_arn = iam.create_role(
        RoleName=role_name, AssumeRolePolicyDocument=json.dumps(trust_policy)
    )["Role"]["Arn"]
    iam.attach_role_policy(
        RoleName=role_name, PolicyArn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
    )
    print("Execution role generated. Waiting 10s for global sync...")
    time.sleep(10)
except iam.exceptions.EntityAlreadyExistsException:
    role_arn = iam.get_role(RoleName=role_name)["Role"]["Arn"]

print(f"✅ Success! Queue ARN: {queue_arn} | Role ARN: {role_arn}")
