#!/usr/bin/env python3
"""
config.py - Configuración central para la API de OpenAI
=========================================================

Este módulo centraliza la configuración y credenciales para interactuar
con la plataforma de OpenAI. Maneja la inicialización del cliente y
las constantes globales del proyecto.

Uso:
----
    from config import client, OPENAI_API_KEY, DEFAULT_MODEL

Notas de Seguridad:
-------------------
    - Nunca commitear API keys al repositorio
    - Usar variables de entorno o archivos .env
    - Agregar .env a .gitignore

Autor: [Tu nombre]
Fecha: 2025
"""

import os
from typing import Optional
from openai import OpenAI

# =============================================================================
# CONFIGURACIÓN DE API KEY
# =============================================================================

def get_api_key() -> str:
    """
    Obtiene la API key de OpenAI desde variables de entorno.
    
    Orden de búsqueda:
        1. Variable de entorno OPENAI_API_KEY
        2. Archivo .env (si python-dotenv está instalado)
    
    Returns:
        str: La API key de OpenAI
    
    Raises:
        ValueError: Si no se encuentra la API key
    
    Ejemplo:
        >>> api_key = get_api_key()
        >>> print(api_key[:20] + "...")
        sk-proj-q5a4_Yw4v...
    """
    # Intentar cargar desde .env si está disponible
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass  # python-dotenv no instalado, continuar sin él
    
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        raise ValueError(
            "No se encontró OPENAI_API_KEY. "
            "Configúrala como variable de entorno o en un archivo .env"
        )
    
    return api_key


# =============================================================================
# INICIALIZACIÓN DEL CLIENTE
# =============================================================================

OPENAI_API_KEY: str = get_api_key()

client: OpenAI = OpenAI(api_key=OPENAI_API_KEY)
"""
Cliente principal de OpenAI inicializado.

Uso:
    from config import client
    
    # Listar modelos
    models = client.models.list()
    
    # Crear completion
    response = client.chat.completions.create(...)
"""


# =============================================================================
# CONSTANTES DEL PROYECTO
# =============================================================================

# Modelo por defecto para completions
DEFAULT_MODEL: str = "gpt-4.1"

# Modelo para tareas de razonamiento complejo
REASONING_MODEL: str = "o4-mini"

# Configuración de Vector Store
DEFAULT_VECTOR_STORE_NAME: str = "knowledge_base"

# Límites de tokens y caracteres
MAX_CONTEXT_CHARS: int = 8000
DEFAULT_SEARCH_RESULTS: int = 5

# Headers para API beta (Assistants v2)
BETA_HEADERS: dict = {
    "OpenAI-Beta": "assistants=v2"
}


# =============================================================================
# FUNCIONES DE UTILIDAD
# =============================================================================

def validate_connection() -> bool:
    """
    Valida que la conexión con OpenAI esté funcionando.
    
    Returns:
        bool: True si la conexión es exitosa
    
    Raises:
        Exception: Si hay error de conexión o autenticación
    
    Ejemplo:
        >>> if validate_connection():
        ...     print("✓ Conexión establecida")
        ✓ Conexión establecida
    """
    try:
        # Intentar listar modelos como prueba de conexión
        models = client.models.list()
        return True
    except Exception as e:
        raise ConnectionError(f"Error de conexión con OpenAI: {e}")


# =============================================================================
# EJECUCIÓN DIRECTA (para testing)
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Verificación de Configuración OpenAI")
    print("=" * 60)
    
    print(f"\n✓ API Key configurada: {OPENAI_API_KEY[:20]}...")
    print(f"✓ Modelo por defecto: {DEFAULT_MODEL}")
    print(f"✓ Modelo de razonamiento: {REASONING_MODEL}")
    
    print("\nValidando conexión...")
    if validate_connection():
        print("✓ Conexión con OpenAI establecida correctamente")
    
    print("\n" + "=" * 60)
