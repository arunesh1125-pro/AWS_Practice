import boto3
import time

lambda_client = boto3.client('lambda', region_name='ap-south-1')
FUNCTION_NAME = 'ml-inference-function'

print("Generating distinct versions up to Version 6...")

for i in range(1, 7):
    print(f"Modifying configuration to prepare Version {i}...")
    # Update an environment variable to force a configuration change
    lambda_client.update_function_configuration(
        FunctionName=FUNCTION_NAME,
        Environment={
            'Variables': {
                'VERSION_BUILD': str(i),
                'MODEL_NAME': f'xgboost_v{i}'
            }
        }
    )

    # Wait a moment for AWS to update the configuration active state
    time.sleep(2)

    # Publish the unique state as a new version
    res = lambda_client.publish_version(
        FunctionName=FUNCTION_NAME,
        Description=f"Stable release version {i}"
    )
    print(f"--> Successfully minted Version: {res['Version']}")

print("All 6 versions are now live in your AWS account!")
