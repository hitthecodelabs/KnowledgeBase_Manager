#!/usr/bin/env python3
"""
vector_search.py - Búsqueda Semántica en Vector Stores
=======================================================

Este módulo proporciona funcionalidades para realizar búsquedas
semánticas en Vector Stores de OpenAI.

¿Cómo funciona la búsqueda?
---------------------------
1. Envías una query (pregunta o texto)
2. OpenAI genera un embedding de la query
3. Busca los chunks más similares en el vector store
4. Retorna los K resultados más relevantes con scores

Estructura del resultado:
    {
        "data": [
            {
                "file_id": "file-abc123",
                "filename": "faq.md",
                "score": 0.87,
                "content": [
                    {"type": "text", "text": "...contenido del chunk..."}
                ]
            },
            ...
        ]
    }

Ejemplo de uso:
---------------
    from vector_search import search_vector_store, extract_context
    
    # Buscar
    hits = search_vector_store("vs_123...", "¿Cuál es la política de devolución?")
    
    # Extraer contexto
    context = extract_context(hits, max_chars=4000)

Autor: [Tu nombre]
Fecha: 2025
"""

import httpx
from typing import List, Dict, Any, Optional, Tuple

from config import client, OPENAI_API_KEY, DEFAULT_SEARCH_RESULTS, MAX_CONTEXT_CHARS


# =============================================================================
# BÚSQUEDA EN VECTOR STORE
# =============================================================================

def search_vector_store(
    vector_store_id: str,
    query: str,
    max_results: int = DEFAULT_SEARCH_RESULTS,
    score_threshold: Optional[float] = None
) -> Dict[str, Any]:
    """
    Realiza una búsqueda semántica en un Vector Store.
    
    Envía la query al endpoint de búsqueda de OpenAI, que genera
    embeddings y encuentra los chunks más similares semánticamente.
    
    Args:
        vector_store_id: ID del vector store a buscar.
                        Formato: vs_XXXXXXXXXXXX
        
        query: Texto de búsqueda (pregunta o consulta).
              Ejemplos:
              - "What is the return policy?"
              - "How much does shipping cost?"
              - "¿Cuáles son los materiales sostenibles?"
        
        max_results: Número máximo de resultados (default: 5).
                    Más resultados = más contexto pero más tokens.
        
        score_threshold: Filtrar resultados por score mínimo.
                        Rango: 0.0 a 1.0 (mayor = más relevante)
                        None = sin filtro
    
    Returns:
        Dict con estructura:
        {
            "data": [
                {
                    "file_id": str,      # ID del archivo fuente
                    "filename": str,      # Nombre del archivo
                    "score": float,       # Relevancia (0-1)
                    "content": [          # Chunks de texto
                        {"type": "text", "text": str}
                    ],
                    "attributes": dict    # Metadatos adicionales
                },
                ...
            ],
            "has_more": bool,
            "next_page": str | None
        }
    
    Ejemplo:
        >>> hits = search_vector_store(
        ...     "vs_6932899d...",
        ...     "Do I have to pay customs or fees?",
        ...     max_results=5
        ... )
        🔍 Buscando: "Do I have to pay customs or fees?"
        ✓ Encontrados 5 resultados
        
        >>> for h in hits["data"]:
        ...     print(f"{h['score']:.2f} - {h['filename']}")
        0.89 - faq_shipping_delivery.md
        0.82 - faq_payment.md
        0.76 - faq_order.md
    
    Notas:
        - Esta función usa httpx directamente (API endpoint)
        - El header OpenAI-Beta es necesario para Assistants v2
        - Los scores son normalizados entre 0 y 1
    """
    print(f'🔍 Buscando: "{query[:50]}..."' if len(query) > 50 else f'🔍 Buscando: "{query}"')
    
    # Construir URL y headers
    url = f"https://api.openai.com/v1/vector_stores/{vector_store_id}/search"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
        "OpenAI-Beta": "assistants=v2"
    }
    
    # Payload de búsqueda
    payload = {
        "query": query,
        "max_num_results": max_results
    }
    
    # Realizar búsqueda
    response = httpx.post(url, headers=headers, json=payload, timeout=30)
    response.raise_for_status()
    
    results = response.json()
    
    # Filtrar por threshold si se especificó
    if score_threshold and "data" in results:
        results["data"] = [
            h for h in results["data"]
            if h.get("score", 0) >= score_threshold
        ]
    
    num_results = len(results.get("data", []))
    print(f"✓ Encontrados {num_results} resultados")
    
    return results


# =============================================================================
# EXTRAER TEXTO DE RESULTADOS
# =============================================================================

def extract_text_from_hit(hit: Dict[str, Any]) -> str:
    """
    Extrae el texto de un único resultado de búsqueda.
    
    Los resultados tienen una estructura de "content" que puede
    contener múltiples partes de texto. Esta función las combina.
    
    Args:
        hit: Un elemento de la lista "data" del resultado de búsqueda
    
    Returns:
        str: Texto combinado del chunk
    
    Ejemplo:
        >>> hit = {
        ...     "content": [
        ...         {"type": "text", "text": "Párrafo 1..."},
        ...         {"type": "text", "text": "Párrafo 2..."}
        ...     ]
        ... }
        >>> text = extract_text_from_hit(hit)
        >>> print(text)
        Párrafo 1...
        Párrafo 2...
    """
    parts = hit.get("content", [])
    texts = []
    
    for part in parts:
        if isinstance(part, dict):
            # Intentar obtener texto de diferentes formatos
            if "text" in part:
                texts.append(part["text"])
            elif part.get("type") == "text" and "text" in part:
                texts.append(part["text"])
    
    return "\n".join(texts).strip()


