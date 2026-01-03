#!/usr/bin/env python3
"""
rag_assistant.py - Asistente RAG (Retrieval Augmented Generation)
===================================================================

Este módulo implementa un sistema RAG completo que:
1. Busca información relevante en el Vector Store
2. Construye un prompt con el contexto encontrado
3. Genera una respuesta usando GPT

¿Qué es RAG?
------------
Retrieval Augmented Generation es una técnica que mejora las respuestas
de un LLM al proporcionarle información específica y actualizada de
una base de conocimiento antes de responder.

Flujo RAG:
    Usuario pregunta → Buscar en KB → Contexto relevante → GPT + Contexto → Respuesta

Ventajas:
    - Respuestas basadas en tu documentación específica
    - Reducción de alucinaciones
    - Información actualizada (no limitada al training del modelo)
    - Trazabilidad (sabes de dónde viene la info)

Ejemplo de uso:
---------------
    from rag_assistant import RAGAssistant
    
    assistant = RAGAssistant(vector_store_id="vs_123...")
    
    response = assistant.answer("What is the return policy?")
    print(response)

Autor: [Tu nombre]
Fecha: 2025
"""

from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass

from openai import OpenAI

from config import client, DEFAULT_MODEL, MAX_CONTEXT_CHARS, DEFAULT_SEARCH_RESULTS
from vector_search import search_vector_store, extract_context


# =============================================================================
# CONFIGURACIÓN DE PROMPTS
# =============================================================================

DEFAULT_SYSTEM_PROMPT = """You are a helpful customer service assistant.
Answer questions using ONLY the provided knowledge base context.
If the information is not in the context, say "I don't have that information in my knowledge base."
Be concise, accurate, and friendly."""

SPANISH_SYSTEM_PROMPT = """Eres un asistente de servicio al cliente útil.
Responde las preguntas usando ÚNICAMENTE el contexto proporcionado.
Si la información no está en el contexto, di "No tengo esa información en mi base de conocimiento."
Sé conciso, preciso y amable."""


# =============================================================================
# DATACLASS PARA RESPUESTAS
# =============================================================================

@dataclass
class RAGResponse:
    """
    Estructura de respuesta del asistente RAG.
    
    Attributes:
        answer: La respuesta generada por el modelo
        context: El contexto usado para generar la respuesta
        sources: Lista de archivos fuente usados
        query: La pregunta original
        model: Modelo usado para la respuesta
        search_results: Resultados raw de la búsqueda
    """
    answer: str
    context: str
    sources: List[str]
    query: str
    model: str
    search_results: Dict[str, Any]


# =============================================================================
# CLASE PRINCIPAL: RAG ASSISTANT
# =============================================================================

