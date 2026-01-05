#!/usr/bin/env python3
"""
api.py - API REST para Vector Store Platform
=============================================

FastAPI backend para la plataforma de gestión de Vector Stores.

Endpoints:
    POST /api/config           - Configurar OpenAI API key
    POST /api/upload           - Subir archivo (PDF/MD)
    GET  /api/files            - Listar archivos subidos
    POST /api/vector-store     - Crear vector store
    GET  /api/vector-stores    - Listar vector stores
    POST /api/query            - Hacer consulta RAG
    GET  /api/status/{vs_id}   - Obtener estado del vector store

Autor: Knowledge Base Manager
Fecha: 2025
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from io import BytesIO

import os
import logging
import tempfile
import shutil
from datetime import datetime

# Importar módulos existentes
from openai import OpenAI

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
# Uvicorn usa estos loggers; este es el más útil para tracebacks
logger = logging.getLogger("uvicorn.error")

app = FastAPI(
    title="Vector Store Platform API",
    description="API para gestión de Vector Stores con OpenAI",
    version="1.0.0",
    debug=True
)

# Configurar CORS para permitir requests desde el frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios exactos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================================================
# ESTADO GLOBAL DE LA APLICACIÓN
# =============================================================================

class AppState:
    """Estado global de la aplicación"""
    def __init__(self):
        self.client: Optional[OpenAI] = None
        self.api_key: Optional[str] = None
        self.vector_store_id: Optional[str] = None
        self.uploaded_files: List[Dict[str, Any]] = []

state = AppState()

# =============================================================================
# MODELOS PYDANTIC
# =============================================================================

class ConfigRequest(BaseModel):
    api_key: str

class ConfigResponse(BaseModel):
    success: bool
    message: str

class VectorStoreRequest(BaseModel):
    name: str

class VectorStoreResponse(BaseModel):
    success: bool
    vector_store_id: str
    message: str

class QueryRequest(BaseModel):
    query: str
    vector_store_id: Optional[str] = None
    model: str = "gpt-5-mini" # Default to gpt-5-mini for cost-effectiveness

class QueryResponse(BaseModel):
    success: bool
    answer: str
    sources: List[str]
    context: str

class FileInfo(BaseModel):
    file_id: str
    filename: str
    size: int
    uploaded_at: str

class StatusResponse(BaseModel):
    vector_store_id: Optional[str]
    vector_store_name: Optional[str]
    file_count: int
    status: str

# =============================================================================
# ENDPOINTS - CONFIGURACIÓN
# =============================================================================

@app.post("/api/config", response_model=ConfigResponse)
async def configure_api_key(config: ConfigRequest):
    """
    Configurar la OpenAI API key.

    Body:
        {
            "api_key": "sk-proj-..."
        }
    """
    try:
        # Validar API key intentando crear cliente
        client = OpenAI(api_key=config.api_key)

        # Probar conexión
        client.models.list()

        # Guardar en estado
        state.api_key = config.api_key
        state.client = client

        return ConfigResponse(
            success=True,
            message="API key configurada correctamente"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"API key inválida: {str(e)}")

# =============================================================================
# ENDPOINTS - ARCHIVOS
# =============================================================================

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Subir un archivo (PDF o MD) a OpenAI.

    Returns:
        {
            "success": true,
            "file_id": "file-XXX",
            "filename": "documento.pdf",
            "size": 12345
        }
    """
    if not state.client:
        raise HTTPException(status_code=400, detail="API key no configurada")

    # Validar extensión
    if not file.filename.endswith(('.pdf', '.md', '.txt')):
        raise HTTPException(
            status_code=400,
            detail="Solo se permiten archivos .pdf, .md o .txt"
        )

    try:
        # Leer contenido del archivo
        file_content = await file.read()

        # Subir a OpenAI con el nombre original del archivo
        # Usando BytesIO para crear un file-like object con el contenido
        file_obj = BytesIO(file_content)
        file_obj.name = file.filename  # Asignar nombre original

        uploaded_file = state.client.files.create(
            file=file_obj,
            purpose="assistants"
        )

        # Guardar info en estado
        file_info = {
            "file_id": uploaded_file.id,
            "filename": file.filename,
            "size": uploaded_file.bytes,
            "uploaded_at": datetime.now().isoformat()
        }
        state.uploaded_files.append(file_info)

        return {
            "success": True,
            "file_id": uploaded_file.id,
            "filename": file.filename,
            "size": uploaded_file.bytes
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al subir archivo: {str(e)}")

@app.get("/api/files", response_model=List[FileInfo])
async def list_files():
    """
    Listar todos los archivos subidos.
    """
    if not state.client:
        raise HTTPException(status_code=400, detail="API key no configurada")

    return state.uploaded_files

# =============================================================================
# ENDPOINTS - VECTOR STORES
# =============================================================================

@app.post("/api/vector-store", response_model=VectorStoreResponse)
async def create_vector_store(request: VectorStoreRequest):
    """
    Crear un nuevo Vector Store e indexar archivos subidos.

    Body:
        {
            "name": "Mi Knowledge Base"
        }
    """
    if not state.client:
        raise HTTPException(status_code=400, detail="API key no configurada")

    if not state.uploaded_files:
        raise HTTPException(status_code=400, detail="No hay archivos subidos para indexar")

    try:
        # Crear Vector Store
        vector_store = state.client.vector_stores.create(
            name=request.name
        )

        # Obtener file_ids
        file_ids = [f["file_id"] for f in state.uploaded_files]

        # Crear batch para indexar archivos
        batch = state.client.vector_stores.file_batches.create(
            vector_store_id=vector_store.id,
            file_ids=file_ids
        )

        # Guardar en estado
        state.vector_store_id = vector_store.id

        return VectorStoreResponse(
            success=True,
            vector_store_id=vector_store.id,
            message=f"Vector Store creado. Indexando {len(file_ids)} archivos..."
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al crear Vector Store: {str(e)}")

@app.get("/api/vector-stores")
async def list_vector_stores():
    """
    Listar todos los Vector Stores disponibles.
    """
    if not state.client:
        raise HTTPException(status_code=400, detail="API key no configurada")

    try:
        response = state.client.vector_stores.list(limit=20)
        vector_stores = []

        for vs in response.data:
            vector_stores.append({
                "id": vs.id,
                "name": vs.name,
                "status": vs.status,
                "file_counts": {
                    "completed": vs.file_counts.completed if vs.file_counts else 0,
                    "in_progress": vs.file_counts.in_progress if vs.file_counts else 0,
                    "failed": vs.file_counts.failed if vs.file_counts else 0
                },
                "created_at": vs.created_at
            })

        return {
            "success": True,
            "vector_stores": vector_stores
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al listar Vector Stores: {str(e)}")

@app.get("/api/status/{vector_store_id}", response_model=StatusResponse)
async def get_status(vector_store_id: str):
    """
    Obtener el estado de un Vector Store específico.
    """
    if not state.client:
        raise HTTPException(status_code=400, detail="API key no configurada")

    try:
        vs = state.client.vector_stores.retrieve(vector_store_id)

        return StatusResponse(
            vector_store_id=vs.id,
            vector_store_name=vs.name,
            file_count=vs.file_counts.completed if vs.file_counts else 0,
            status=vs.status
        )

    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Vector Store no encontrado: {str(e)}")

@app.get("/api/vector-stores/{vector_store_id}/files")
async def list_vector_store_files(vector_store_id: str, limit: int = 100):
    """
    Listar archivos de un Vector Store específico.
    Args:
        vector_store_id: ID del vector store
        limit: Número máximo de archivos a retornar (máx 100)
    """
    if not state.client:
        raise HTTPException(status_code=400, detail="API key no configurada")

    try:
        # Limitar a máximo 100
        limit = min(limit, 100)

        # Obtener archivos del vector store
        vs_files = state.client.vector_stores.files.list(
            vector_store_id=vector_store_id,
            limit=limit
        )

        files = []
        for item in vs_files.data:
            # Obtener metadatos del archivo
            try:
                file_meta = state.client.files.retrieve(item.id)
                files.append({
                    "id": item.id,
                    "status": item.status,
                    "filename": file_meta.filename,
                    "purpose": file_meta.purpose,
                    "bytes": file_meta.bytes,
                    "created_at": file_meta.created_at
                })
            except Exception as e:
                # Si falla obtener metadatos (archivo eliminado o error),
                # omitir el archivo en lugar de mostrarlo como "unknown"
                print(f"Warning: No se pudieron obtener metadatos para archivo {item.id}: {e}")
                continue

        return {
            "success": True,
            "vector_store_id": vector_store_id,
            "files": files,
            "total": len(files)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al listar archivos: {str(e)}")

@app.post("/api/vector-stores/{vector_store_id}/add-files")
async def add_files_to_vector_store(vector_store_id: str):
    """
    Agregar archivos nuevos a un Vector Store existente.
    Este endpoint:
    1. Obtiene los file_ids actuales del Vector Store
    2. Agrega los nuevos file_ids de archivos subidos
    3. Crea un nuevo batch con TODOS los file_ids
    4. Retorna el batch_id para monitoreo
    Args:
        vector_store_id: ID del vector store existente
    """
    if not state.client:
        raise HTTPException(status_code=400, detail="API key no configurada")

    if not state.uploaded_files:
        raise HTTPException(status_code=400, detail="No hay archivos nuevos para agregar")

    try:
        # 1. Obtener file_ids existentes en el Vector Store
        existing_file_ids = []
        vs_files = state.client.vector_stores.files.list(
            vector_store_id=vector_store_id,
            limit=100
        )

        for item in vs_files.data:
            existing_file_ids.append(item.id)

        # 2. Obtener nuevos file_ids de archivos subidos
        new_file_ids = [f["file_id"] for f in state.uploaded_files]

        # 3. Combinar todos los file_ids (existentes + nuevos)
        all_file_ids = existing_file_ids + new_file_ids

        # 4. Crear batch con todos los file_ids
        batch = state.client.vector_stores.file_batches.create(
            vector_store_id=vector_store_id,
            file_ids=all_file_ids
        )

        # 5. Actualizar estado
        state.vector_store_id = vector_store_id

        return {
            "success": True,
            "batch_id": batch.id,
            "vector_store_id": vector_store_id,
            "total_files": len(all_file_ids),
            "existing_files": len(existing_file_ids),
            "new_files": len(new_file_ids),
            "message": f"Batch creado. Procesando {len(all_file_ids)} archivos..."
        }

    except Exception as e:
        logger.exception("Error al agregar archivos a Vector Store %s", vector_store_id)
        raise HTTPException(status_code=500, detail=f"Error al agregar archivos: {str(e)}")

@app.get("/api/vector-stores/{vector_store_id}/batch/{batch_id}/status")
async def get_batch_status(vector_store_id: str, batch_id: str):
    """
    Obtener el estado de un batch de indexación.
    Args:
        vector_store_id: ID del vector store
        batch_id: ID del batch a consultar
    """
    if not state.client:
        raise HTTPException(status_code=400, detail="API key no configurada")

    try:
        batch = state.client.vector_stores.file_batches.retrieve(
            vector_store_id=vector_store_id,
            batch_id=batch_id
        )

        file_counts = {
            "completed": batch.file_counts.completed if batch.file_counts else 0,
            "in_progress": batch.file_counts.in_progress if batch.file_counts else 0,
            "failed": batch.file_counts.failed if batch.file_counts else 0,
            "cancelled": batch.file_counts.cancelled if batch.file_counts else 0,
            "total": batch.file_counts.total if batch.file_counts else 0
        }

        return {
            "success": True,
            "batch_id": batch.id,
            "status": batch.status,
            "file_counts": file_counts,
            "is_complete": batch.status not in ("queued", "in_progress")
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener estado del batch: {str(e)}")

@app.delete("/api/vector-stores/{vector_store_id}/files/{file_id}")
async def delete_file_from_vector_store(vector_store_id: str, file_id: str):
    """
    Eliminar un archivo de un Vector Store.
    Args:
        vector_store_id: ID del vector store
        file_id: ID del archivo a eliminar
    """
    if not state.client:
        raise HTTPException(status_code=400, detail="API key no configurada")

    try:
        state.client.vector_stores.files.delete(
            vector_store_id=vector_store_id,
            file_id=file_id
        )

        return {
            "success": True,
            "message": f"Archivo {file_id} eliminado del Vector Store"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar archivo: {str(e)}")

@app.get("/api/vector-stores/{vector_store_id}/files/{file_id}/content")
async def get_file_content(vector_store_id: str, file_id: str):
    """
    Obtener el contenido de un archivo de un Vector Store (solo archivos de texto: .md, .txt).
    Args:
        vector_store_id: ID del vector store
        file_id: ID del archivo
    """
    if not state.client:
        raise HTTPException(status_code=400, detail="API key no configurada")

    try:
        # Obtener metadatos del archivo
        file_meta = state.client.files.retrieve(file_id)

        # Verificar si es archivo de texto
        filename = file_meta.filename.lower()
        is_text = filename.endswith(('.md', '.txt'))

        if not is_text:
            return {
                "success": False,
                "message": f"Archivo {file_meta.filename} no es de texto plano. Solo se soportan .md y .txt",
                "filename": file_meta.filename,
                "content": None
            }

        # Obtener contenido del archivo desde el Vector Store
        # Este es el método correcto para archivos con purpose="assistants"
        page = state.client.vector_stores.files.content(
            vector_store_id=vector_store_id,
            file_id=file_id
        )

        # Extraer texto de todos los items
        text_parts = []
        for item in page.data:
            if item.type == "text" and item.text:
                text_parts.append(item.text)

        content_text = "\n".join(text_parts)

        return {
            "success": True,
            "filename": file_meta.filename,
            "file_id": file_id,
            "content": content_text,
            "size": file_meta.bytes
        }

    except Exception as e:
        logger.exception("Error al obtener contenido de archivo %s en VS %s", file_id, vector_store_id)
        raise HTTPException(status_code=500, detail=f"Error al obtener contenido: {str(e)}")
    
# =============================================================================
# ENDPOINTS - CONSULTAS RAG
# =============================================================================

@app.post("/api/query", response_model=QueryResponse)
async def query_rag(request: QueryRequest):
    """
    Hacer una consulta RAG usando búsqueda directa en Vector Store.
    Body:
        {
            "query": "¿Cuál es la política de devoluciones?",
            "vector_store_id": "vs_XXX",  // opcional
            "model": "gpt-5"  // opcional
        }
    """
    if not state.client:
        raise HTTPException(status_code=400, detail="API key no configurada")

    # Determinar vector_store_id a usar
    vs_id = request.vector_store_id or state.vector_store_id
    if not vs_id:
        raise HTTPException(
            status_code=400,
            detail="No hay Vector Store configurado. Crea uno primero."
        )

    try:
        import httpx

        # 1. Búsqueda directa en Vector Store
        search_url = f"https://api.openai.com/v1/vector_stores/{vs_id}/search"
        headers = {
            "Authorization": f"Bearer {state.api_key}",
            "Content-Type": "application/json",
            "OpenAI-Beta": "assistants=v2",
        }
        payload = {
            "query": request.query,
            "max_num_results": 20  # Obtener top 20 chunks más relevantes
        }

        async with httpx.AsyncClient() as http_client:
            search_response = await http_client.post(
                search_url,
                headers=headers,
                json=payload,
                timeout=60.0
            )
            search_response.raise_for_status()
            search_data = search_response.json()

        # 2. Extraer texto de los hits
        def extract_text_from_hit(hit):
            """Extrae texto de un hit del vector store"""
            parts = hit.get("content", []) or []
            texts = []
            for p in parts:
                if not isinstance(p, dict):
                    continue
                # Caso A: {"text": "..."}
                if isinstance(p.get("text"), str):
                    texts.append(p["text"])
                # Caso B: {"type":"text","text":{"value":"..."}}
                elif isinstance(p.get("text"), dict) and isinstance(p["text"].get("value"), str):
                    texts.append(p["text"]["value"])
                # Caso C: {"type":"text","value":"..."}
                elif p.get("type") == "text" and isinstance(p.get("value"), str):
                    texts.append(p["value"])
            return "\n".join(t.strip() for t in texts if t and t.strip()).strip()

        # 3. Construir contexto y extraer fuentes
        chunks = []
        sources = []
        file_id_to_name = {}

        for i, hit in enumerate(search_data.get("data", [])[:10], start=1):  # Top 10 chunks
            file_id = hit.get("file_id")
            txt = extract_text_from_hit(hit)

            if txt:
                chunks.append(f"[Chunk #{i}]\n{txt}")

                # Obtener filename si no lo tenemos
                if file_id and file_id not in file_id_to_name:
                    try:
                        file_info = state.client.files.retrieve(file_id)
                        file_id_to_name[file_id] = file_info.filename
                        if file_info.filename not in sources:
                            sources.append(file_info.filename)
                    except:
                        pass

        context = "\n\n---\n\n".join(chunks)
        context = context[:8000]  # Limitar a 8000 caracteres

        # 4. Si no hay contexto, responder directamente
        if not context:
            return QueryResponse(
                success=True,
                answer="No encontré información relevante en los documentos para responder a tu pregunta.",
                sources=[],
                context=""
            )

        # 5. Construir prompt y llamar al modelo
        system_prompt = """Eres un asistente útil que responde preguntas basándote ÚNICAMENTE en el contexto proporcionado de la base de conocimiento.

REGLAS:
- Usa SOLO la información del contexto KB que se te proporciona
- Si la información no está en el contexto, di claramente que no tienes esa información
- Sé preciso, conciso y amable
- Responde en el mismo idioma que la pregunta"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "system", "content": f"CONTEXTO DE LA BASE DE CONOCIMIENTO:\n\n{context}"},
            {"role": "user", "content": request.query}
        ]

        # 6. Generar respuesta
        completion = state.client.chat.completions.create(
            model=request.model,
            messages=messages,
            reasoning_effort="high",
        )

        answer = completion.choices[0].message.content

        return QueryResponse(
            success=True,
            answer=answer,
            sources=sources,
            context=context[:500] + "..." if len(context) > 500 else context
        )

    except HTTPException:
        raise
    except httpx.HTTPStatusError as e:
        import traceback
        error_detail = f"Error en búsqueda de Vector Store: {e.response.status_code} - {e.response.text}\n{traceback.format_exc()}"
        print(error_detail)
        raise HTTPException(
            status_code=500,
            detail=f"Error en búsqueda: {e.response.status_code}"
        )
    except Exception as e:
        import traceback
        error_detail = f"Error al procesar consulta: {str(e)}\n{traceback.format_exc()}"
        print(error_detail)
        raise HTTPException(status_code=500, detail=f"Error al procesar consulta: {str(e)}")

# =============================================================================
# ENDPOINT DE SALUD
# =============================================================================

@app.get("/")
async def root():
    """Endpoint raíz para verificar que la API está funcionando"""
    return {
        "message": "Vector Store Platform API",
        "version": "1.0.0",
        "status": "running",
        "configured": state.client is not None
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "api_configured": state.client is not None,
        "vector_store_configured": state.vector_store_id is not None,
        "files_uploaded": len(state.uploaded_files)
    }

# =============================================================================
# EJECUCIÓN
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, 
                host="0.0.0.0", 
                port=8000, 
                # reload=True,          # hot reload en desarrollo
                log_level="debug",    # logs verbose
                access_log=True,      # logs de requests
                )