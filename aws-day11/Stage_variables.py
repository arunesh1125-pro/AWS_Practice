import boto3

apigw = boto3.client('apigateway')

# Create a deployment to the prod stage
apigw.create_deployment(
    restApiId='abc123def',   # replace with your API ID
    stageName='prod',
    stageDescription='Production deployment v4',
    description='Deploying XGBoost model v4 endpoints'
)

# Update a stage variable
apigw.update_stage(
    restApiId='abc123def',   # replace with your API ID
    stageName='prod',
    patchOperations=[
        {
            'op': 'replace',
            'path': '/variables/LAMBDA_ALIAS',
            'value': 'prod'
        }
    ]
)