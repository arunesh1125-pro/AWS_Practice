import boto3

# Initialize KMS client for Mumbai region
kms = boto3.client('kms', region_name='ap-south-1')

# Use your verified working key alias
TARGET_ALIAS = "alias/ml-models-key"

try:
    # 1. Resolve alias to the true Key ARN (rotation APIs require Key ID or Key ARN)
    print(f"Resolving alias '{TARGET_ALIAS}' to real Key ARN...")
    key_info = kms.describe_key(KeyId=TARGET_ALIAS)
    REAL_KEY_ARN = key_info['KeyMetadata']['Arn']
    print(f"Resolved to: {REAL_KEY_ARN}\n")

    # 2. Enable Automatic Annual Rotation
    print(f"Enabling automatic annual rotation on key...")
    kms.enable_key_rotation(KeyId=REAL_KEY_ARN)
    print("SUCCESS: Automatic rotation configuration updated.")

    # 3. Verify Rotation Status
    print("Checking current key rotation status...")
    status_response = kms.get_key_rotation_status(KeyId=REAL_KEY_ARN)
    print(f"-> Rotation enabled status: {status_response['KeyRotationEnabled']}\n")


    # 4. Manual Rotation Demonstration Pattern
    def demonstrate_manual_key_rotation(alias_name, description):
        print(f"--- Starting Manual Rotation for '{alias_name}' ---")
        
        # Step A: Spin up a completely fresh CMK backing backing key
        print("Creating brand new CMK backing key...")
        new_key = kms.create_key(
            Description=description + ' (manually rotated)',
            KeyUsage='ENCRYPT_DECRYPT',
            KeySpec='SYMMETRIC_DEFAULT'
        )
        new_key_id = new_key['KeyMetadata']['KeyId']
        new_key_arn = new_key['KeyMetadata']['Arn']
        print(f"New Key Created: {new_key_arn}")

        # Step B: Point the existing alias to the fresh backing key
        print(f"Updating alias '{alias_name}' to target the new key...")
        kms.update_alias(
            AliasName=alias_name,
            TargetKeyId=new_key_id
        )

        print(f"SUCCESS: Alias '{alias_name}' now routes traffic to new key ID: {new_key_id}")
        print("CRITICAL: Old key is preserved automatically. It will still be used to decrypt old data.")
        return new_key_id

    # Execute the manual rotation pattern
    demonstrate_manual_key_rotation(TARGET_ALIAS, "ML Platform Key")

except kms.exceptions.NotFoundException:
    print(f"\nError: The key alias '{TARGET_ALIAS}' was not found. Please verify it exists.")
except Exception as e:
    print(f"\nAn error occurred: {e}")
