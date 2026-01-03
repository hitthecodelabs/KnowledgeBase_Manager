#!/usr/bin/env python3
"""
file_uploader.py - Subida de Archivos a OpenAI
===============================================

Este módulo maneja la subida de archivos a la plataforma de OpenAI
para su uso con Assistants, Vector Stores y otras funcionalidades.

Flujo de subida:
    1. Seleccionar archivos locales (glob pattern o lista)
    2. Subir cada archivo → Obtener file_id
    3. Usar file_ids para crear batches o attachments

Formatos soportados para Assistants/Vector Stores:
    - .md (Markdown) - Recomendado para documentación
    - .pdf (PDF)
    - .txt (Texto plano)
    - .docx (Word)
    - .json
    - Y otros (ver documentación oficial)

Límites:
    - Archivo individual: hasta 512 MB
    - Total por organización: hasta 1 TB
    - Para Assistants: hasta 2 millones de tokens por archivo

IDs generados:
    - File ID: file-W5b8FpTkLrNX386CpPSGgZ

Ejemplo de uso:
---------------
    from file_uploader import upload_files_from_pattern, upload_single_file
    
    # Subir todos los .md de una carpeta
    file_ids = upload_files_from_pattern("docs/*.md")
    
    # Subir un archivo específico
    file_id = upload_single_file("faq.md")

Autor: [Tu nombre]
Fecha: 2025
"""

import os
from glob import glob
from typing import List, Optional, Tuple, Literal
from pathlib import Path

from openai import OpenAI
from openai.types.file_object import FileObject

from config import client


# Tipos de propósito válidos para archivos
FilePurpose = Literal[
    "assistants",    # Para Assistants API y Vector Stores
    "batch",         # Para Batch API
    "fine-tune",     # Para fine-tuning
    "vision",        # Para vision fine-tuning
    "user_data",     # Propósito flexible
    "evals"          # Para evaluaciones
]


# =============================================================================
# SUBIR UN SOLO ARCHIVO
# =============================================================================

def upload_single_file(
    file_path: str,
    purpose: FilePurpose = "assistants"
) -> str:
    """
    Sube un único archivo a OpenAI.
    
    El archivo se sube al almacenamiento de OpenAI y recibe un ID
    único que puede usarse para adjuntarlo a vector stores,
    assistants, o para procesamiento batch.
    
    Args:
        file_path: Ruta al archivo local.
                  Ejemplo: "docs/faq.md", "./data/manual.pdf"
        
        purpose: Propósito del archivo (determina validaciones):
                - "assistants": Para Assistants API y Vector Stores
                - "batch": Para Batch API (solo .jsonl)
                - "fine-tune": Para fine-tuning (solo .jsonl)
                - "vision": Para vision fine-tuning
                - "user_data": Uso flexible
                - "evals": Para evaluaciones
    
    Returns:
        str: El file_id del archivo subido.
             Formato: file-XXXXXXXXXXXX
    
    Raises:
        FileNotFoundError: Si el archivo no existe
        openai.BadRequestError: Si el formato no es válido
    
    Ejemplo:
        >>> file_id = upload_single_file("faq_customer_service.md")
        ✓ Subido: faq_customer_service.md -> file-W5b8FpTkLrNX386CpPSGgZ
        
        >>> file_id = upload_single_file("batch_input.jsonl", purpose="batch")
        ✓ Subido: batch_input.jsonl -> file-ABC123...
    
    Notas:
        - Los archivos para "assistants" pueden ser .md, .pdf, .txt, etc.
        - Los archivos para "batch" y "fine-tune" deben ser .jsonl
        - Guarda los file_ids para crear batches posteriormente
    """
    # Validar que el archivo existe
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Archivo no encontrado: {file_path}")
    
    file_name = os.path.basename(file_path)
    file_size = os.path.getsize(file_path)
    
    print(f"📤 Subiendo: {file_name} ({file_size:,} bytes)...")
    
    # Subir el archivo
    with open(file_path, "rb") as f:
        uploaded_file: FileObject = client.files.create(
            file=f,
            purpose=purpose
        )
    
    print(f"✓ Subido: {file_name} -> {uploaded_file.id}")
    
    return uploaded_file.id


