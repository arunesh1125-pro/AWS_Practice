import boto3

# Initialize KMS client for Mumbai region
kms = boto3.client('kms', region_name='ap-south-1')

# Use your verified working key alias
KEY_ALIAS = "alias/ml-models-key"

# Define the strict cryptographically bound metadata (Encryption Context)
production_context = {
    'Purpose':     'ml-model-encryption',
    'ModelId':     'xgboost-v5',
    'Environment': 'production',
    'TeamId':      'ml-platform'
}

try:
    print(f"--- Step 1: Generating Data Key bound to Production Context ---")
    response = kms.generate_data_key(
        KeyId=KEY_ALIAS,
        KeySpec='AES_256',
        EncryptionContext=production_context
    )
    encrypted_dek = response['CiphertextBlob']
    plaintext_dek = response['Plaintext']
    print("SUCCESS: Data Key generated and cryptographically bound to metadata.")

    print(f"\n--- Step 2: Attempting Decryption with the CORRECT Context ---")
    decrypt_response = kms.decrypt(
        CiphertextBlob=encrypted_dek,
        EncryptionContext=production_context
    )
    print("SUCCESS: Decryption verified! Data key extracted successfully because context matched.")

    print(f"\n--- Step 3: Attempting Decryption with an INCORRECT Context (Tamper Test) ---")
    tampered_context = production_context.copy()
    tampered_context['Environment'] = 'development'  # Changing a single variable

    try:
        invalid_response = kms.decrypt(
            CiphertextBlob=encrypted_dek,
            EncryptionContext=tampered_context
        )
        print("WARNING: This shouldn't happen. Decryption succeeded with wrong context!")
    except kms.exceptions.InvalidCiphertextException:
        print("SUCCESS: Security check passed! KMS rejected the decryption because the context did not match.")

    # 4. Reference Policy Structure Explanation
    print("\n--- Encryption Context IAM/Key Policy Note ---")
    print("To restrict an IAM role to only production objects, apply this condition logic:")
    print(
        """
        "Condition": {
            "StringEquals": {
                "kms:EncryptionContext:Environment": "production"
            }
        }
        """
    )

except kms.exceptions.NotFoundException:
    print(f"\nError: The key alias '{KEY_ALIAS}' was not found. Please verify it exists.")
except Exception as e:
    print(f"\nAn unexpected error occurred: {e}")
