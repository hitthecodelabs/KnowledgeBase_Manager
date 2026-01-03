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
import os
import tempfile
import shutil
from datetime import datetime

# Importar módulos existentes
from openai import OpenAI

app = FastAPI(
    title="Vector Store Platform API",
    description="API para gestión de Vector Stores con OpenAI",
    version="1.0.0"
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
    model: str = "gpt-5-mini"  # Default to gpt-5-mini for cost-effectiveness

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
        # Guardar archivo temporalmente
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name

        # Subir a OpenAI con el nombre original del archivo
        with open(tmp_path, "rb") as f:
            uploaded_file = state.client.files.create(
                file=(file.filename, f),  # Tupla (filename, file_object) preserva el nombre original
                purpose="assistants"
            )

        # Limpiar archivo temporal
        os.unlink(tmp_path)

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
    Hacer una consulta al asistente RAG.

    Body:
        {
            "query": "¿Cuál es la política de devoluciones?",
            "vector_store_id": "vs_XXX",  // opcional
            "model": "gpt-4.1"  // opcional
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
        # Realizar búsqueda en el vector store
        # Usando el endpoint de búsqueda directa
        import httpx

        # Construir headers
        headers = {
            "Authorization": f"Bearer {state.api_key}",
            "Content-Type": "application/json",
            "OpenAI-Beta": "assistants=v2"
        }

        # Endpoint de búsqueda
        search_url = f"https://api.openai.com/v1/vector_stores/{vs_id}/search"

        # Realizar búsqueda
        async with httpx.AsyncClient() as client:
            search_response = await client.post(
                search_url,
                headers=headers,
                json={"query": request.query, "max_results": 5},
                timeout=30.0
            )

        if search_response.status_code != 200:
            # Fallback: usar asistente sin búsqueda previa
            context = ""
            sources = []
        else:
            search_data = search_response.json()

            # Extraer contexto
            chunks = []
            sources = []

            for hit in search_data.get("data", [])[:5]:
                content = hit.get("content", "")
                if isinstance(content, list):
                    for item in content:
                        if item.get("type") == "text":
                            chunks.append(item.get("text", {}).get("value", ""))
                elif isinstance(content, str):
                    chunks.append(content)

                # Extraer filename si existe
                filename = hit.get("filename", "unknown")
                if filename not in sources:
                    sources.append(filename)

            context = "\n\n".join(chunks)

        # Construir prompt para GPT
        system_prompt = """Eres un asistente útil que responde preguntas basándote ÚNICAMENTE en el contexto proporcionado.
Si la información no está en el contexto, di "No tengo esa información en mi base de conocimiento."
Sé conciso, preciso y amable."""

        messages = [
            {"role": "system", "content": system_prompt}
        ]

        if context:
            messages.append({
                "role": "system",
                "content": f"CONTEXTO DE LA BASE DE CONOCIMIENTO:\n{context}"
            })

        messages.append({"role": "user", "content": request.query})

        # Generar respuesta con GPT
        completion = state.client.chat.completions.create(
            model=request.model,
            messages=messages,
            temperature=0.7
        )

        answer = completion.choices[0].message.content

        return QueryResponse(
            success=True,
            answer=answer,
            sources=sources,
            context=context[:500] + "..." if len(context) > 500 else context
        )

    except Exception as e:
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
    uvicorn.run(app, host="0.0.0.0", port=8000)
