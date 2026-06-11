from cryptography.hazmat.primitives.serialization import load_pem_public_key
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
import base64

def local_encrypt():
    print("--- Simulating External Client Encryption (Offline) ---")
    
    # Load the exported public key file
    with open("aws-day17\\public_key.pem", "rb") as key_file:
        public_key = load_pem_public_key(key_file.read())
        
    secret_message = "Confidential ML Pipeline Data Payload"
    print(f"Original Text: {secret_message}")
    
    # Encrypt locally using RSAES_OAEP with a SHA-256 hashing digest matching AWS KMS spec
    encrypted_bytes = public_key.encrypt(
        secret_message.encode('utf-8'),
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    
    # Save the ciphertext to a file to send back to AWS
    with open("encrypted_payload.dat", "wb") as f:
        f.write(encrypted_bytes)
        
    print("🔒 Data securely encrypted offline and saved as 'encrypted_payload.dat'.")

if __name__ == "__main__":
    local_encrypt()
