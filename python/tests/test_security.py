import base64
import hashlib
import hmac
import unittest

from platforms.security import verify_hmac_sha256


class SecurityTests(unittest.TestCase):
    def test_valid_and_invalid_signatures(self):
        body = b'{"event":"message"}'
        secret = "secret"
        signature = base64.b64encode(hmac.new(secret.encode(), body, hashlib.sha256).digest()).decode()
        self.assertTrue(verify_hmac_sha256(body, secret, "sha256=" + signature, "sha256="))
        self.assertFalse(verify_hmac_sha256(body + b"x", secret, "sha256=" + signature, "sha256="))


if __name__ == "__main__":
    unittest.main()
