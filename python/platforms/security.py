from __future__ import annotations

import base64
import hashlib
import hmac


def verify_hmac_sha256(body: bytes, secret: str, provided: str, prefix: str = "") -> bool:
    actual = provided[len(prefix):] if prefix and provided.startswith(prefix) else provided
    expected = base64.b64encode(hmac.new(secret.encode(), body, hashlib.sha256).digest()).decode()
    return hmac.compare_digest(expected, actual)
