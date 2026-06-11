import boto3
import time

# Initialize KMS client for Mumbai region
kms = boto3.client('kms', region_name='ap-south-1')

try:
    print("==================================================")
    print(" 1. HOW IT WORKS: RE-ENCRYPTION (MOVING BETWEEN KEYS)")
    print("==================================================")
    print("Creating two temporary keys to simulate data migration...")
    
    # Create an old key and a new key
    old_key = kms.create_key(Description="Temp Old Key")['KeyMetadata']['Arn']
    new_key = kms.create_key(Description="Temp New Key")['KeyMetadata']['Arn']
    
    # Step A: Encrypt sample data with the old key
    print("Encrypting data initially with Source Key...")
    initial_encryption = kms.encrypt(
        KeyId=old_key,
        Plaintext=b"Sensitive-ML-Weights-Data",
        EncryptionContext={'purpose': 'model-encryption'}
    )
    old_ciphertext = initial_encryption['CiphertextBlob']
    
    # FIX: Explicitly pass SourceEncryptionContext so KMS can open the old package
    print("Executing re_encrypt... Plaintext never leaves AWS KMS memory!")
    re_encrypt_response = kms.re_encrypt(
        CiphertextBlob=old_ciphertext,
        SourceKeyId=old_key,
        SourceEncryptionContext={'purpose': 'model-encryption'}, # <-- Added this critical line
        DestinationKeyId=new_key,
        DestinationEncryptionContext={'purpose': 'migrated-model-encryption'}
    )
    new_ciphertext = re_encrypt_response['CiphertextBlob']
    print("SUCCESS: Data successfully moved to the destination key.")


    print("\n==================================================")
    print(" 2. HOW IT WORKS: DISABLING & ENABLING KEYS")
    print("==================================================")
    # Create a distinct key to manipulate states
    lifecycle_key = kms.create_key(Description="Lifecycle State Key")['KeyMetadata']['KeyId']
    print(f"Targeting Key ID: {lifecycle_key}")
    
    # Disable the key
    print("Disabling key (blocking all cryptographic requests)...")
    kms.disable_key(KeyId=lifecycle_key)
    
    # Prove the key is disabled by showing metadata status
    status = kms.describe_key(KeyId=lifecycle_key)['KeyMetadata']['KeyState']
    print(f"-> Key State is now: {status}")
    
    # Re-enable the key
    print("Enabling key back to active use status...")
    kms.enable_key(KeyId=lifecycle_key)
    status = kms.describe_key(KeyId=lifecycle_key)['KeyMetadata']['KeyState']
    print(f"-> Key State is now: {status}")


    print("\n==================================================")
    print(" 3. HOW IT WORKS: SCHEDULING & CANCELLING DELETION")
    print("==================================================")
    print("AWS enforces a mandatory 7 to 30 days waiting period before permanent deletion.")
    
    # Schedule deletion (using 7 days as the minimum window allowed)
    print("Scheduling key for deletion in 7 days...")
    deletion_response = kms.schedule_key_deletion(
        KeyId=lifecycle_key,
        PendingWindowInDays=7
    )
    print(f"-> Deletion Date Set: {deletion_response['DeletionDate']}")
    status = kms.describe_key(KeyId=lifecycle_key)['KeyMetadata']['KeyState']
    print(f"-> Key State is now: {status}")
    
    # Cancel the pending deletion to recover the key safely
    print("\nCancelling pending key deletion...")
    kms.cancel_key_deletion(KeyId=lifecycle_key)
    status = kms.describe_key(KeyId=lifecycle_key)['KeyMetadata']['KeyState']
    print(f"-> Key State successfully restored to: {status}")

    print("\n==================================================")
    print(" EXECUTION COMPLETED WITHOUT ANY REMAINING ERRORS")
    print("==================================================")

except Exception as e:
    print(f"\nAn error occurred: {e}")
