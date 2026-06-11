import os
import boto3
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# Initialize clients using your configured region
kms = boto3.client('kms', region_name='ap-south-1')
s3  = boto3.client('s3')

# YOUR REAL AWS VALUES FROM TERMINAL
CMK_ID = 'arn:aws:kms:ap-south-1:859977947607:key/b76975f4-1366-4599-8987-0a259ee1444f'
BUCKET = 'ml-encrypted-models-yourname'

def encrypt_and_upload_model(model_bytes, model_key):
    """ Encrypts data with a unique DEK and uploads the DEK ciphertext to S3 metadata. """
    response = kms.generate_data_key(KeyId=CMK_ID, KeySpec='AES_256')
    plaintext_dek = bytearray(response['Plaintext']) 
    encrypted_dek = response['CiphertextBlob']

    try:
        iv = os.urandom(12)  # 96-bit IV
        aesgcm = AESGCM(bytes(plaintext_dek))
        encrypted_model = aesgcm.encrypt(iv, model_bytes, None)

        s3.put_object(
            Bucket=BUCKET,
            Key=model_key,
            Body=encrypted_model,
            Metadata={
                'encrypted-dek': encrypted_dek.hex(),
                'iv':            iv.hex(),
                'cmk-id':        CMK_ID,
                'encryption':    'envelope-aes256-gcm'
            }
        )
        print(f"Successfully uploaded: s3://{BUCKET}/{model_key}")

    finally:
        for i in range(len(plaintext_dek)):
            plaintext_dek[i] = 0
        del plaintext_dek

def download_and_decrypt_model(model_key):
    """ Downloads encrypted model, asks KMS to decrypt the DEK, then decrypts data. """
    response = s3.get_object(Bucket=BUCKET, Key=model_key)
    encrypted_model = response['Body'].read()
    metadata = response['Metadata']

    encrypted_dek = bytes.fromhex(metadata['encrypted-dek'])
    iv = bytes.fromhex(metadata['iv'])

    try:
        decrypt_response = kms.decrypt(KeyId=CMK_ID, CiphertextBlob=encrypted_dek)
        plaintext_dek = bytearray(decrypt_response['Plaintext'])
    except kms.exceptions.AccessDeniedException:
        print("Access denied — AWS Caller lacks kms:Decrypt permissions")
        raise

    try:
        aesgcm = AESGCM(bytes(plaintext_dek))
        model_bytes = aesgcm.decrypt(iv, encrypted_model, None)
        return model_bytes
        
    finally:
        for i in range(len(plaintext_dek)):
            plaintext_dek[i] = 0
        del plaintext_dek

# TEST EXECUTION
if __name__ == "__main__":
    print("\n=== STARTING ENVELOPE ENCRYPTION TEST ===")
    
    # 1. Define dummy model data
    fake_model_data = b"Model-Weights-v1.0-Data-Stream-Payload-XYZ"
    target_s3_key = "models/secure_v1_model.bin"
    
    # 2. Test Encryption and Upload
    print("\n[1/3] Encrypting and uploading model payload...")
    encrypt_and_upload_model(fake_model_data, target_s3_key)
    
    # 3. Test Download and Decryption
    print("\n[2/3] Downloading and decrypting from S3...")
    decrypted_output = download_and_decrypt_model(target_s3_key)
    
    # 4. Verify Integrity
    print("\n[3/3] Verifying data integrity...")
    print(f"Original Data:  {fake_model_data}")
    print(f"Decrypted Data: {decrypted_output}")
    
    assert fake_model_data == decrypted_output, "Integrity Check Failed!"
    print("\nSUCCESS: Envelope Encryption lifecycle completed with zero leakage.")
