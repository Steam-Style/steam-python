from Crypto.Cipher import PKCS1_OAEP
from Crypto.Hash import SHA1
from Crypto.PublicKey.RSA import import_key
from os import urandom
from base64 import b64decode


class UniverseKey(object):
    """
    Public keys for Universes.
    """

    Public = import_key(b64decode("""
MIGdMA0GCSqGSIb3DQEBAQUAA4GLADCBhwKBgQDf7BrWLBBmLBc1OhSwfFkRf53T
2Ct64+AVzRkeRuh7h3SiGEYxqQMUeYKO6UWiSRKpI2hzic9pobFhRr3Bvr/WARvY
gdTckPv+T1JzZsuVcNfFjrocejN1oWI0Rrtgt4Bo+hOneoo3S57G9F1fOpn5nsQ6
6WOiu4gZKODnFMBCiQIBEQ==
"""))


def generate_session_key(hmac_secret: bytes = b"") -> tuple[bytes, bytes]:
    """
    Generates a session key and its encrypted form using the Universe public key.

    Args:
        hmac_secret: Optional HMAC secret to append to the session key before encryption.

    Returns:
        A tuple containing the session key and its encrypted form.
    """
    session_key = urandom(32)
    encrypted_session_key = PKCS1_OAEP.new(
        UniverseKey.Public, SHA1).encrypt(session_key + hmac_secret)

    return (session_key, encrypted_session_key)
