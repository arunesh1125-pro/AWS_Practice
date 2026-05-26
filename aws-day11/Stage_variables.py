import boto3

apigw = boto3.client('apigateway')


# YOUR REAL API ID FROM AWS
TARGET_API_ID = 'ul6o4f6y6f'  # <--- Change this to your actual API ID

print("Starting API Gateway deployment automation...")

try:
    # Create a deployment to the prod stage
    deployment_response = apigw.create_deployment(
        restApiId=TARGET_API_ID,
        stageName='prod',
        stageDescription='Production deployment v4',
        description='Deploying XGBoost model v4 endpoints'
    )
    print(f"✅ Successfully deployed API! Deployment ID: {deployment_response['id']}")

    # Update a stage variable named LAMBDA_ALIAS
    apigw.update_stage(
        restApiId=TARGET_API_ID,   # replace with your API ID
        stageName='prod',
        patchOperations=[
            {
                'op': 'replace',
                'path': '/variables/LAMBDA_ALIAS',
                'value': 'prod'
            }
        ]
    )
    print("✅ Successfully updated stage variable 'LAMBDA_ALIAS' to 'prod'!")

except Exception as e:
    print(f"❌ Error occurred: {str(e)}")