import boto3

apigw = boto3.client('apigateway', region_name = 'ap-south-1')

# YOUR REAL VARIABLES
TARGET_API_ID = 'ul6o4f6y6f'  # replace with your API ID
COGNITO_POOL_ARN = 'arn:aws:cognito-idp:ap-south-1:859977947607:userpool/ap-south-1_mQ4AGy6cI'

print("Creating automated Cognito User Pool Authorizer...")

try:
    # Create the Cognito authorizer on your REST API
    response = apigw.create_authorizer(
        restApiId=TARGET_API_ID,
        name='CognitoDeepDiveAuthorizer',
        type='COGNITO_USER_POOLS',
        providerARNs=[COGNITO_POOL_ARN],
        identitySource='method.request.header.Authorization',
        authorizerResultTtlInSeconds=300 # Cache validation results for 5 minutes
    )

    print(f"✅ Authorizer created successfully!")
    print(f"Authorizer ID: {response['id']}")
    print("\nNext step: Remember to go to API Gateway, attach 'CognitoDeepDiveAuthorizer' to your POST method, and deploy the 'prod' stage live!")

except Exception as e:
    print(f"❌ Automation failed: {str(e)}")