import json
import time
import boto3
from botocore.exceptions import ClientError

region = "ap-south-1"
sqs = boto3.client("sqs", region_name=region)
iam = boto3.client("iam")

# 1. Resolve or Create SQS Queues
print("Configuring SQS Queues...")
audit_url = sqs.create_queue(QueueName="audit-queue")["QueueUrl"]
audit_arn = sqs.get_queue_attributes(QueueUrl=audit_url, AttributeNames=["QueueArn"])["Attributes"]["QueueArn"]

deploy_url = sqs.create_queue(QueueName="deploy-queue")["QueueUrl"]
deploy_arn = sqs.get_queue_attributes(QueueUrl=deploy_url, AttributeNames=["QueueArn"])["Attributes"]["QueueArn"]

# 2. Define Fixed Trust Policy for AWS Lambda
role_name = "SNSFilteringLambdaRole"
fixed_trust_policy = {
    "Version": "2012-10-17",
    "Statement": [{
        "Effect": "Allow",
        "Principal": {"Service": "lambda.amazonaws.com"}, # FIX: Changed from sns to lambda
        "Action": "sts:AssumeRole"
    }]
}

# 3. Create or Fix Existing Role Policies
try:
    role_arn = iam.create_role(
        RoleName=role_name, 
        AssumeRolePolicyDocument=json.dumps(fixed_trust_policy)
    )["Role"]["Arn"]
    print("Created brand new IAM role.")
except iam.exceptions.EntityAlreadyExistsException:
    role_arn = iam.get_role(RoleName=role_name)["Role"]["Arn"]
    print("Role exists. Forcing trust policy correction update...")
    # This forces the existing role to accept Lambda
    iam.update_assume_role_policy(
        RoleName=role_name,
        PolicyDocument=json.dumps(fixed_trust_policy)
    )

# 4. Attach standard execution policies
iam.attach_role_policy(
    RoleName=role_name, 
    PolicyArn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
)

print("Waiting 15 seconds for global IAM trust policy updates...")
time.sleep(15)
print(f"✅ Infrastructure Live!\n -> Audit ARN: {audit_arn}\n -> Deploy ARN: {deploy_arn}")
