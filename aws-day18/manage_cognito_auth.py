import boto3
import json
import urllib.request
from jose import jwt as jose_jwt

# Initialize Cognito Client
cognito_idp = boto3.client('cognito-idp', region_name='ap-south-1')

# CRITICAL: Replace these with your real IDs from Step 1
USER_POOL_ID = 'ap-south-1_nZlIt8tqo'
CLIENT_ID    = '5afv1vumh632q9bgeqjto3lebn'

TEST_EMAIL    = 'ml_engineer_test@example.com'
TEMP_PASSWORD = 'TempP@ssword123!'
PERM_PASSWORD = 'SecureM1_Auth99!'

# ── 1. Admin operations (server-side) ────────────────────────────────
def create_user(email, temp_password):
    print(f"Creating user profile for: {email}...")
    response = cognito_idp.admin_create_user(
        UserPoolId=USER_POOL_ID,
        Username=email,
        TemporaryPassword=temp_password,
        UserAttributes=[
            {'Name': 'email',          'Value': email},
            {'Name': 'email_verified', 'Value': 'true'},
            {'Name': 'custom:role',    'Value': 'ml-engineer'}
        ],
        MessageAction='SUPPRESS'
    )
    print("SUCCESS: User profile built.")
    return response['User']

def add_user_to_group(username, group_name):
    print(f"Assigning user '{username}' to security group: {group_name}...")
    cognito_idp.admin_add_user_to_group(
        UserPoolId=USER_POOL_ID,
        Username=username,
        GroupName=group_name
    )
    print("SUCCESS: Security group attached.")

# ── 2. Authentication flows ──────────────────────────────────────────
def authenticate_user(username, password):
    print(f"Attempting standard USER_PASSWORD_AUTH login for {username}...")
    try:
        response = cognito_idp.initiate_auth(
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={'USERNAME': username, 'PASSWORD': password},
            ClientId=CLIENT_ID
        )
        
        # Handle force change password condition if returned by Cognito
        if 'ChallengeName' in response and response['ChallengeName'] == 'NEW_PASSWORD_REQUIRED':
            print("-> [Challenge] First login detected. Establishing permanent password password...")
            challenge_response = cognito_idp.admin_respond_to_auth_challenge(
                UserPoolId=USER_POOL_ID,
                ClientId=CLIENT_ID,
                ChallengeName='NEW_PASSWORD_REQUIRED',
                ChallengeResponses={
                    'USERNAME': username,
                    'NEW_PASSWORD': PERM_PASSWORD
                },
                Session=response['Session']
            )
            auth_result = challenge_response['AuthenticationResult']
        else:
            auth_result = response['AuthenticationResult']

        print("SUCCESS: Token payload acquired.")
        return {
            'idToken':      auth_result['IdToken'],
            'accessToken':  auth_result['AccessToken'],
            'refreshToken': auth_result['RefreshToken']
        }
    except Exception as e:
        print(f"Authentication Failed: {e}")
        return None

# ── 3. Token Parsing and Validation ─────────────────────────────────
def decode_and_validate_jwt(token):
    print("\nDownloading Cognito public JSON Web Key Sets (JWKS) for verification...")
    keys_url = f"https://cognito-idp.ap-south-1.amazonaws.com/{USER_POOL_ID}/.well-known/jwks.json"
    with urllib.request.urlopen(keys_url) as response:
        keys = json.loads(response.read())['keys']

    try:
        print("Validating RS256 signature, expiration state, and client audience claims...")
        claims = jose_jwt.decode(token, keys, algorithms=['RS256'], audience=CLIENT_ID)
        print("SUCCESS: Token signature is completely valid.")
        return claims
    except Exception as e:
        print(f"Invalid token: {e}")
        return None

# ── Execution Harness ─────────────────────────────────────────────────
if __name__ == "__main__":
    print("==================================================")
    print(" AWS COGNITO IDENTITY FLOW HARNESS")
    print("==================================================")
    
    try:
        # Step A: Provision User
        create_user(TEST_EMAIL, TEMP_PASSWORD)
        add_user_to_group(TEST_EMAIL, "ml-engineers")
        
        # Step B: Log in and clear the password reset challenge
        tokens = authenticate_user(TEST_EMAIL, TEMP_PASSWORD)
        
        if tokens:
            print(f"\nAccess Token acquired: {tokens['accessToken'][:25]}... [Truncated]")
            
            # Step C: Verify the integrity of the generated identity token
            claims = decode_and_validate_jwt(tokens['idToken'])
            if claims:
                print(f"\nDecoded Identity Token Claims:")
                print(f"  * Issuer:       {claims['iss']}")
                print(f"  * User Email:   {claims['email']}")
                print(f"  * Custom Role:  {claims['custom:role']}")
                
    except Exception as general_err:
        print(f"\nExecution Aborted: {general_err}")
