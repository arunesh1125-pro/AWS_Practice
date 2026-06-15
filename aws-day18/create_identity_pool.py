import boto3

# Initialize Cognito Identity Client
client = boto3.client('cognito-identity', region_name='ap-south-1')

try:
    print("Executing native Boto3 API call to create Identity Pool...")
    response = client.create_identity_pool(
        IdentityPoolName='MLIdentityPoolFinal',
        AllowUnauthenticatedIdentities=False,
        CognitoIdentityProviders=[
            {
                # THIS IS THE EXACT PATH ENFORCED BY AWS
                'ProviderName': '://amazonaws.com',
                'ClientId': '5afv1vumh632q9bgeqjto3lebn',
                'ServerSideTokenCheck': False
            }
        ]
    )
    print("\n==================================================")
    print("SUCCESS: IDENTITY POOL CREATED")
    print("==================================================")
    print(f"Your Identity Pool ID is: {response['IdentityPoolId']}")
    print("==================================================")

except Exception as e:
    print(f"API Error Occurred: {e}")
