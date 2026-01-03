# KnowledgeBase_Manager

### Estructura del Pryecto

```
openai_knowledge_base/
├── config.py               # Configuración y cliente OpenAI
├── vector_store_manager.py # Crear/gestionar vector stores
├── file_uploader.py        # Subir archivos a OpenAI
├── batch_manager.py        # Gestionar file batches
├── vector_search.py        # Búsqueda semántica
├── rag_assistant.py        # Asistente RAG completo
├── main.py                 # Script de orquestación
├── requirements.txt        # Dependencias
├── .env                    # Variables de entorno (no commitear)
├── .gitignore              # Ignorar .env y configs
└── docs/                   # Tus documentos a indexar
    ├── faq_customer_service.md
    ├── faq_products_care.md
    └── ...
```

### Uso Rápido
```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Configurar API key
export OPENAI_API_KEY="sk-proj-..."

# 3. Setup completo
python main.py --action setup --pattern "docs/*.md"

# 4. Modo interactivo
python main.py --action interactive

# 5. Ejecutar tests
python main.py --action test
```
