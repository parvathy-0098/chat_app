import os
import base64
import hashlib
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from Crypto.Random import get_random_bytes
import logging

class CryptoUtils:
    """Utility class for cryptographic operations"""
    
    def __init__(self):
        self.key_size = 2048
    
    def generate_key_pair(self):
        """Generate RSA public/private key pair"""
        try:
            key = RSA.generate(self.key_size)
            private_key = key.export_key().decode('utf-8')
            public_key = key.publickey().export_key().decode('utf-8')
            return public_key, private_key
        except Exception as e:
            logging.error(f"Key generation error: {str(e)}")
            raise Exception("Failed to generate RSA key pair")
    
    def encrypt_message(self, message, public_key_pem):
        """Encrypt message using RSA public key"""
        try:
            # Import public key
            public_key = RSA.import_key(public_key_pem.encode('utf-8'))
            cipher = PKCS1_OAEP.new(public_key)
            
            # RSA can only encrypt small messages, so we'll split long messages
            message_bytes = message.encode('utf-8')
            max_chunk_size = (self.key_size // 8) - 42  # PKCS1_OAEP overhead
            
            if len(message_bytes) <= max_chunk_size:
                # Single chunk
                encrypted_data = cipher.encrypt(message_bytes)
                return base64.b64encode(encrypted_data).decode('utf-8')
            else:
                # Multiple chunks
                chunks = []
                for i in range(0, len(message_bytes), max_chunk_size):
                    chunk = message_bytes[i:i + max_chunk_size]
                    encrypted_chunk = cipher.encrypt(chunk)
                    chunks.append(base64.b64encode(encrypted_chunk).decode('utf-8'))
                return '|'.join(chunks)
                
        except Exception as e:
            logging.error(f"Encryption error: {str(e)}")
            raise Exception("Failed to encrypt message")
    
    def decrypt_message(self, encrypted_message, private_key_pem):
        """Decrypt message using RSA private key"""
        try:
            # Import private key
            private_key = RSA.import_key(private_key_pem.encode('utf-8'))
            cipher = PKCS1_OAEP.new(private_key)
            
            # Check if message is chunked
            if '|' in encrypted_message:
                # Multiple chunks
                chunks = encrypted_message.split('|')
                decrypted_chunks = []
                for chunk in chunks:
                    encrypted_data = base64.b64decode(chunk.encode('utf-8'))
                    decrypted_chunk = cipher.decrypt(encrypted_data)
                    decrypted_chunks.append(decrypted_chunk)
                return b''.join(decrypted_chunks).decode('utf-8')
            else:
                # Single chunk
                encrypted_data = base64.b64decode(encrypted_message.encode('utf-8'))
                decrypted_data = cipher.decrypt(encrypted_data)
                return decrypted_data.decode('utf-8')
                
        except Exception as e:
            logging.error(f"Decryption error: {str(e)}")
            raise Exception("Failed to decrypt message")
    
    def hash_password(self, password):
        """Hash password using SHA256"""
        salt = get_random_bytes(32)
        password_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
        return base64.b64encode(salt + password_hash).decode('utf-8')
    
    def verify_password(self, password, hashed_password):
        """Verify password against hash"""
        try:
            decoded_hash = base64.b64decode(hashed_password.encode('utf-8'))
            salt = decoded_hash[:32]
            stored_hash = decoded_hash[32:]
            
            password_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
            return password_hash == stored_hash
        except Exception as e:
            logging.error(f"Password verification error: {str(e)}")
            return False
    
    def generate_random_token(self, length=32):
        """Generate random token for verification codes"""
        return base64.urlsafe_b64encode(get_random_bytes(length)).decode('utf-8')[:length]