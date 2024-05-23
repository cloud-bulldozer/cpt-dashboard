import zlib
import hashlib
from cryptography.fernet import Fernet

symmetric_encryptor = b'k3tGwuK6O59c0SEMmnIeJUEpTN5kuxibPy8Q8VfYC6A='

def hash_encrypt_json(json_data):
    # Serialize the JSON data to a string
    json_str = str(json_data)
    
    # Generate an MD5 hash of the JSON string
    hash_digest = hashlib.md5(json_str.encode()).hexdigest()
    
    # Compress the JSON string
    compressed_data = zlib.compress(json_str.encode())
    
    cipher = Fernet(symmetric_encryptor)
    
    # Encrypt the compressed JSON string
    encrypted_data = cipher.encrypt(compressed_data)
    
    return hash_digest, encrypted_data

def decrypt_unhash_json(hash_digest, encrypted_data):
    cipher = Fernet(symmetric_encryptor)
    
    # Decrypt the encrypted JSON data
    decompressed_data = cipher.decrypt(encrypted_data)
    
    # Decompress the decrypted data
    decompressed_json_str = zlib.decompress(decompressed_data).decode()
    
    # Verify hash digest
    calculated_hash = hashlib.md5(decompressed_json_str.encode()).hexdigest()
    if calculated_hash != hash_digest:
        raise ValueError("Hash digest does not match")
    
    # Deserialize the JSON string back to JSON data
    json_data = eval(decompressed_json_str)
    
    return json_data
