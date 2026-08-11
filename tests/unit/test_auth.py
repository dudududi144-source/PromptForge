"""Tests for authentication module."""
import pytest
from promptforge.core.auth import AuthManager, hash_secret


class TestAuthManager:
    def test_generate_token(self):
        am = AuthManager()
        token = am.generate_token()
        assert isinstance(token, str)
        assert len(token) > 20

    def test_validate_token(self):
        am = AuthManager()
        token = am.generate_token()
        assert am.validate_token(token) is True

    def test_revoke_token(self):
        am = AuthManager()
        token = am.generate_token()
        am.revoke_token(token)
        assert am.validate_token(token) is False


class TestHashSecret:
    def test_hash_secret(self):
        hashed = hash_secret("test_secret")
        assert isinstance(hashed, str)
        assert len(hashed) == 64