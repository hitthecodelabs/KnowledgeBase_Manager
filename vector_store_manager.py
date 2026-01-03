#!/usr/bin/env python3
"""
vector_store_manager.py - Gestión de Vector Stores en OpenAI
=============================================================

Este módulo proporciona funcionalidades para crear, listar, obtener
y eliminar Vector Stores en la plataforma de OpenAI.

¿Qué es un Vector Store?
------------------------
Un Vector Store es un contenedor que almacena archivos indexados
vectorialmente para búsqueda semántica. Permite hacer RAG (Retrieval
Augmented Generation) buscando información relevante en documentos.

Flujo típico:
    1. Crear Vector Store → Obtener vs_id
    2. Subir archivos → Obtener file_ids
    3. Crear File Batch → Indexar archivos en el Vector Store
    4. Buscar → Recuperar chunks relevantes

IDs generados:
    - Vector Store ID: vs_6932899d...cdb6ac7487
    - Estos IDs son persistentes y reutilizables

Ejemplo de uso:
---------------
    from vector_store_manager import create_vector_store, get_vector_store
    
    # Crear nuevo vector store
    vs_id = create_vector_store("mi_base_conocimiento")
    print(f"Creado: {vs_id}")
    
    # Obtener info de uno existente
    info = get_vector_store("vs_6932899d...cdb6ac7487")

Autor: [Tu nombre]
Fecha: 2025
"""

from typing import Optional, List, Dict, Any
from openai import OpenAI
from openai.types.vector_store import VectorStore

from config import client


# =============================================================================
# CREAR VECTOR STORE
# =============================================================================

def create_vector_store(
    name: str,
    metadata: Optional[Dict[str, str]] = None,
    expires_after_days: Optional[int] = None
) -> str:
    """
    Crea un nuevo Vector Store para almacenar archivos indexados.
    
    Un Vector Store es el contenedor principal donde se indexarán
    los archivos para búsqueda semántica. El ID generado es 
    persistente y debe guardarse para uso futuro.
    
    Args:
        name: Nombre descriptivo del vector store.
              Ejemplo: "snatched_base", "faq_knowledge_base"
        
        metadata: Diccionario opcional con metadatos personalizados.
                  Útil para categorización o tracking.
                  Ejemplo: {"project": "ecommerce", "version": "1.0"}
        
        expires_after_days: Días hasta expiración automática.
                           None = sin expiración (por defecto)
    
    Returns:
        str: El ID del vector store creado.
             Formato: vs_XXXXXXXXXXXX
    
    Ejemplo:
        >>> vs_id = create_vector_store("snatched_base")
        >>> print(vs_id)
        vs_6932899d0eb481919e4ccdb6ac7487
        
        >>> # Con metadatos
        >>> vs_id = create_vector_store(
        ...     name="FAQ Base",
        ...     metadata={"category": "customer_support", "language": "en"}
        ... )
    
    Notas:
        - Guarda el vs_id en configuración o base de datos
        - Puedes tener múltiples vector stores por proyecto
        - Cada vector store tiene límites de almacenamiento
    """
    # Preparar parámetros de creación
    create_params: Dict[str, Any] = {"name": name}
    
    if metadata:
        create_params["metadata"] = metadata
    
    if expires_after_days:
        create_params["expires_after"] = {
            "anchor": "last_active_at",
            "days": expires_after_days
        }
    
    # Crear el vector store
    vector_store: VectorStore = client.vector_stores.create(**create_params)
    
    print(f"✓ Vector Store creado exitosamente")
    print(f"  ID: {vector_store.id}")
    print(f"  Nombre: {vector_store.name}")
    print(f"  Estado: {vector_store.status}")
    
    return vector_store.id


# =============================================================================
# OBTENER VECTOR STORE EXISTENTE
# =============================================================================

def get_vector_store(vector_store_id: str) -> VectorStore:
    """
    Obtiene información detallada de un Vector Store existente.
    
    Útil para verificar el estado, conteo de archivos y 
    configuración actual de un vector store.
    
    Args:
        vector_store_id: El ID del vector store.
                        Formato: vs_XXXXXXXXXXXX
    
    Returns:
        VectorStore: Objeto con toda la información del vector store.
                    Atributos importantes:
                    - id: Identificador único
                    - name: Nombre asignado
                    - status: "completed", "in_progress", "expired"
                    - file_counts: Conteo de archivos por estado
                    - created_at: Timestamp de creación
    
    Raises:
        openai.NotFoundError: Si el vector store no existe
    
    Ejemplo:
        >>> vs = get_vector_store("vs_6932899d0eb481919e4ccdb6ac7487")
        >>> print(f"Nombre: {vs.name}")
        Nombre: snatched_base
        >>> print(f"Archivos: {vs.file_counts.completed}")
        Archivos: 15
    """
    vector_store = client.vector_stores.retrieve(vector_store_id)
    
    print(f"✓ Vector Store encontrado")
    print(f"  ID: {vector_store.id}")
    print(f"  Nombre: {vector_store.name}")
    print(f"  Estado: {vector_store.status}")
    
    if vector_store.file_counts:
        print(f"  Archivos completados: {vector_store.file_counts.completed}")
        print(f"  Archivos en progreso: {vector_store.file_counts.in_progress}")
        print(f"  Archivos fallidos: {vector_store.file_counts.failed}")
    
    return vector_store


