import pytest
from app.core.security import hash_password, verify_password

def test_hash_is_not_plain_text():
    h = hash_password('text')
    assert h != 'text'
    assert len(h) != 32

def test_verify_accepts_correct_password():
    h = hash_password("text")
    assert verify_password("text", h) is True


def test_verify_rejects_wrong_password():
    h = hash_password("text")
    assert verify_password("wrong", h) is False