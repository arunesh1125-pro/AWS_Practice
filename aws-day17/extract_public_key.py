import boto3
import base64

kms_client = boto3.client('kms', region_name='ap-south-1')
# 👈 Replace with your real KMS Key ARN generated in Step 1
KEY_ID = "arn:aws:kms:ap-south-1:859977947607:key/ffc8ff91-0de1-4844-9700-7fdfb1f3ec0f" 

def export_public_key():
    print("--- Fetching Public Key from AWS KMS ---")
    
    response = kms_client.get_public_key(KeyId=KEY_ID)
    public_key_der = response['PublicKey']  # Raw DER-encoded public key bytes
    
    # Standard practice: Encode to Base64 PEM-style format for external transmission
    b64_encoded = base64.b64encode(public_key_der).decode('utf-8')
    
    # Save the key locally as a file to simulate handing it to an external vendor
    with open("public_key.pem", "w") as f:
        f.write(f"-----BEGIN PUBLIC KEY-----\n{b64_encoded}\n-----END PUBLIC KEY-----")
        
    print("✅ Public key extracted and saved locally as 'public_key.pem'!")

if __name__ == "__main__":
    export_public_key()
