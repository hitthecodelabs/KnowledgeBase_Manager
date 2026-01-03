#!/usr/bin/env python3
"""
main.py - Script Principal de Orquestación
===========================================

Este script demuestra el flujo completo de trabajo con Vector Stores:
1. Crear/obtener vector store
2. Subir archivos
3. Crear batch y esperar indexación
4. Probar búsquedas
5. Hacer preguntas con RAG

Uso:
    python main.py --action setup     # Crear VS y subir archivos
    python main.py --action search    # Probar búsquedas
    python main.py --action ask       # Hacer preguntas interactivas
    python main.py --action test      # Ejecutar tests

Autor: [Tu nombre]
Fecha: 2025
"""

import argparse
import json
import os
from typing import Optional

from config import validate_connection
from vector_store_manager import (
    create_vector_store,
    get_or_create_vector_store,
    get_vector_store,
    list_vector_stores
)
from file_uploader import (
    upload_files_from_pattern,
    list_uploaded_files
)
from batch_manager import (
    create_and_wait_batch,
    list_batches
)
from vector_search import (
    search_and_extract,
    display_results
)
from rag_assistant import (
    RAGAssistant,
    run_test_suite
)


# =============================================================================
# CONFIGURACIÓN DEL PROYECTO
# =============================================================================

# Archivo de configuración para persistir IDs
CONFIG_FILE = ".openai_kb_config.json"

def load_config() -> dict:
    """Carga configuración guardada."""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}

def save_config(config: dict) -> None:
    """Guarda configuración."""
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


# =============================================================================
# ACCIONES PRINCIPALES
# =============================================================================

def action_setup(
    name: str = "Knowledge Base",
    file_pattern: str = "docs/**/*.md",
    vs_id: Optional[str] = None
) -> str:
    """
    Configura el vector store completo: crear, subir, indexar.
    
    Args:
        name: Nombre del vector store
        file_pattern: Patrón glob para archivos a subir
        vs_id: ID existente (opcional, para agregar archivos)
    
    Returns:
        str: ID del vector store configurado
    """
    print("=" * 70)
    print("🚀 SETUP: Configurando Knowledge Base")
    print("=" * 70)
    
    # 1. Crear o usar vector store existente
    print("\n📦 Paso 1: Vector Store")
    print("-" * 40)
    vs_id = get_or_create_vector_store(name, vs_id)
    
    # 2. Subir archivos
    print(f"\n📤 Paso 2: Subiendo archivos ({file_pattern})")
    print("-" * 40)
    file_ids = upload_files_from_pattern(file_pattern)
    
    if not file_ids:
        print("⚠ No se subieron archivos")
        return vs_id
    
    # 3. Crear batch y esperar
    print("\n🔄 Paso 3: Indexando archivos")
    print("-" * 40)
    status = create_and_wait_batch(vs_id, file_ids, timeout_seconds=600)
    
    if status == "completed":
        print("\n✓ Knowledge Base configurada exitosamente!")
    else:
        print(f"\n⚠ Batch terminó con estado: {status}")
    
    # 4. Guardar configuración
    config = load_config()
    config["vector_store_id"] = vs_id
    config["last_file_ids"] = file_ids
    save_config(config)
    
    print(f"\n📋 Configuración guardada en {CONFIG_FILE}")
    print(f"   Vector Store ID: {vs_id}")
    print(f"   Archivos indexados: {len(file_ids)}")
    
    return vs_id


def action_search(query: str, vs_id: Optional[str] = None) -> None:
    """
    Realiza una búsqueda en el vector store.
    
    Args:
        query: Consulta de búsqueda
        vs_id: ID del vector store (usa guardado si no se especifica)
    """
    # Obtener VS ID
    if not vs_id:
        config = load_config()
        vs_id = config.get("vector_store_id")
    
    if not vs_id:
        print("❌ No hay vector store configurado.")
        print("   Ejecuta primero: python main.py --action setup")
        return
    
    print("=" * 70)
    print("🔍 SEARCH: Búsqueda en Knowledge Base")
    print("=" * 70)
    print(f"Vector Store: {vs_id}")
    print(f"Query: {query}")
    print("-" * 70)
    
    context, hits = search_and_extract(vs_id, query, max_results=5)
    display_results(hits)
    
    print("\n📝 Contexto extraído:")
    print("-" * 40)
    print(context[:1000] + "..." if len(context) > 1000 else context)


def action_ask(question: str, vs_id: Optional[str] = None) -> None:
    """
    Hace una pregunta al asistente RAG.
    
    Args:
        question: Pregunta a responder
        vs_id: ID del vector store
    """
    if not vs_id:
        config = load_config()
        vs_id = config.get("vector_store_id")
    
    if not vs_id:
        print("❌ No hay vector store configurado.")
        return
    
    print("=" * 70)
    print("💬 ASK: Pregunta al Asistente")
    print("=" * 70)
    
    assistant = RAGAssistant(vs_id)
    response = assistant.answer(question)
    
    print(f"\n❓ Pregunta: {question}")
    print(f"\n💡 Respuesta:\n{response.answer}")
    print(f"\n📚 Fuentes: {', '.join(response.sources)}")


