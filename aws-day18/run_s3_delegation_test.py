import boto3
import json
import os

# Configuration variables
IDENTITY_POOL_ID = 'ap-south-1:be44c608-8c7e-4443-b577-fda5c50849d6'
S3_BUCKET_NAME   = 'ml-platform-models-auth1'

USER_POOL_ID     = 'ap-south-1_nZlIt8tqo'
CLIENT_ID        = '5afv1vumh632q9bgeqjto3lebn'
TEST_EMAIL       = 'ml_engineer_test@example.com'
PERM_PASSWORD    = 'SecureM1_Auth99!'
LOCAL_FILE       = r'D:\AWS\aws-day18\model.bin'
S3_OBJECT_KEY    = 'models/deployed_model.bin'

cognito_idp      = boto3.client('cognito-idp', region_name='ap-south-1')
cognito_identity = boto3.client('cognito-identity', region_name='ap-south-1')

def create_local_dummy_file():
    """Ensures the directory exists and creates a dummy binary file for testing."""
    os.makedirs(os.path.dirname(LOCAL_FILE), exist_ok=True)
    print(f"Creating mock local file at: {LOCAL_FILE}")
    with open(LOCAL_FILE, "wb") as f:
        f.write(b"Mock Model Weights Data Parameters v1.0.0")

def run_pipeline():
    # Fix the missing file issue first
    create_local_dummy_file()

    # 1. Fetch User Token
    print("\n[1/4] Signing user in to User Pool context...")
    auth_resp = cognito_idp.initiate_auth(
        AuthFlow='USER_PASSWORD_AUTH',
        AuthParameters={'USERNAME': TEST_EMAIL, 'PASSWORD': PERM_PASSWORD},
        ClientId=CLIENT_ID
    )
    id_token = auth_resp['AuthenticationResult']['IdToken']
    provider_key = f'cognito-idp.ap-south-1.amazonaws.com/{USER_POOL_ID}'

    # 2. Exchange for Identity ID
    print("[2/4] Resolving identity pool registration context ID...")
    id_resp = cognito_identity.get_id(
        IdentityPoolId=IDENTITY_POOL_ID,
        Logins={provider_key: id_token}
    )
    identity_id = id_resp['IdentityId']

    # 3. Get temporary AWS credentials
    print("[3/4] Requesting temporary federated AWS access tokens...")
    creds_resp = cognito_identity.get_credentials_for_identity(
        IdentityId=identity_id,
        Logins={provider_key: id_token}
    )
    creds = creds_resp['Credentials']

    # 4. Initialize direct S3 Client session
    print("[4/4] Executing serverless S3 file upload using federated keys...")
    s3_delegated_client = boto3.client(
        's3',
        aws_access_key_id=creds['AccessKeyId'],
        aws_secret_access_key=creds['SecretKey'],
        aws_session_token=creds['SessionToken'],
        region_name='ap-south-1'
    )
    
    s3_delegated_client.upload_file(LOCAL_FILE, S3_BUCKET_NAME, S3_OBJECT_KEY)
    print(f"\nSUCCESS: File uploaded directly to s3://{S3_BUCKET_NAME}/{S3_OBJECT_KEY}")

if __name__ == "__main__":
    run_pipeline()
