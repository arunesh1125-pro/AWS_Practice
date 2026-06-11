import boto3

# Initialize KMS and STS clients
kms = boto3.client('kms', region_name='ap-south-1')
sts = boto3.client('sts')

# UPDATED: Using your existing working alias from your earlier terminal steps
KEY_ALIAS = "alias/ml-models-key"

try:
    # 1. Look up the real Key ARN because grants do not accept aliases
    print(f"Resolving alias '{KEY_ALIAS}' to real Key ARN...")
    key_info = kms.describe_key(KeyId=KEY_ALIAS)
    REAL_KEY_ARN = key_info['KeyMetadata']['Arn']
    print(f"Resolved to: {REAL_KEY_ARN}")

    # 2. Dynamically fetch your exact authenticated identity string
    print("\nFetching active caller identity from AWS STS...")
    caller_identity = sts.get_caller_identity()
    GRANTEE_PRINCIPAL = caller_identity['Arn']
    
    print(f"Creating a programmatic KMS grant for: {GRANTEE_PRINCIPAL}...")
    
    # Step 3: Create the Grant using the REAL_KEY_ARN
    response = kms.create_grant(
        KeyId=REAL_KEY_ARN,
        GranteePrincipal=GRANTEE_PRINCIPAL,
        Operations=[
            'GenerateDataKey',
            'Decrypt'
        ],
        Name='training-job-grant'
    )

    grant_id    = response['GrantId']
    grant_token = response['GrantToken']
    
    print("\nSUCCESS: Grant Created!")
    print(f"Grant ID:    {grant_id}")
    print(f"Grant Token: {grant_token[:30]}... [Truncated]")

    # Step 4: Clean up by revoking the grant using the REAL_KEY_ARN
    print(f"\nRevoking the grant {grant_id}...")
    kms.revoke_grant(
        KeyId=REAL_KEY_ARN,
        GrantId=grant_id
    )
    print("SUCCESS: Grant successfully revoked.")

except kms.exceptions.NotFoundException:
    print(f"\nError: The key alias '{KEY_ALIAS}' was not found. Please verify it exists.")
except Exception as e:
    print(f"\nAn error occurred: {e}")
