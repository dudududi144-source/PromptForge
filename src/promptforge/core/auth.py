"""PromptForge Authentication."""
import hashlib
import secrets
from typing import Optional


class AuthManager:
    """Authentication manager for API access."""

    def __init__(self):
        self.tokens: dict[str, dict] = {}

    def generate_token(self) -> str:
        """Generate a new API token."""
        token = secrets.token_urlsafe(32)
        self.tokens[token] = {"created": True, "revoked": False}
        return token

    def validate_token(self, token: str) -> bool:
        """Validate an API token."""
        if token not in self.tokens:
            return False
        if self.tokens[token].get("revoked"):
            return False
        return True

    def revoke_token(self, token: str) -> bool:
        """Revoke an API token."""
        if token in self.tokens:
            self.tokens[token]["revoked"] = True
            return True
        return False


def hash_secret(secret: str) -> str:
    """Hash a secret for storage."""
    return hashlib.sha256(secret.encode()).hexdigest()