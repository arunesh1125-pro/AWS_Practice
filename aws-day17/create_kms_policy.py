import boto3
import json

# Initialize KMS client for Mumbai region
kms = boto3.client('kms', region_name='ap-south-1')

# REAL AWS VALUE FROM YOUR TERMINAL
MY_ACCOUNT_ID = "859977947607"

# Define Custom KMS Key Policy mapping to your actual environment
key_policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            # Account root — must always be present or you lose access to the key
            "Sid": "Enable IAM User Permissions",
            "Effect": "Allow",
            "Principal": {"AWS": f"arn:aws:iam::{MY_ACCOUNT_ID}:root"},
            "Action": "kms:*",
            "Resource": "*"
        },
        {
            # Giving your active dev user management access explicitly
            "Sid": "AllowAruneshDevAdmin",
            "Effect": "Allow",
            "Principal": {"AWS": f"arn:aws:iam::{MY_ACCOUNT_ID}:user/arunesh-dev"},
            "Action": "kms:*",
            "Resource": "*"
        },
        {
            # ML roles (keep as placeholders or update to active roles if created)
            "Sid": "AllowMLTeamUsage",
            "Effect": "Allow",
            "Principal": {
                "AWS": [
                    f"arn:aws:iam::{MY_ACCOUNT_ID}:role/ml-engineer-role",
                    f"arn:aws:iam::{MY_ACCOUNT_ID}:role/lambda-ml-execution-role"
                ]
            },
            "Action": [
                "kms:GenerateDataKey",
                "kms:Decrypt",
                "kms:DescribeKey"
            ],
            "Resource": "*"
        },
        {
            # Security role management block
            "Sid": "AllowSecurityTeamAdminOnly",
            "Effect": "Allow",
            "Principal": {
                "AWS": f"arn:aws:iam::{MY_ACCOUNT_ID}:role/security-admin-role"
            },
            "Action": [
                "kms:Create*",
                "kms:Describe*",
                "kms:Enable*",
                "kms:List*",
                "kms:Put*",
                "kms:Update*",
                "kms:Revoke*",
                "kms:Disable*",
                "kms:Get*",
                "kms:Delete*",
                "kms:ScheduleKeyDeletion",
                "kms:CancelKeyDeletion"
            ],
            "Resource": "*"
        },
        {
            # Cross-account sharing block (e.g. Partner account 999999999999)
            "Sid": "AllowCrossAccountUsage",
            "Effect": "Allow",
            "Principal": {
                "AWS": "arn:aws:iam::999999999999:role/partner-role"
            },
            "Action": [
                "kms:GenerateDataKey",
                "kms:Decrypt"
            ],
            "Resource": "*"
        }
    ]
}

try:
    print("Creating new CMK with explicit cross-account and role policies...")
    response = kms.create_key(
        Description='ML Platform encryption key — model artifacts',
        KeyUsage='ENCRYPT_DECRYPT',
        KeySpec='SYMMETRIC_DEFAULT',   # AES-256
        Policy=json.dumps(key_policy)
    )

    key_id  = response['KeyMetadata']['KeyId']
    key_arn = response['KeyMetadata']['Arn']
    
    print(f"Key created successfully. ARN: {key_arn}")

    # Create an alias for readable reference
    print("Creating alias: alias/ml-platform-key...")
    kms.create_alias(
        AliasName='alias/ml-platform-key',
        TargetKeyId=key_id
    )

    print(f"\nSUCCESS!")
    print(f"CMK ARN: {key_arn}")
    print(f"Alias  : alias/ml-platform-key")

except kms.exceptions.MalformedPolicyDocumentException as e:
    print(f"\nError: The policy structure is invalid. {e}")
except Exception as e:
    print(f"\nAn error occurred: {e}")