def action_test(vs_id: Optional[str] = None) -> None:
    """
    Ejecuta tests de validación del RAG.
    """
    if not vs_id:
        config = load_config()
        vs_id = config.get("vector_store_id")
    
    if not vs_id:
        print("❌ No hay vector store configurado.")
        return
    
    # Tests de ejemplo - personalizar según tu documentación
    tests = [
        {"q": "Do I have to pay customs or fees?", 
         "must_contain": ["no"]},
        {"q": "What is the return period?", 
         "must_contain": ["14 days"]},
        {"q": "How much is shipping under £112?", 
         "must_contain": ["6.99"]},
    ]
    
    print("=" * 70)
    print("🧪 TEST: Validación del Sistema RAG")
    print("=" * 70)
    
    run_test_suite(vs_id, tests)


def action_interactive(vs_id: Optional[str] = None) -> None:
    """
    Modo interactivo para hacer preguntas.
    """
    if not vs_id:
        config = load_config()
        vs_id = config.get("vector_store_id")
    
    if not vs_id:
        print("❌ No hay vector store configurado.")
        return
    
    print("=" * 70)
    print("🤖 MODO INTERACTIVO")
    print("=" * 70)
    print("Escribe tus preguntas. Escribe 'salir' para terminar.\n")
    
    assistant = RAGAssistant(vs_id)
    
    while True:
        try:
            question = input("❓ Tu pregunta: ").strip()
            
            if question.lower() in ['salir', 'exit', 'quit', 'q']:
                print("👋 ¡Hasta luego!")
                break
            
            if not question:
                continue
            
            response = assistant.answer(question)
            print(f"\n💡 Respuesta: {response.answer}")
            print(f"📚 Fuentes: {', '.join(response.sources)}\n")
            
        except KeyboardInterrupt:
            print("\n👋 ¡Hasta luego!")
            break


def action_status() -> None:
    """
    Muestra el estado actual de la configuración.
    """
    print("=" * 70)
    print("📊 STATUS: Estado del Sistema")
    print("=" * 70)
    
    config = load_config()
    vs_id = config.get("vector_store_id")
    
    if vs_id:
        print(f"\n✓ Vector Store configurado: {vs_id}")
        try:
            vs = get_vector_store(vs_id)
        except Exception as e:
            print(f"  ⚠ Error al obtener info: {e}")
    else:
        print("\n⚠ No hay Vector Store configurado")
        print("  Ejecuta: python main.py --action setup")
    
    print("\n📋 Vector Stores disponibles:")
    list_vector_stores(limit=5)


# =============================================================================
# PUNTO DE ENTRADA
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Gestión de Knowledge Base con OpenAI Vector Stores",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python main.py --action setup --pattern "docs/*.md"
  python main.py --action search --query "return policy"
  python main.py --action ask --question "What is the shipping cost?"
  python main.py --action interactive
  python main.py --action test
  python main.py --action status
        """
    )
    
    parser.add_argument(
        "--action", "-a",
        choices=["setup", "search", "ask", "test", "interactive", "status"],
        required=True,
        help="Acción a ejecutar"
    )
    
    parser.add_argument(
        "--name", "-n",
        default="Knowledge Base",
        help="Nombre del vector store (para setup)"
    )
    
    parser.add_argument(
        "--pattern", "-p",
        default="docs/**/*.md",
        help="Patrón glob de archivos a subir (para setup)"
    )
    
    parser.add_argument(
        "--vs-id", "-v",
        default=None,
        help="ID del vector store (opcional, usa guardado por defecto)"
    )
    
    parser.add_argument(
        "--query", "-q",
        default=None,
        help="Consulta de búsqueda (para search)"
    )
    
    parser.add_argument(
        "--question",
        default=None,
        help="Pregunta para el asistente (para ask)"
    )
    
    args = parser.parse_args()
    
    # Validar conexión
    print("Verificando conexión con OpenAI...")
    validate_connection()
    print("✓ Conexión OK\n")
    
    # Ejecutar acción
    if args.action == "setup":
        action_setup(args.name, args.pattern, args.vs_id)
    
    elif args.action == "search":
        if not args.query:
            args.query = input("Ingresa tu consulta de búsqueda: ")
        action_search(args.query, args.vs_id)
    
    elif args.action == "ask":
        if not args.question:
            args.question = input("Ingresa tu pregunta: ")
        action_ask(args.question, args.vs_id)
    
    elif args.action == "test":
        action_test(args.vs_id)
    
    elif args.action == "interactive":
        action_interactive(args.vs_id)
    
    elif args.action == "status":
        action_status()


if __name__ == "__main__":
    main()
