import boto3

lambda_client = boto3.client('lambda', region_name='ap-south-1')

# Publish current $LATEST as a new immutable version
response = lambda_client.publish_version(
    FunctionName='ml-inference-function',
    Description='Stable release with XGBoost model v3'
)

version_number = response['Version']
version_arn = response['FunctionArn']
print(f"Published version: {version_number}")
print(f"Version ARN: {version_arn}")