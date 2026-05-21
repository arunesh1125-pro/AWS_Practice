import boto3
from botocore.exceptions import ClientError

lambda_client = boto3.client('lambda', region_name='ap-south-1')
FUNCTION_NAME = 'ml-inference-function'

# Step 1: Initialize Alias at Version 5
print("Setting 'prod' alias pointing to Version 5...")
try:
    lambda_client.create_alias(
        FunctionName=FUNCTION_NAME,
        Name='prod',
        FunctionVersion='5',
        Description='Production alias — XGBoost model v3'
    )
    print("Alias 'prod' successfully created pointing to V5.")
except ClientError as e:
    if e.response['Error']['Code'] == 'ResourceConflictException':
        lambda_client.update_alias(
            FunctionName=FUNCTION_NAME,
            Name='prod',
            FunctionVersion='5',
            Description='Production alias — XGBoost model v3'
        )
        print("Alias 'prod' updated back to V5.")
    else:
       raise

# ── Step 2: Promote Version 6 to Prod ─────────────────────────────
print("\nPromoting Version 6 to prod...")
lambda_client.update_alias(
    FunctionName=FUNCTION_NAME,
    Name='prod',
    FunctionVersion='6',
    Description='Production alias — XGBoost model v4'
)
print("Alias 'prod' successfully promoted to Version 6!")