# =============================================================================
# SUBIR MÚLTIPLES ARCHIVOS POR PATRÓN
# =============================================================================

def upload_files_from_pattern(
    pattern: str,
    purpose: FilePurpose = "assistants",
    recursive: bool = True
) -> List[str]:
    """
    Sube todos los archivos que coincidan con un patrón glob.
    
    Útil para subir directorios completos de documentación.
    Retorna la lista de file_ids para uso posterior.
    
    Args:
        pattern: Patrón glob para seleccionar archivos.
                Ejemplos:
                - "*.md" - Todos los .md en directorio actual
                - "docs/*.md" - Todos los .md en carpeta docs
                - "*/*.md" - Todos los .md en subdirectorios
                - "**/*.md" - Recursivo (requiere recursive=True)
        
        purpose: Propósito de los archivos (ver upload_single_file)
        
        recursive: Si True, busca recursivamente en subdirectorios
    
    Returns:
        List[str]: Lista de file_ids de los archivos subidos
    
    Raises:
        SystemExit: Si no se encuentran archivos
    
    Ejemplo:
        >>> # Subir todos los markdown de docs
        >>> file_ids = upload_files_from_pattern("docs/*.md")
        📁 Encontrados 15 archivos para subir
        📤 Subiendo: faq_customer_service.md (2,345 bytes)...
        ✓ Subido: faq_customer_service.md -> file-W5b8FpTkLrNX386CpPSGgZ
        ...
        ✓ Subidos 15/15 archivos exitosamente
        
        >>> # Subir recursivamente
        >>> file_ids = upload_files_from_pattern("**/*.md", recursive=True)
    
    Output típico:
        Uploaded: faq_customer_service.md -> file-W5b8FpTkLrNX386CpPSGgZ
        Uploaded: faq_products_care.md -> file-Ns8sgmpmC4V9nf92zFzEDq
        Uploaded: faq_environment_sustainability.md -> file-SeSR77SPsoMUf5sNJbemKe
        ...
    """
    # Buscar archivos
    paths = glob(pattern, recursive=recursive)
    
    if not paths:
        raise SystemExit(f"❌ No se encontraron archivos con patrón: {pattern}")
    
    print(f"📁 Encontrados {len(paths)} archivos para subir")
    print("-" * 50)
    
    file_ids: List[str] = []
    errors: List[Tuple[str, str]] = []
    
    for path in sorted(paths):
        try:
            file_id = upload_single_file(path, purpose=purpose)
            file_ids.append(file_id)
        except Exception as e:
            error_msg = str(e)
            errors.append((path, error_msg))
            print(f"✗ Error subiendo {path}: {error_msg}")
    
    # Resumen
    print("-" * 50)
    print(f"✓ Subidos {len(file_ids)}/{len(paths)} archivos exitosamente")
    
    if errors:
        print(f"⚠ {len(errors)} archivos con errores:")
        for path, err in errors:
            print(f"  - {path}: {err}")
    
    return file_ids


# =============================================================================
# SUBIR LISTA ESPECÍFICA DE ARCHIVOS
# =============================================================================

def upload_file_list(
    file_paths: List[str],
    purpose: FilePurpose = "assistants"
) -> List[str]:
    """
    Sube una lista específica de archivos.
    
    A diferencia de upload_files_from_pattern, esta función
    acepta una lista explícita de rutas de archivo.
    
    Args:
        file_paths: Lista de rutas a archivos.
                   Ejemplo: ["faq.md", "manual.pdf", "terms.txt"]
        purpose: Propósito de los archivos
    
    Returns:
        List[str]: Lista de file_ids subidos exitosamente
    
    Ejemplo:
        >>> files = [
        ...     "docs/faq_customer_service.md",
        ...     "docs/faq_products_care.md",
        ...     "policies/returns.md"
        ... ]
        >>> file_ids = upload_file_list(files)
    """
    print(f"📁 Subiendo {len(file_paths)} archivos específicos")
    print("-" * 50)
    
    file_ids: List[str] = []
    
    for path in file_paths:
        try:
            file_id = upload_single_file(path, purpose=purpose)
            file_ids.append(file_id)
        except Exception as e:
            print(f"✗ Error con {path}: {e}")
    
    print("-" * 50)
    print(f"✓ Subidos {len(file_ids)}/{len(file_paths)} archivos")
    
    return file_ids


