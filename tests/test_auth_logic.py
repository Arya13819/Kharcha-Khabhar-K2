"""check_secret: bcrypt verification + legacy plaintext upgrade path."""
from app import check_secret, bcrypt


def test_correct_password_matches_hash():
    h = bcrypt.generate_password_hash("mypassword").decode("utf-8")
    assert check_secret(h, "mypassword") == (True, False)


def test_wrong_password_fails():
    h = bcrypt.generate_password_hash("mypassword").decode("utf-8")
    assert check_secret(h, "wrong") == (False, False)


def test_legacy_plaintext_matches_and_flags_rehash():
    # Old accounts stored plaintext; a match must request an upgrade
    assert check_secret("plaintext123", "plaintext123") == (True, True)


def test_legacy_plaintext_wrong_fails():
    assert check_secret("plaintext123", "nope") == (False, False)


def test_empty_stored_value_fails_safely():
    assert check_secret(None, "anything") == (False, False)
    assert check_secret("", "anything") == (False, False)
