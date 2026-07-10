from eshia_research.crawler.jobs import compute_checksum


def test_compute_checksum_is_deterministic():
    assert compute_checksum("hello") == compute_checksum("hello")


def test_compute_checksum_differs_for_different_input():
    assert compute_checksum("hello") != compute_checksum("hello!")


def test_compute_checksum_is_sha256_hex_digest():
    checksum = compute_checksum("hello")
    assert checksum == "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
    assert len(checksum) == 64


def test_compute_checksum_sensitive_to_arabic_text():
    assert compute_checksum("الكافي") != compute_checksum("الكافى")