class RAGAssistant:
    """
    Asistente RAG que combina búsqueda vectorial con generación de respuestas.
    
    Esta clase encapsula todo el flujo RAG:
    1. Recibe una pregunta del usuario
    2. Busca contexto relevante en el Vector Store
    3. Construye un prompt con el contexto
    4. Genera una respuesta usando GPT
    
    Attributes:
        vector_store_id: ID del vector store a usar
        model: Modelo de OpenAI para respuestas
        system_prompt: Instrucciones del sistema
        max_results: Número de chunks a recuperar
        max_context_chars: Límite de caracteres del contexto
    
    Ejemplo básico:
        >>> assistant = RAGAssistant("vs_6932899d...")
        >>> response = assistant.answer("What is the return policy?")
        >>> print(response.answer)
        You can return items within 14 days...
    
    Ejemplo con configuración personalizada:
        >>> assistant = RAGAssistant(
        ...     vector_store_id="vs_123...",
        ...     model="gpt-4.1",
        ...     system_prompt="Responde siempre en español...",
        ...     max_results=3
        ... )
    """
    
    def __init__(
        self,
        vector_store_id: str,
        model: str = DEFAULT_MODEL,
        system_prompt: str = DEFAULT_SYSTEM_PROMPT,
        max_results: int = DEFAULT_SEARCH_RESULTS,
        max_context_chars: int = MAX_CONTEXT_CHARS
    ):
        """
        Inicializa el asistente RAG.
        
        Args:
            vector_store_id: ID del vector store con la knowledge base
            model: Modelo de OpenAI a usar (default: gpt-4.1)
            system_prompt: Instrucciones del sistema para el modelo
            max_results: Número de chunks a recuperar por búsqueda
            max_context_chars: Límite de caracteres del contexto
        """
        self.vector_store_id = vector_store_id
        self.model = model
        self.system_prompt = system_prompt
        self.max_results = max_results
        self.max_context_chars = max_context_chars
        self.client = client
    
    def search(self, query: str) -> Tuple[str, Dict[str, Any]]:
        """
        Busca contexto relevante para una query.
        
        Args:
            query: Pregunta o consulta del usuario
        
        Returns:
            Tuple[str, Dict]: (contexto_formateado, resultados_raw)
        """
        # Realizar búsqueda
        search_results = search_vector_store(
            vector_store_id=self.vector_store_id,
            query=query,
            max_results=self.max_results
        )
        
        # Extraer contexto formateado
        context = extract_context(
            search_results,
            max_chars=self.max_context_chars
        )
        
        return context, search_results
    
    def answer(
        self,
        query: str,
        additional_context: Optional[str] = None,
        temperature: float = 0.7
    ) -> RAGResponse:
        """
        Genera una respuesta a una pregunta usando RAG.
        
        Flujo:
        1. Busca contexto relevante en el vector store
        2. Construye mensajes con el contexto
        3. Genera respuesta con el modelo
        
        Args:
            query: Pregunta del usuario
            additional_context: Contexto adicional opcional (ej: historial)
            temperature: Creatividad de la respuesta (0.0-2.0)
        
        Returns:
            RAGResponse: Objeto con respuesta, contexto y metadatos
        
        Ejemplo:
            >>> response = assistant.answer("How much is shipping?")
            >>> print(response.answer)
            Shipping costs £6.99 for orders under £112. 
            Orders over £112 qualify for free shipping.
            
            >>> print(response.sources)
            ['faq_shipping_delivery.md']
        """
        # 1. Buscar contexto
        context, search_results = self.search(query)
        
        # Extraer fuentes
        sources = [
            hit.get("filename", "unknown")
            for hit in search_results.get("data", [])
        ]
        
        # 2. Construir mensajes
        messages = [
            {"role": "system", "content": self.system_prompt}
        ]
        
        # Agregar contexto de KB
        if context:
            messages.append({
                "role": "system",
                "content": f"KNOWLEDGE BASE CONTEXT:\n{context}"
            })
        
        # Agregar contexto adicional si existe
        if additional_context:
            messages.append({
                "role": "system",
                "content": f"ADDITIONAL CONTEXT:\n{additional_context}"
            })
        
        # Agregar pregunta del usuario
        messages.append({"role": "user", "content": query})
        
        # 3. Generar respuesta
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature
        )
        
        answer_text = completion.choices[0].message.content
        
        return RAGResponse(
            answer=answer_text,
            context=context,
            sources=sources,
            query=query,
            model=self.model,
            search_results=search_results
        )
    
    def answer_with_history(
        self,
        query: str,
        conversation_history: List[Dict[str, str]],
        temperature: float = 0.7
    ) -> RAGResponse:
        """
        Genera respuesta considerando historial de conversación.
        
        Útil para chatbots con memoria de contexto conversacional.
        
        Args:
            query: Pregunta actual del usuario
            conversation_history: Lista de mensajes previos
                                 [{"role": "user", "content": "..."},
                                  {"role": "assistant", "content": "..."}]
            temperature: Creatividad de la respuesta
        
        Returns:
            RAGResponse: Respuesta con contexto
        
        Ejemplo:
            >>> history = [
            ...     {"role": "user", "content": "What's your return policy?"},
            ...     {"role": "assistant", "content": "You can return within 14 days..."}
            ... ]
            >>> response = assistant.answer_with_history(
            ...     "What about international orders?",
            ...     history
            ... )
        """
        # Buscar contexto
        context, search_results = self.search(query)
        sources = [h.get("filename", "") for h in search_results.get("data", [])]
        
        # Construir mensajes
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "system", "content": f"KNOWLEDGE BASE CONTEXT:\n{context}"}
        ]
        
        # Agregar historial
        messages.extend(conversation_history)
        
        # Agregar nueva pregunta
        messages.append({"role": "user", "content": query})
        
        # Generar
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature
        )
        
        return RAGResponse(
            answer=completion.choices[0].message.content,
            context=context,
            sources=sources,
            query=query,
            model=self.model,
            search_results=search_results
        )


