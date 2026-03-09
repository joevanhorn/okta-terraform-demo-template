#!/usr/bin/env python3
"""
Convert RSA public key PEM to JWKS JSON.

Used by Terraform external data source to compute JWKS from tls_private_key.

Input (JSON on stdin):
  {"public_key_pem": "-----BEGIN PUBLIC KEY-----\n...", "key_id": "my-key-id"}

Output (JSON on stdout):
  {"jwks_json": "{\"keys\":[...]}"}
"""

import sys
import json
import base64

from cryptography.hazmat.primitives.serialization import load_pem_public_key


def int_to_base64url(n, length=None):
    byte_length = length or (n.bit_length() + 7) // 8
    n_bytes = n.to_bytes(byte_length, byteorder="big")
    return base64.urlsafe_b64encode(n_bytes).rstrip(b"=").decode("ascii")


def main():
    input_data = json.load(sys.stdin)
    pem = input_data["public_key_pem"].encode()
    key_id = input_data["key_id"]

    public_key = load_pem_public_key(pem)
    numbers = public_key.public_numbers()

    jwks = {
        "keys": [
            {
                "kty": "RSA",
                "use": "sig",
                "alg": "RS256",
                "kid": key_id,
                "n": int_to_base64url(numbers.n, 256),
                "e": int_to_base64url(numbers.e),
            }
        ]
    }

    output = {"jwks_json": json.dumps(jwks)}
    json.dump(output, sys.stdout)


if __name__ == "__main__":
    main()
