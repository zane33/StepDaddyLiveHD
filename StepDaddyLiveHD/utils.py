import os
import base64

key_bytes = os.urandom(64)


def encrypt(input_string: str):
    input_bytes = input_string.encode()
    result = xor(input_bytes)
    return base64.urlsafe_b64encode(result).decode().rstrip('=')


def decrypt(input_string: str):
    padding_needed = 4 - (len(input_string) % 4)
    if padding_needed:
        input_string += '=' * padding_needed
    input_bytes = base64.urlsafe_b64decode(input_string)
    result = xor(input_bytes)
    return result.decode()


def xor(input_bytes):
    return bytes([input_bytes[i] ^ key_bytes[i % len(key_bytes)] for i in range(len(input_bytes))])
