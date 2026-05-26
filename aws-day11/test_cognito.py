import boto3
import requests
import json

# AS USER POOL CONFIGURATION
REGION = 'ap-south-1'
CLIENT_ID = '50ic6rr4ltm9dj8eudiugbpibe'
API_URL = 'https://ul6o4f6y6f.execute-api.ap-south-1.amazonaws.com/prod/users/12345'

# Intialize Cognito client
cognito_client = boto3.client('cognito-idp', region_name=REGION)

print("Authenticating user with Amazon Cognito...")

try:
    # 1. Login user to receive JWT token values
    auth_response = cognito_client.initiate_auth(
        AuthFlow='USER_PASSWORD_AUTH',
        AuthParameters={
            'USERNAME': 'arunesh1125@gmail.com',
            'PASSWORD': 'SecurePass123!'
        },
        ClientId=CLIENT_ID
    )

    # Extract the Identity Token JWT
    id_token = auth_response['AuthenticationResult']['IdToken']
    print("✅ Authentication successful! JWT Token extracted.")

    # 2. Make an authorized API call to API Gateway
    print("\nSending authorized request to secure API Gateway endpoint...")

    headers = {
        'Authorization': id_token,     # Secure Cognito Token Header
        'Content-Type': 'application/json'
    }

    body_payload = {
        'features': [0.1, 0.2, 0.3]
    }

    api_response = requests.post(
        API_URL,
        headers=headers,
        json=body_payload
    )

    print(f"✅ Status Code Received: {api_response.status_code}")
    print("Response Content:")
    print(json.dumps(api_response.json(), indent=4))

except Exception as e:
    print(f"❌ Error Occurred: {str(e)}")