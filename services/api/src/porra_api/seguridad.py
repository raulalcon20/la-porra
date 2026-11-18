import hashlib
import secrets


def generar_token() -> str:
    """Token aleatorio de 32 bytes, codificado para viajar en URLs y cabeceras."""
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    """Huella SHA-256 del token: es lo único que se guarda en la base de datos."""
    return hashlib.sha256(token.encode()).hexdigest()
