"""AES-256-GCM encryption per il vault password.

- Chiave master letta da VAULT_MASTER_KEY (base64, 32 byte).
- Per ogni record viene generato un nonce univoco di 12 byte.
- Output: base64(nonce || ciphertext+tag).
"""

import base64
import os
from typing import Final

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

_NONCE_BYTES: Final[int] = 12
_KEY_BYTES: Final[int] = 32


class EncryptionError(Exception):
    pass


def _load_master_key() -> bytes:
    raw = os.getenv("VAULT_MASTER_KEY")
    if not raw:
        raise EncryptionError(
            "VAULT_MASTER_KEY mancante nell'environment. "
            "Generala con: python -c \"import os,base64; print(base64.b64encode(os.urandom(32)).decode())\""
        )
    try:
        key = base64.b64decode(raw, validate=True)
    except Exception:
        key = raw.encode("utf-8")

    if len(key) != _KEY_BYTES:
        raise EncryptionError(
            f"VAULT_MASTER_KEY deve corrispondere a {_KEY_BYTES} byte (attualmente {len(key)})."
        )
    return key


_aesgcm: AESGCM | None = None


def _get_cipher() -> AESGCM:
    global _aesgcm
    if _aesgcm is None:
        _aesgcm = AESGCM(_load_master_key())
    return _aesgcm


def encrypt(plaintext: str) -> str:
    nonce = os.urandom(_NONCE_BYTES)
    ct = _get_cipher().encrypt(nonce, plaintext.encode("utf-8"), associated_data=None)
    return base64.b64encode(nonce + ct).decode("ascii")


def decrypt(token: str) -> str:
    try:
        blob = base64.b64decode(token)
        nonce, ct = blob[:_NONCE_BYTES], blob[_NONCE_BYTES:]
        return _get_cipher().decrypt(nonce, ct, associated_data=None).decode("utf-8")
    except Exception as e:
        raise EncryptionError(f"Decifratura fallita: {e}") from e
