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


def urlsafe_base64(input_string: str) -> str:
    input_bytes = input_string.encode("utf-8")
    base64_bytes = base64.urlsafe_b64encode(input_bytes)
    base64_string = base64_bytes.decode("utf-8")
    return base64_string


def urlsafe_base64_decode(base64_string: str) -> str:
    padding = '=' * (-len(base64_string) % 4)
    base64_string_padded = base64_string + padding
    base64_bytes = base64_string_padded.encode("utf-8")
    decoded_bytes = base64.urlsafe_b64decode(base64_bytes)
    return decoded_bytes.decode("utf-8")