# =============================================================================
# LISTAR ARCHIVOS SUBIDOS
# =============================================================================

def list_uploaded_files(
    purpose: Optional[FilePurpose] = None,
    limit: int = 100
) -> List[FileObject]:
    """
    Lista los archivos subidos a OpenAI.
    
    Args:
        purpose: Filtrar por propósito (opcional)
        limit: Número máximo de resultados
    
    Returns:
        List[FileObject]: Lista de objetos de archivo
    
    Ejemplo:
        >>> files = list_uploaded_files(purpose="assistants")
        📋 Archivos en OpenAI (purpose=assistants):
          file-W5b8... faq_customer_service.md (2,345 bytes)
          file-Ns8s... faq_products_care.md (1,892 bytes)
    """
    params = {"limit": limit}
    if purpose:
        params["purpose"] = purpose
    
    response = client.files.list(**params)
    files = list(response.data)
    
    purpose_str = f"purpose={purpose}" if purpose else "todos"
    print(f"📋 Archivos en OpenAI ({purpose_str}):")
    print("-" * 60)
    
    for f in files:
        size_str = f"{f.bytes:,}" if f.bytes else "?"
        print(f"  {f.id[:12]}... {f.filename} ({size_str} bytes)")
    
    print(f"\nTotal: {len(files)} archivos")
    
    return files


# =============================================================================
# ELIMINAR ARCHIVO
# =============================================================================

def delete_file(file_id: str) -> bool:
    """
    Elimina un archivo de OpenAI.
    
    Args:
        file_id: ID del archivo a eliminar
    
    Returns:
        bool: True si se eliminó exitosamente
    
    Ejemplo:
        >>> delete_file("file-W5b8FpTkLrNX386CpPSGgZ")
        ✓ Archivo file-W5b8... eliminado
    """
    response = client.files.delete(file_id)
    
    if response.deleted:
        print(f"✓ Archivo {file_id[:12]}... eliminado")
        return True
    return False


# =============================================================================
# OBTENER INFORMACIÓN DE ARCHIVO
# =============================================================================

def get_file_info(file_id: str) -> FileObject:
    """
    Obtiene información detallada de un archivo.
    
    Args:
        file_id: ID del archivo
    
    Returns:
        FileObject: Información completa del archivo
    
    Ejemplo:
        >>> info = get_file_info("file-W5b8FpTkLrNX386CpPSGgZ")
        >>> print(info.filename, info.bytes)
        faq_customer_service.md 2345
    """
    file_info = client.files.retrieve(file_id)
    
    print(f"📄 Archivo: {file_info.filename}")
    print(f"   ID: {file_info.id}")
    print(f"   Tamaño: {file_info.bytes:,} bytes")
    print(f"   Propósito: {file_info.purpose}")
    print(f"   Estado: {file_info.status}")
    
    return file_info


# =============================================================================
# EJECUCIÓN DIRECTA (demostración)
# =============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("Demo: File Uploader")
    print("=" * 70)
    
    # Ejemplo 1: Listar archivos existentes
    print("\n📋 Archivos existentes en OpenAI:")
    print("-" * 50)
    files = list_uploaded_files(purpose="assistants", limit=10)
    
    # Ejemplo 2: Subir archivos (descomentado para demo real)
    # print("\n📤 Subiendo archivos:")
    # print("-" * 50)
    # file_ids = upload_files_from_pattern("docs/*.md")
    # print(f"\nFile IDs obtenidos: {file_ids}")
    
    print("\n" + "=" * 70)
    print("Para subir archivos, descomenta las líneas de ejemplo")
    print("o usa las funciones en tu propio script")
    print("=" * 70)
