import hashlib
import zlib

from cryptography.fernet import Fernet, InvalidToken
import pytest

from app.api.v1.commons.hasher import decrypt_unhash_json, hash_encrypt_json


class TestHashEncryptJson:
    """Test cases for hash_encrypt_json function"""

    @pytest.mark.parametrize(
        "json_data,expected_type",
        (
            ({"key": "value", "number": 42}, tuple),
            (["item1", "item2", 123], tuple),
            ("simple string", tuple),
            (42, tuple),
            (True, tuple),
            (None, tuple),
            ({"nested": {"data": [1, 2, 3]}}, tuple),
        ),
    )
    def test_hash_encrypt_json_returns_tuple(self, json_data, expected_type):
        """Test that hash_encrypt_json returns a tuple for various input types"""
        result = hash_encrypt_json(json_data)
        assert isinstance(result, expected_type)
        assert len(result) == 2

    @pytest.mark.parametrize(
        "json_data",
        (
            {"test": "data"},
            [1, 2, 3],
            "string_data",
            123,
            {"complex": {"nested": {"structure": [1, 2, {"deep": True}]}}},
        ),
    )
    def test_hash_digest_format(self, json_data):
        """Test that hash digest is a valid MD5 hex string"""
        hash_digest, encrypted_data = hash_encrypt_json(json_data)

        # MD5 hash should be 32 characters long and hexadecimal
        assert len(hash_digest) == 32
        assert all(c in "0123456789abcdef" for c in hash_digest)

        # Verify it matches expected MD5
        json_str = str(json_data)
        expected_hash = hashlib.md5(json_str.encode()).hexdigest()
        assert hash_digest == expected_hash

    def test_consistent_output_same_input(self):
        """Test that same input produces same hash but different encrypted data"""
        json_data = {"consistent": "test"}

        hash1, encrypted1 = hash_encrypt_json(json_data)
        hash2, encrypted2 = hash_encrypt_json(json_data)

        # Hash should be the same
        assert hash1 == hash2

        # Encrypted data will be different due to Fernet's built-in randomness
        # but both should decrypt to the same compressed data
        cipher = Fernet(b"k3tGwuK6O59c0SEMmnIeJUEpTN5kuxibPy8Q8VfYC6A=")
        decompressed1 = zlib.decompress(cipher.decrypt(encrypted1))
        decompressed2 = zlib.decompress(cipher.decrypt(encrypted2))
        assert decompressed1 == decompressed2


class TestDecryptUnhashJson:
    """Test cases for decrypt_unhash_json function"""

    def test_hash_verification_failure(self):
        """Test that incorrect hash raises ValueError"""
        json_data = {"test": "data"}
        hash_digest, encrypted_data = hash_encrypt_json(json_data)

        # Modify the hash digest
        wrong_hash = "0" * 32

        with pytest.raises(ValueError, match="Hash digest does not match"):
            decrypt_unhash_json(wrong_hash, encrypted_data)

    def test_invalid_encrypted_data(self):
        """Test that invalid encrypted data raises InvalidToken"""
        json_data = {"test": "data"}
        hash_digest, _ = hash_encrypt_json(json_data)

        # Use invalid encrypted data
        invalid_encrypted_data = b"invalid_encrypted_data"

        with pytest.raises(InvalidToken):
            decrypt_unhash_json(hash_digest, invalid_encrypted_data)

    def test_corrupted_encrypted_data(self):
        """Test that corrupted encrypted data raises InvalidToken"""
        json_data = {"test": "data"}
        hash_digest, encrypted_data = hash_encrypt_json(json_data)

        # Corrupt the encrypted data by changing a byte
        corrupted_data = bytearray(encrypted_data)
        corrupted_data[0] = (corrupted_data[0] + 1) % 256

        with pytest.raises(InvalidToken):
            decrypt_unhash_json(hash_digest, bytes(corrupted_data))


class TestRoundTrip:
    """Test cases for round-trip functionality"""

    def test_multiple_roundtrips_same_data(self):
        """Test that multiple encryptions of same data can all be decrypted"""
        original_data = {"test": "multiple_roundtrips", "count": 5}

        # Create multiple encrypted versions
        encrypted_versions = []
        for i in range(3):
            hash_digest, encrypted_data = hash_encrypt_json(original_data)
            encrypted_versions.append((hash_digest, encrypted_data))

        # All hashes should be the same
        hashes = [h for h, _ in encrypted_versions]
        assert all(h == hashes[0] for h in hashes)

        # All should decrypt to original data
        for hash_digest, encrypted_data in encrypted_versions:
            decrypted = decrypt_unhash_json(hash_digest, encrypted_data)
            assert decrypted == original_data


class TestEdgeCases:
    """Test edge cases and error conditions"""

    def test_large_data_structure(self):
        """Test with a larger data structure"""
        large_data = {
            f"key_{i}": {
                "value": f"data_{i}",
                "nested": list(range(10)),
                "meta": {"index": i, "processed": True},
            }
            for i in range(100)
        }

        hash_digest, encrypted_data = hash_encrypt_json(large_data)
        decrypted = decrypt_unhash_json(hash_digest, encrypted_data)
        assert decrypted == large_data

    def test_unicode_data(self):
        """Test with unicode characters"""
        unicode_data = {
            "english": "Hello World",
            "spanish": "Hola Mundo",
            "chinese": "你好世界",
            "emoji": "🔒🔑💾",
            "special": "äöü ñ ßß",
        }

        hash_digest, encrypted_data = hash_encrypt_json(unicode_data)
        decrypted = decrypt_unhash_json(hash_digest, encrypted_data)
        assert decrypted == unicode_data
