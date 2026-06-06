import io
import zipfile
import boto3

region = "ap-south-1"
awslambda = boto3.client("lambda", region_name=region)
iam = boto3.client("iam")

role_arn = iam.get_role(RoleName="SNSFilteringLambdaRole")["Role"]["Arn"]
function_name = "alert-on-failure"

lambda_code = """
import json
def lambda_handler(event, context):
    for record in event.get('Records', []):
        subject = record['Sns'].get('Subject', 'No Subject')
        print(f"🚨 CRITICAL NOTIFICATION RECEIVED - {subject}")
        print(f"Payload Detail: {record['Sns']['Message']}")
    return {'statusCode': 200}
"""

zip_buffer = io.BytesIO()
with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
    zf.writestr("lambda_function.py", lambda_code)
zip_bytes = zip_buffer.getvalue()

print("Deploying Failure Monitor Core to AWS Lambda...")
try:
    lambda_arn = awslambda.create_function(
        FunctionName=function_name,
        Runtime="python3.12",
        Role=role_arn,
        Handler="lambda_function.lambda_handler",
        Code={"ZipFile": zip_bytes},
        Timeout=10
    )["FunctionArn"]
    print(f"✅ Lambda tracking live! ARN: {lambda_arn}")
except awslambda.exceptions.ResourceConflictException:
    lambda_arn = awslambda.get_function(FunctionName=function_name)["Configuration"]["FunctionArn"]
    print(f"Using existing active Lambda. ARN: {lambda_arn}")