# =============================================================================
# EXTRAER CONTEXTO FORMATEADO
# =============================================================================

def extract_context(
    search_results: Dict[str, Any],
    max_chars: int = MAX_CONTEXT_CHARS,
    include_source: bool = True,
    separator: str = "\n\n---\n\n"
) -> str:
    """
    Extrae y formatea el contexto de los resultados de búsqueda.
    
    Combina todos los chunks encontrados en un string formateado
    listo para usar como contexto en un prompt de LLM.
    
    Args:
        search_results: Resultado de search_vector_store()
        max_chars: Límite de caracteres (protección de tokens)
        include_source: Si True, incluye referencia a archivo fuente
        separator: Separador entre chunks
    
    Returns:
        str: Contexto formateado y truncado
    
    Ejemplo:
        >>> hits = search_vector_store(vs_id, "return policy")
        >>> context = extract_context(hits, max_chars=4000)
        >>> print(context)
        [KB#1 - faq_returns.md]
        You can return items within 14 days...
        
        ---
        
        [KB#2 - policy_summary.md]
        Our return policy allows...
    """
    snippets: List[str] = []
    
    for i, hit in enumerate(search_results.get("data", []), start=1):
        text = extract_text_from_hit(hit)
        
        if not text:
            continue
        
        if include_source:
            filename = hit.get("filename", "unknown")
            score = hit.get("score", 0)
            header = f"[KB#{i} - {filename} (score: {score:.2f})]"
            snippets.append(f"{header}\n{text}")
        else:
            snippets.append(f"[KB#{i}]\n{text}")
    
    # Combinar y truncar
    context = separator.join(snippets)
    
    if len(context) > max_chars:
        context = context[:max_chars] + "\n\n[... truncado por límite de tokens ...]"
    
    return context


# =============================================================================
# BÚSQUEDA CON SNIPPETS (función de conveniencia)
# =============================================================================

def search_and_extract(
    vector_store_id: str,
    query: str,
    max_results: int = 5,
    max_chars: int = MAX_CONTEXT_CHARS
) -> Tuple[str, Dict[str, Any]]:
    """
    Función de conveniencia que busca y extrae contexto en un solo paso.
    
    Args:
        vector_store_id: ID del vector store
        query: Consulta de búsqueda
        max_results: Número máximo de resultados
        max_chars: Límite de caracteres del contexto
    
    Returns:
        Tuple[str, Dict]: (contexto_formateado, resultados_raw)
    
    Ejemplo:
        >>> context, raw_hits = search_and_extract(
        ...     "vs_123...",
        ...     "What is the shipping cost?",
        ...     max_results=3
        ... )
        >>> print(context[:200])
        [KB#1 - faq_shipping.md (score: 0.91)]
        Shipping costs £6.99 for orders under £112...
    """
    hits = search_vector_store(vector_store_id, query, max_results)
    context = extract_context(hits, max_chars)
    return context, hits


# =============================================================================
# MOSTRAR RESULTADOS (debug/exploración)
# =============================================================================

def display_results(search_results: Dict[str, Any]) -> None:
    """
    Muestra los resultados de búsqueda de forma legible.
    
    Útil para debugging y exploración de qué está encontrando
    la búsqueda semántica.
    
    Args:
        search_results: Resultado de search_vector_store()
    
    Ejemplo:
        >>> hits = search_vector_store(vs_id, "shipping")
        >>> display_results(hits)
        
        ═══════════════════════════════════════════════════════
        Resultado #1 (Score: 0.91)
        Archivo: faq_shipping_delivery.md
        ───────────────────────────────────────────────────────
        We offer free shipping on orders over £112. For orders
        under £112, shipping costs £6.99...
        ═══════════════════════════════════════════════════════
    """
    data = search_results.get("data", [])
    
    if not data:
        print("No se encontraron resultados")
        return
    
    for i, hit in enumerate(data, start=1):
        score = hit.get("score", 0)
        filename = hit.get("filename", "unknown")
        text = extract_text_from_hit(hit)
        
        print("\n" + "═" * 60)
        print(f"Resultado #{i} (Score: {score:.3f})")
        print(f"Archivo: {filename}")
        print("─" * 60)
        
        # Truncar texto muy largo para display
        if len(text) > 500:
            print(text[:500] + "...")
        else:
            print(text)
    
    print("═" * 60)


# =============================================================================
# EJECUCIÓN DIRECTA (demostración)
# =============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("Demo: Vector Search")
    print("=" * 70)
    
    # Para demo real, configura tu VS_ID
    DEMO_VS_ID = "vs_6932899d0eb481919e4ccdb6ac7487"  # Reemplaza con tu ID
    
    demo_queries = [
        "Do I have to pay customs or fees?",
        "What is the return period?",
        "How much is shipping under £112?"
    ]
    
    print(f"""
Para usar este módulo:

    from vector_search import search_and_extract, display_results
    
    # Búsqueda simple
    context, hits = search_and_extract(
        vector_store_id="{DEMO_VS_ID}",
        query="What is your return policy?"
    )
    
    # Ver resultados
    display_results(hits)
    
    # Usar contexto en un prompt
    print(context)
""")
    
    # Intentar demo real si el VS existe
    try:
        print("\n🧪 Probando búsqueda de ejemplo...")
        context, hits = search_and_extract(
            DEMO_VS_ID,
            "Do I have to pay customs or fees?",
            max_results=3
        )
        display_results(hits)
    except Exception as e:
        print(f"⚠ Demo no disponible: {e}")
        print("  (Configura un VS_ID válido para probar)")
    
    print("\n" + "=" * 70)
