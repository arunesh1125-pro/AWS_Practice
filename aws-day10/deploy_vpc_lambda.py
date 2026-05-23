import boto3
import time

lambda_client = boto3.client('lambda', region_name='ap-south-1')

# Define your infrastructure variables
ROLE_ARN = 'arn:aws:iam::859977947607:role/arunesh-lambda-vpc-role'
FUNCTION_NAME = 'ml-inference-with-rds'

print("Reading function.zip package...")
try:
    with open('function.zip', 'rb') as f:
        zip_bytes = f.read()
except FileNotFoundError:
    print("Error: function.zip not found! Run 'Compress-Archive -Path .\\handler.py -DestinationPath .\\function.zip -Force' first.")
    exit(1)

# IAM Roles take a few seconds to propagate globally across AWS regions
print("Waiting 5 seconds for IAM role to propagate across AWS servers...")
time.sleep(5)

print(f"Creating Lambda function '{FUNCTION_NAME}' inside your VPC...")
try:
    response = lambda_client.create_function(
        FunctionName=FUNCTION_NAME,
        Runtime='python3.12',
        Role=ROLE_ARN,
        Handler='handler.lambda_handler',
        Code={'ZipFile': zip_bytes},
        VpcConfig={
            'SubnetIds': [
                'subnet-00a99bf4567354e66',
                'subnet-0339afdd93c74f795'
            ],
            'SecurityGroupIds': [
                'sg-05ce2268f3f18da09'
            ]
        },
        Timeout=30,
        MemorySize=512
    )
    print("\n🎉 SUCCESS! Your VPC Lambda Function has been created.")
    print(f"Function ARN: {response['FunctionArn']}")
    print(f"State: {response['State']}")

except Exception as e:
    print(f"\n❌ Error deploying Lambda function: {e}")
