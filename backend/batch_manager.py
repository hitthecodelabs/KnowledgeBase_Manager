#!/usr/bin/env python3
"""
batch_manager.py - Gestión de File Batches para Vector Stores
==============================================================

Este módulo maneja la creación y monitoreo de File Batches, que son
el mecanismo para indexar múltiples archivos en un Vector Store.

¿Qué es un File Batch?
----------------------
Un File Batch es una operación que procesa múltiples archivos
simultáneamente para indexarlos en un Vector Store. Cuando subes
archivos, estos no se indexan automáticamente; necesitas crear
un batch para que OpenAI los procese y los haga buscables.

Flujo:
    1. Tener un vector_store_id (de vector_store_manager)
    2. Tener una lista de file_ids (de file_uploader)
    3. Crear file batch → Obtener batch_id
    4. Esperar a que complete el procesamiento
    5. Los archivos ya son buscables en el vector store

IDs generados:
    - Batch ID: vsfb_ibj_69328...6ecf92f

Estados del batch:
    - "in_progress": Procesando archivos
    - "completed": Todos los archivos indexados
    - "failed": Error en procesamiento
    - "cancelled": Cancelado por usuario

Ejemplo de uso:
---------------
    from batch_manager import create_file_batch, wait_for_batch
    
    # Crear batch
    batch_id = create_file_batch(vs_id, file_ids)
    
    # Esperar completado
    status = wait_for_batch(vs_id, batch_id)

Autor: [Tu nombre]
Fecha: 2025
"""

import time
from typing import List, Optional, Dict, Any
from openai import OpenAI
from openai.types.vector_stores import VectorStoreFileBatch

from config import client


# =============================================================================
# CREAR FILE BATCH
# =============================================================================

def create_file_batch(
    vector_store_id: str,
    file_ids: List[str],
    chunking_strategy: Optional[Dict[str, Any]] = None
) -> str:
    """
    Crea un File Batch para indexar archivos en un Vector Store.
    
    El batch procesa los archivos, los divide en chunks, genera
    embeddings y los indexa para búsqueda semántica.
    
    Args:
        vector_store_id: ID del vector store destino.
                        Formato: vs_XXXXXXXXXXXX
        
        file_ids: Lista de IDs de archivos a indexar.
                 Formato: ["file-ABC123", "file-DEF456", ...]
                 
        chunking_strategy: Estrategia de división opcional.
                          Por defecto usa "auto" que funciona bien.
                          Ejemplo personalizado:
                          {
                              "type": "static",
                              "static": {
                                  "max_chunk_size_tokens": 800,
                                  "chunk_overlap_tokens": 400
                              }
                          }
    
    Returns:
        str: El batch_id del batch creado.
             Formato: vsfb_XXXXXXXXXXXX
    
    Ejemplo:
        >>> file_ids = [
        ...     "file-W5b8FpTkLrNX386CpPSGgZ",
        ...     "file-Ns8sgmpmC4V9nf92zFzEDq",
        ...     "file-SeSR77SPsoMUf5sNJbemKe"
        ... ]
        >>> batch_id = create_file_batch("vs_6932899d...", file_ids)
        🔄 Creando file batch...
        ✓ Batch creado: vsfb_ibj_69328...6ecf92f
          Archivos: 3
          Estado: in_progress
    
    Notas:
        - El procesamiento es asíncrono
        - Usa wait_for_batch() para esperar completado
        - Archivos grandes pueden tardar más
    """
    print(f"🔄 Creando file batch para {len(file_ids)} archivos...")
    
    # Preparar parámetros
    create_params = {
        "vector_store_id": vector_store_id,
        "file_ids": file_ids
    }
    
    if chunking_strategy:
        create_params["chunking_strategy"] = chunking_strategy
    
    # Crear el batch
    batch: VectorStoreFileBatch = client.vector_stores.file_batches.create(
        **create_params
    )
    
    print(f"✓ Batch creado: {batch.id}")
    print(f"  Archivos: {len(file_ids)}")
    print(f"  Estado: {batch.status}")
    
    if batch.file_counts:
        print(f"  Completados: {batch.file_counts.completed}")
        print(f"  En progreso: {batch.file_counts.in_progress}")
        print(f"  Fallidos: {batch.file_counts.failed}")
    
    return batch.id


