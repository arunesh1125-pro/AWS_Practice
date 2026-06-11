import boto3

kms_client = boto3.client('kms', region_name='ap-south-1')
# 👈 Replace with your real KMS Key ARN
KEY_ID = "arn:aws:kms:ap-south-1:859977947607:key/ffc8ff91-0de1-4844-9700-7fdfb1f3ec0f" 

def decrypt_payload_via_kms():
    print("--- Processing Received Ciphertext via AWS KMS ---")
    
    # Read the encrypted bytes file sent by the external client
    with open("encrypted_payload.dat", "rb") as f:
        ciphertext_blob = f.read()
        
    # Ask KMS to decrypt using its internal hidden private key
    response = kms_client.decrypt(
        KeyId=KEY_ID,
        CiphertextBlob=ciphertext_blob,
        EncryptionAlgorithm='RSAES_OAEP_SHA_256' # Must match exact algorithm encryption spec
    )
    
    decrypted_plaintext = response['Plaintext'].decode('utf-8')
    print(f"🔓 Decryption Successful! Clean Plaintext: '{decrypted_plaintext}'")

if __name__ == "__main__":
    decrypt_payload_via_kms()
