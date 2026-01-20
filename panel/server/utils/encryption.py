"""
Utilidades para encriptar/desencriptar datos sensibles (contraseñas RCON)
Usa Fernet (symmetric encryption) de la librería cryptography
"""
import os
import base64
from cryptography.fernet import Fernet
from django.conf import settings

# Clave de encriptación - debe estar en variables de entorno
ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY')

def get_encryption_key():
    """Obtener o generar clave de encriptación"""
    global ENCRYPTION_KEY
    
    if not ENCRYPTION_KEY:
        # Si no existe, generar una nueva (solo para desarrollo)
        # En producción, DEBE estar en variables de entorno
        key = Fernet.generate_key()
        print("⚠️ ADVERTENCIA: ENCRYPTION_KEY no configurada. Generando clave temporal.")
        print(f"⚠️ Configura esta variable en .env: ENCRYPTION_KEY={key.decode()}")
        ENCRYPTION_KEY = key.decode()
    
    # Si es string, convertir a bytes
    if isinstance(ENCRYPTION_KEY, str):
        return ENCRYPTION_KEY.encode()
    return ENCRYPTION_KEY

def encrypt_password(password):
    """Encriptar contraseña RCON"""
    if not password:
        return None
    
    try:
        key = get_encryption_key()
        fernet = Fernet(key)
        encrypted = fernet.encrypt(password.encode())
        return encrypted.decode()
    except Exception as e:
        print(f"Error encriptando contraseña: {e}")
        # En caso de error, retornar sin encriptar (solo para compatibilidad durante migración)
        return password

def decrypt_password(encrypted_password):
    """Desencriptar contraseña RCON"""
    if not encrypted_password:
        return None
    
    try:
        key = get_encryption_key()
        fernet = Fernet(key)
        decrypted = fernet.decrypt(encrypted_password.encode())
        return decrypted.decode()
    except Exception as e:
        # Si falla, puede ser que la contraseña no esté encriptada (migración)
        # Intentar usar directamente
        print(f"Error desencriptando (puede ser contraseña sin encriptar): {e}")
        return encrypted_password

def is_encrypted(password):
    """Verificar si una contraseña está encriptada"""
    if not password:
        return False
    try:
        # Las contraseñas encriptadas con Fernet tienen un formato específico
        # Base64 que termina con '='
        decoded = base64.urlsafe_b64decode(password)
        return len(decoded) == 32  # Fernet token tiene 32 bytes decodificados
    except:
        return False
