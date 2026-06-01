import json
import time
import boto3
from botocore.exceptions import ClientError

region = "ap-south-1"
iam = boto3.client("iam")
awslambda = boto3.client("lambda", region_name=region)
dynamodb = boto3.client("dynamodb", region_name=region)

table_name = "SensorReadings"
role_name = "LambdaDDBStreamExecutionRole"
function_name = "ProcessSensorStream"

# 1. Update Existing DynamoDB Table to Enable Streams
print(f"Enabling DynamoDB Streams on existing table '{table_name}'...")
try:
    dynamodb.update_table(
        TableName=table_name,
        StreamSpecification={
            "StreamEnabled": True,
            "StreamViewType": "NEW_AND_OLD_IMAGES",  # Captures both before & after images
        },
    )
    print("Waiting 15 seconds for AWS to provision stream resources...")
    time.sleep(15)

    # Fetch the newly generated Stream ARN
    table_desc = dynamodb.describe_table(TableName=table_name)
    stream_arn = table_desc["Table"]["LatestStreamArn"]
    print(f"Stream is active! ARN: {stream_arn}")
except ClientError as e:
    print(f"Failed to update table: {e.response['Error']['Message']}")
    exit()

# 2. Create the Lambda Execution Role
trust_policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {"Service": "://amazonaws.com"},
            "Action": "sts:AssumeRole",
        }
    ],
}

print("Configuring IAM Security Roles...")
try:
    role_arn = iam.create_role(
        RoleName=role_name, AssumeRolePolicyDocument=json.dumps(trust_policy)
    )["Role"]["Arn"]
    iam.attach_role_policy(
        RoleName=role_name,
        PolicyArn="arn:aws:iam::aws:policy/service-role/AWSLambdaDynamoDBExecutionRole",
    )
    print("Security roles generated. Waiting 10s for global sync...")
    time.sleep(10)
except iam.exceptions.EntityAlreadyExistsException:
    role_arn = iam.get_role(RoleName=role_name)["Role"]["Arn"]
    print("Using existing IAM Execution Role.")

# 3. Create Lambda Function
print("Uploading and deploying code to Lambda...")
with open("lambda_deploy.zip", "rb") as f:
    zip_bytes = f.read()

try:
    awslambda.create_function(
        FunctionName=function_name,
        Runtime="python3.12",
        Role=role_arn,
        Handler="lambda_function.lambda_handler",
        Code={"ZipFile": zip_bytes},
        Timeout=15,
    )
    print("Lambda function successfully deployed.")
except awslambda.exceptions.ResourceInUseException:
    awslambda.update_function_code(
        FunctionName=function_name, ZipFile=zip_bytes
    )
    print("Lambda code updated successfully.")

# 4. Create the Event Source Mapping Trigger
print("Wiring Table Stream directly to Lambda Trigger pipeline...")
try:
    awslambda.create_event_source_mapping(
        EventSourceArn=stream_arn,
        FunctionName=function_name,
        StartingPosition="LATEST",
        BatchSize=1,
    )
    print("Success! Your live database streaming pipeline is ready.")
except awslambda.exceptions.ResourceConflictException:
    print("Trigger configuration link already exists.")