# =============================================================================
# LISTAR VECTOR STORES
# =============================================================================

def list_vector_stores(limit: int = 20) -> List[VectorStore]:
    """
    Lista todos los Vector Stores de la cuenta.
    
    Args:
        limit: Número máximo de resultados (default: 20, max: 100)
    
    Returns:
        List[VectorStore]: Lista de objetos VectorStore
    
    Ejemplo:
        >>> stores = list_vector_stores()
        >>> for vs in stores:
        ...     print(f"{vs.id}: {vs.name}")
        vs_abc123: FAQ Base
        vs_def456: Product Catalog
    """
    response = client.vector_stores.list(limit=limit)
    vector_stores = list(response.data)
    
    print(f"✓ Encontrados {len(vector_stores)} vector stores:")
    for vs in vector_stores:
        status_emoji = "✓" if vs.status == "completed" else "⏳"
        print(f"  {status_emoji} {vs.id}: {vs.name} [{vs.status}]")
    
    return vector_stores


# =============================================================================
# OBTENER O CREAR VECTOR STORE
# =============================================================================

def get_or_create_vector_store(
    name: str,
    vector_store_id: Optional[str] = None
) -> str:
    """
    Obtiene un Vector Store existente o crea uno nuevo.
    
    Patrón útil para scripts que pueden ejecutarse múltiples veces.
    Si se proporciona un ID y existe, lo usa. Si no, crea uno nuevo.
    
    Args:
        name: Nombre para el vector store (usado si se crea nuevo)
        vector_store_id: ID opcional de un vector store existente
    
    Returns:
        str: ID del vector store (existente o recién creado)
    
    Ejemplo:
        >>> # Primera ejecución: crea nuevo
        >>> vs_id = get_or_create_vector_store("Mi KB")
        ✓ Vector Store creado exitosamente
        
        >>> # Ejecuciones siguientes: usa existente
        >>> vs_id = get_or_create_vector_store("Mi KB", vs_id)
        ✓ Usando vector store existente: vs_abc123
    """
    if vector_store_id:
        try:
            vs = get_vector_store(vector_store_id)
            print(f"✓ Usando vector store existente: {vs.id}")
            return vs.id
        except Exception as e:
            print(f"⚠ Vector store {vector_store_id} no encontrado: {e}")
            print("  Creando uno nuevo...")
    
    return create_vector_store(name)


# =============================================================================
# ELIMINAR VECTOR STORE
# =============================================================================

def delete_vector_store(vector_store_id: str) -> bool:
    """
    Elimina un Vector Store y todos sus archivos indexados.
    
    ⚠️ PRECAUCIÓN: Esta acción es irreversible. Los archivos 
    originales subidos a OpenAI Files NO se eliminan automáticamente.
    
    Args:
        vector_store_id: ID del vector store a eliminar
    
    Returns:
        bool: True si se eliminó exitosamente
    
    Ejemplo:
        >>> delete_vector_store("vs_6932899d0eb481919e4ccdb6ac7487")
        ⚠ Eliminando vector store vs_6932899d...
        ✓ Vector store eliminado exitosamente
        True
    """
    print(f"⚠ Eliminando vector store {vector_store_id}...")
    
    response = client.vector_stores.delete(vector_store_id)
    
    if response.deleted:
        print("✓ Vector store eliminado exitosamente")
        return True
    else:
        print("✗ Error al eliminar vector store")
        return False


# =============================================================================
# EJECUCIÓN DIRECTA (demostración)
# =============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("Demo: Vector Store Manager")
    print("=" * 70)
    
    # Ejemplo 1: Listar vector stores existentes
    print("\n📋 Vector Stores existentes:")
    print("-" * 40)
    stores = list_vector_stores(limit=5)
    
    # Ejemplo 2: Crear nuevo vector store (comentado para no crear basura)
    # print("\n📦 Creando nuevo Vector Store:")
    # print("-" * 40)
    # new_vs_id = create_vector_store(
    #     name="demo_knowledge_base",
    #     metadata={"demo": "true", "created_by": "script"}
    # )
    
    # Ejemplo 3: Obtener detalles de uno existente
    if stores:
        print(f"\n🔍 Detalles del primer Vector Store:")
        print("-" * 40)
        get_vector_store(stores[0].id)
    
    print("\n" + "=" * 70)
