import hashlib
import secrets

# Sin caracteres que se confunden al leerlos o dictarlos: 0/O, 1/I/L
ALFABETO_INVITACION = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
LONGITUD_INVITACION = 8


def generar_token() -> str:
    """Token aleatorio de 32 bytes, codificado para viajar en URLs y cabeceras."""
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    """Huella SHA-256 del token: es lo único que se guarda en la base de datos."""
    return hashlib.sha256(token.encode()).hexdigest()


def generar_codigo_invitacion() -> str:
    """Código de invitación aleatorio, fácil de leer y de dictar."""
    return "".join(secrets.choice(ALFABETO_INVITACION) for _ in range(LONGITUD_INVITACION))


def normalizar_codigo(codigo: str) -> str:
    """Acepta el código con espacios o en minúsculas, como lo escribiría una persona."""
    return codigo.strip().upper()
