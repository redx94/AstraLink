# Data Encryption Manager for AstraLink

from cryptography.fernet import Fernet

class DataEncryptionManager:
    def __init__(self, key):
        self.key = key
        self.cipher_suite = Fernet(key)

    def encrypt_data(self, data):
        """ Encrypts data using the provided key. """
        encrypted_data = self.cipher_suite.encrypt(data.encode())
        return encrypted_data

    def decrypt_data(self, encrypted_data):
        """ Decrypts encrypted data using the provided key. """
        decrypted_data = self.cipher_suite.decrypt(encrypted_data).decode()
        return decrypted_data

# Example usage
key = Fernet.generate_key()
manager = DataEncryptionManager(key)
data = "Sample data for encryption."
encrypted_data = manager.encrypt_data(data)
print("Encrypted data: ", encrypted_data)
decrypted = manager.decrypt_data(encrypted_data)
print("Decrypted data: ", decrypted)
