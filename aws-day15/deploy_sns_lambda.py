import io
import json
import zipfile
import boto3
from botocore.exceptions import ClientError

region = "ap-south-1"
awslambda = boto3.client("lambda", region_name=region)
iam = boto3.client("iam")

role_arn = iam.get_role(RoleName="SNSLambdaExecutionRole")["Role"]["Arn"]
function_name = "process-model-event"

# In-memory lambda function code definition
lambda_code = """
import json
def lambda_handler(event, context):
    print("Received real-time SNS Fan-Out notification!")
    for record in event.get('Records', []):
        print(f"Payload processed via Lambda: {record['Sns']['Message']}")
    return {'statusCode': 200}
"""

zip_buffer = io.BytesIO()
with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
    zf.writestr("lambda_function.py", lambda_code)
zip_bytes = zip_buffer.getvalue()

print("Uploading deployment code package to AWS Lambda...")
try:
    lambda_arn = awslambda.create_function(
        FunctionName=function_name,
        Runtime="python3.12",
        Role=role_arn,
        Handler="lambda_function.lambda_handler",
        Code={"ZipFile": zip_bytes},
        Timeout=15
    )["FunctionArn"]
    print(f"✅ Success! Lambda function deployed. ARN: {lambda_arn}")
except awslambda.exceptions.ResourceConflictException:
    lambda_arn = awslambda.get_function(FunctionName=function_name)["Configuration"]["FunctionArn"]
    print(f"Using existing Lambda function. ARN: {lambda_arn}")