# =============================================================================
# FUNCIONES DE CONVENIENCIA
# =============================================================================

def quick_answer(
    vector_store_id: str,
    query: str,
    model: str = DEFAULT_MODEL
) -> str:
    """
    Función rápida para obtener una respuesta sin crear instancia.
    
    Args:
        vector_store_id: ID del vector store
        query: Pregunta del usuario
        model: Modelo a usar
    
    Returns:
        str: Respuesta del asistente
    
    Ejemplo:
        >>> answer = quick_answer("vs_123...", "What is your return policy?")
        >>> print(answer)
        You can return items within 14 days...
    """
    assistant = RAGAssistant(vector_store_id, model=model)
    response = assistant.answer(query)
    return response.answer


# =============================================================================
# TESTING / EVALUACIÓN
# =============================================================================

def run_test_suite(
    vector_store_id: str,
    test_cases: List[Dict[str, Any]],
    model: str = DEFAULT_MODEL
) -> Dict[str, Any]:
    """
    Ejecuta una suite de tests contra el RAG assistant.
    
    Útil para evaluar la calidad de las respuestas y el retrieval.
    
    Args:
        vector_store_id: ID del vector store
        test_cases: Lista de casos de prueba con formato:
                   [{"q": "pregunta", "must_contain": ["keyword1", "keyword2"]}, ...]
        model: Modelo a usar
    
    Returns:
        Dict con resultados: {"passed": int, "failed": int, "details": [...]}
    
    Ejemplo:
        >>> tests = [
        ...     {"q": "Return period?", "must_contain": ["14 days"]},
        ...     {"q": "Shipping cost?", "must_contain": ["£6.99"]},
        ... ]
        >>> results = run_test_suite("vs_123...", tests)
        >>> print(f"Passed: {results['passed']}/{results['total']}")
    """
    assistant = RAGAssistant(vector_store_id, model=model)
    
    results = {
        "passed": 0,
        "failed": 0,
        "total": len(test_cases),
        "details": []
    }
    
    for test in test_cases:
        query = test["q"]
        must_contain = test.get("must_contain", [])
        
        print(f"\n📝 Testing: {query}")
        
        response = assistant.answer(query)
        answer_lower = response.answer.lower()
        
        # Verificar que contiene las keywords esperadas
        passed = all(
            keyword.lower() in answer_lower
            for keyword in must_contain
        )
        
        if passed:
            results["passed"] += 1
            status = "✓ PASSED"
        else:
            results["failed"] += 1
            status = "✗ FAILED"
        
        print(f"   {status}")
        print(f"   Answer: {response.answer[:100]}...")
        
        results["details"].append({
            "query": query,
            "passed": passed,
            "answer": response.answer,
            "sources": response.sources
        })
    
    print(f"\n{'='*50}")
    print(f"Results: {results['passed']}/{results['total']} passed")
    print(f"{'='*50}")
    
    return results


# =============================================================================
# EJECUCIÓN DIRECTA (demostración)
# =============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("Demo: RAG Assistant")
    print("=" * 70)
    
    # Configurar tu VS_ID aquí
    DEMO_VS_ID = "vs_6932899d0eb481919e4ccdb6ac7487"
    
    # Tests de ejemplo
    demo_tests = [
        {"q": "Do I have to pay customs or fees?", "must_contain": ["no"]},
        {"q": "What is the return period?", "must_contain": ["14 days"]},
        {"q": "How much is shipping under £112?", "must_contain": ["£6.99"]},
    ]
    
    print("""
Uso básico:

    from rag_assistant import RAGAssistant
    
    # Crear asistente
    assistant = RAGAssistant(
        vector_store_id="vs_6932899d...",
        model="gpt-4.1"
    )
    
    # Hacer pregunta
    response = assistant.answer("What is your return policy?")
    
    # Acceder a respuesta y metadatos
    print(response.answer)      # Respuesta generada
    print(response.sources)     # Archivos fuente usados
    print(response.context)     # Contexto recuperado
""")
    
    # Intentar demo real
    try:
        print("\n🧪 Ejecutando tests de ejemplo...")
        print("-" * 50)
        
        results = run_test_suite(DEMO_VS_ID, demo_tests)
        
    except Exception as e:
        print(f"⚠ Demo no disponible: {e}")
        print("  Configura DEMO_VS_ID con un vector store válido")
    
    print("\n" + "=" * 70)