# =============================================================================
# OBTENER ESTADO DEL BATCH
# =============================================================================

def get_batch_status(
    vector_store_id: str,
    batch_id: str
) -> VectorStoreFileBatch:
    """
    Obtiene el estado actual de un File Batch.
    
    Args:
        vector_store_id: ID del vector store
        batch_id: ID del batch a consultar
    
    Returns:
        VectorStoreFileBatch: Objeto con información del batch
            - status: "in_progress", "completed", "failed", "cancelled"
            - file_counts: Conteo de archivos por estado
    
    Ejemplo:
        >>> batch = get_batch_status("vs_123...", "vsfb_456...")
        >>> print(batch.status)
        completed
        >>> print(batch.file_counts.completed)
        15
    """
    batch = client.vector_stores.file_batches.retrieve(
        vector_store_id=vector_store_id,
        batch_id=batch_id
    )
    
    return batch


# =============================================================================
# ESPERAR COMPLETADO DEL BATCH
# =============================================================================

def wait_for_batch(
    vector_store_id: str,
    batch_id: str,
    timeout_seconds: int = 300,
    poll_interval: int = 5,
    verbose: bool = True
) -> str:
    """
    Espera a que un File Batch complete su procesamiento.
    
    Hace polling periódico del estado del batch hasta que
    complete, falle o se agote el tiempo de espera.
    
    Args:
        vector_store_id: ID del vector store
        batch_id: ID del batch a monitorear
        timeout_seconds: Tiempo máximo de espera (default: 300s = 5min)
        poll_interval: Segundos entre cada verificación (default: 5s)
        verbose: Si True, imprime progreso
    
    Returns:
        str: Estado final ("completed", "failed", "cancelled")
    
    Raises:
        TimeoutError: Si se agota el tiempo de espera
    
    Ejemplo:
        >>> batch_id = create_file_batch(vs_id, file_ids)
        >>> status = wait_for_batch(vs_id, batch_id)
        ⏳ Esperando batch vsfb_123...
        [10s] in_progress - 3/15 archivos completados
        [15s] in_progress - 8/15 archivos completados
        [20s] completed - 15/15 archivos completados
        ✓ Batch completado exitosamente
    
    Notas:
        - Para archivos pequeños (<1MB), suele completar en <30s
        - Archivos grandes o muchos archivos pueden tardar minutos
        - El timeout de 5 minutos suele ser suficiente
    """
    if verbose:
        print(f"⏳ Esperando batch {batch_id[:20]}...")
    
    start_time = time.time()
    
    while True:
        elapsed = int(time.time() - start_time)
        
        # Verificar timeout
        if elapsed >= timeout_seconds:
            raise TimeoutError(
                f"Batch no completó en {timeout_seconds}s. "
                f"Último estado: {batch.status}"
            )
        
        # Obtener estado actual
        batch = get_batch_status(vector_store_id, batch_id)
        
        # Mostrar progreso
        if verbose and batch.file_counts:
            completed = batch.file_counts.completed
            total = (batch.file_counts.completed + 
                    batch.file_counts.in_progress + 
                    batch.file_counts.failed +
                    batch.file_counts.cancelled)
            print(f"  [{elapsed}s] {batch.status} - {completed}/{total} archivos completados")
        
        # Verificar estados finales
        if batch.status == "completed":
            if verbose:
                print("✓ Batch completado exitosamente")
            return "completed"
        
        if batch.status == "failed":
            if verbose:
                print(f"✗ Batch falló")
                if batch.file_counts:
                    print(f"  Fallidos: {batch.file_counts.failed}")
            return "failed"
        
        if batch.status == "cancelled":
            if verbose:
                print("⚠ Batch cancelado")
            return "cancelled"
        
        # Esperar antes de siguiente poll
        time.sleep(poll_interval)


# =============================================================================
# CREAR BATCH Y ESPERAR
# =============================================================================

