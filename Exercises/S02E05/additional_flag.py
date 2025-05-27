import base64
from itertools import cycle

cipher_b64 = "GhUiPj1fKTM3NCY1KSUmNxkP"
key = b"andrzej"

# 1. Base-64
cipher_bytes = base64.b64decode(cipher_b64)

# 2. Repeating XOR
plain = bytes(c ^ k for c, k in zip(cipher_bytes, cycle(key)))

print(plain.decode())