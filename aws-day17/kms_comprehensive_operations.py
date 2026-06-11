import boto3

# Initialize KMS client for Mumbai region
kms = boto3.client('kms', region_name='ap-south-1')

# Use your verified working key alias
KEY_ALIAS = "alias/ml-models-key"

try:
    print("==================================================")
    print(" ── 1. DIRECT ENCRYPTION (≤4 KB Payload Only) ──")
    print("==================================================")
    secret_payload = b'my-secret-api-key-1234'
    print(f"Original Secret: {secret_payload}")

    # Encrypt a small secret directly using the KMS engine
    encrypt_response = kms.encrypt(
        KeyId=KEY_ALIAS,
        Plaintext=secret_payload,
        EncryptionContext={'purpose': 'api-key-storage'}
    )
    ciphertext = encrypt_response['CiphertextBlob']
    print(f"SUCCESS: Direct Encryption complete. Ciphertext bytes: {ciphertext[:15].hex()}... [Truncated]")

    # Decrypt the small secret directly
    decrypt_response = kms.decrypt(
        CiphertextBlob=ciphertext,
        EncryptionContext={'purpose': 'api-key-storage'}
    )
    plaintext = decrypt_response['Plaintext']
    print(f"SUCCESS: Direct Decryption complete. Recovered: {plaintext}")


    print("\n==================================================")
    print(" ── 2. ENVELOPE ENCRYPTION DEK GENERATION ──")
    print("==================================================")
    
    # Generate a full plaintext data key and its encrypted package variant
    print("Generating complete standard Data Key (DEK)...")
    dek_response = kms.generate_data_key(
        KeyId=KEY_ALIAS,
        KeySpec='AES_256',
        EncryptionContext={'purpose': 'model-encryption'}
    )
    plaintext_dek = dek_response['Plaintext']
    encrypted_dek = dek_response['CiphertextBlob']
    print(f"SUCCESS: Standard DEK Ready. Plaintext Size: {len(plaintext_dek)} bytes. Ciphertext Size: {len(encrypted_dek)} bytes.")

    # Generate an encrypted data key ONLY (No plaintext sent across the wire)
    print("\nGenerating encrypted data key ONLY...")
    dek_only_response = kms.generate_data_key_without_plaintext(
        KeyId=KEY_ALIAS,
        KeySpec='AES_256'
    )
    encrypted_dek_only = dek_only_response['CiphertextBlob']
    print(f"SUCCESS: Encrypted-Only DEK Packaged. Size: {len(encrypted_dek_only)} bytes.")


    print("\n==================================================")
    print(" ── 3. KEY MANAGEMENT & METADATA DISCOVERY ──")
    print("==================================================")
    
    # Describe the tracking properties of your alias target
    print(f"Describing target alias metadata for '{KEY_ALIAS}'...")
    key_metadata = kms.describe_key(KeyId=KEY_ALIAS)
    print(f"-> Key ARN: {key_metadata['KeyMetadata']['Arn']}")
    print(f"-> Key Status: {key_metadata['KeyMetadata']['KeyState']}")

    # List all customer managed master key components in the region
    print("\nListing root KMS keys registered in ap-south-1...")
    keys_list = kms.list_keys()
    print(f"Found {len(keys_list['Keys'])} active master keys.")

    # List custom human-readable mapping pointer aliases in the region
    print("\nListing alias pointer mappings registered in ap-south-1...")
    aliases_list = kms.list_aliases()
    print(f"Found {len(aliases_list['Aliases'])} mapped resource pointers.")
    
    print("\n==================================================")
    print(" ALL SCENARIO EXECUTIONS PASSED SUCCESSFULLY")
    print("==================================================")

except kms.exceptions.NotFoundException:
    print(f"\nError: The key alias '{KEY_ALIAS}' was not found. Please verify your resource configs.")
except Exception as e:
    print(f"\nAn unexpected runtime error occurred: {e}")