def create_and_wait_batch(
    vector_store_id: str,
    file_ids: List[str],
    timeout_seconds: int = 300
) -> str:
    """
    Función de conveniencia que crea un batch y espera su completado.
    
    Combina create_file_batch() y wait_for_batch() en una sola llamada.
    
    Args:
        vector_store_id: ID del vector store
        file_ids: Lista de file_ids a indexar
        timeout_seconds: Tiempo máximo de espera
    
    Returns:
        str: Estado final del batch
    
    Ejemplo:
        >>> status = create_and_wait_batch(vs_id, file_ids)
        🔄 Creando file batch para 15 archivos...
        ✓ Batch creado: vsfb_123...
        ⏳ Esperando batch vsfb_123...
        [5s] in_progress - 5/15 archivos completados
        [10s] completed - 15/15 archivos completados
        ✓ Batch completado exitosamente
        
        >>> print(status)
        completed
    """
    batch_id = create_file_batch(vector_store_id, file_ids)
    return wait_for_batch(vector_store_id, batch_id, timeout_seconds)


# =============================================================================
# LISTAR BATCHES DE UN VECTOR STORE
# =============================================================================

def list_batches(
    vector_store_id: str,
    limit: int = 20
) -> List[VectorStoreFileBatch]:
    """
    Lista los File Batches de un Vector Store.
    
    Args:
        vector_store_id: ID del vector store
        limit: Número máximo de resultados
    
    Returns:
        List[VectorStoreFileBatch]: Lista de batches
    
    Ejemplo:
        >>> batches = list_batches("vs_6932899d...")
        📋 Batches del vector store:
          vsfb_abc... completed (15/15 archivos)
          vsfb_def... in_progress (3/10 archivos)
    """
    response = client.vector_stores.file_batches.list(
        vector_store_id=vector_store_id,
        limit=limit
    )
    
    batches = list(response.data)
    
    print(f"📋 Batches del vector store:")
    for b in batches:
        counts = b.file_counts
        if counts:
            total = counts.completed + counts.in_progress + counts.failed
            print(f"  {b.id[:15]}... {b.status} ({counts.completed}/{total} archivos)")
        else:
            print(f"  {b.id[:15]}... {b.status}")
    
    return batches


# =============================================================================
# CANCELAR BATCH
# =============================================================================

def cancel_batch(
    vector_store_id: str,
    batch_id: str
) -> bool:
    """
    Cancela un File Batch en progreso.
    
    Args:
        vector_store_id: ID del vector store
        batch_id: ID del batch a cancelar
    
    Returns:
        bool: True si se canceló exitosamente
    
    Ejemplo:
        >>> cancel_batch("vs_123...", "vsfb_456...")
        ⚠ Cancelando batch vsfb_456...
        ✓ Batch cancelado
    """
    print(f"⚠ Cancelando batch {batch_id[:15]}...")
    
    batch = client.vector_stores.file_batches.cancel(
        vector_store_id=vector_store_id,
        batch_id=batch_id
    )
    
    if batch.status == "cancelled":
        print("✓ Batch cancelado")
        return True
    else:
        print(f"Estado actual: {batch.status}")
        return False


# =============================================================================
# EJECUCIÓN DIRECTA (demostración)
# =============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("Demo: Batch Manager")
    print("=" * 70)
    
    # Para una demo real, necesitas IDs válidos:
    # VS_ID = "vs_6932899d0eb481919e4ccdb6ac7487"
    # FILE_IDS = ["file-abc123", "file-def456"]
    
    print("""
Ejemplo de uso típico:
    
    from batch_manager import create_and_wait_batch
    from vector_store_manager import create_vector_store
    from file_uploader import upload_files_from_pattern
    
    # 1. Crear vector store
    vs_id = create_vector_store("Mi Knowledge Base")
    
    # 2. Subir archivos
    file_ids = upload_files_from_pattern("docs/*.md")
    
    # 3. Crear batch y esperar
    status = create_and_wait_batch(vs_id, file_ids)
    
    # 4. ¡Listo para búsquedas!
    """)
    
    print("=" * 70)
