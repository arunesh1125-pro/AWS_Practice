import boto3
import time

lambda_client = boto3.client('lambda', region_name='ap-south-1')
function_name = 'ml-inference-function'

print("Generating versions up to Version 6...")
# Loop 5 times to create versions 2, 3, 4, 5, and 6
for i in range(1, 7):
    try:
        print(f"Publishing Version {i}...")
        res=lambda_client.publish_version(
            FunctionName=function_name,
            Description=f"Auto-generated version {i}"
        )
        print(f"Successfully published Version: {res['Version']}")
        time.sleep(1)  # Short pause to prevent AWS rate limits
    except Exception as e:
        print(f"Error publishing version {i}: {e}")

print("All versions created successfully!")
