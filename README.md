# KnowledgeBase_Manager

Plataforma completa para gestionar Vector Stores con OpenAI. Incluye interfaz web moderna (TypeScript + React) y API REST (Python + FastAPI) para subir documentos, crear bases de conocimiento y hacer consultas con RAG.

## 🚀 Inicio Rápido

### Opción 1: Plataforma Web Completa (Recomendado)

```bash

# 1. Instala el módulo venv 
apt install python3-venv

# 2. Crea el entorno virtual
python3 -m venv venv

# 3. Activa el entorno virtual
source venv/bin/activate

# 4. Instalar dependencias Python
pip install -r requirements.txt

# 5. En otra terminal, instalar dependencias del frontend
cd frontend
npm install
cd ..

# 6. Iniciar toda la plataforma (backend + frontend)
./start_platform.sh
```

Abre http://localhost:3000 en tu navegador.

### Opción 2: Solo Backend API

```bash
# Iniciar solo el backend
./start_backend.sh
```

API disponible en http://localhost:8000

### Opción 3: CLI (Línea de Comandos)

```bash
# 1. Configurar API key
export OPENAI_API_KEY="sk-proj-..."

# 2. Setup completo
python main.py --action setup --pattern "docs/*.md"

# 3. Modo interactivo
python main.py --action interactive
```

## 📁 Estructura del Proyecto

```
KnowledgeBase_Manager/
├── Backend (Python + FastAPI)
│   ├── api.py                      # API REST principal
│   ├── config.py                   # Configuración OpenAI
│   ├── vector_store_manager.py     # Gestión de Vector Stores
│   ├── file_uploader.py            # Subida de archivos
│   ├── batch_manager.py            # Gestión de batches
│   ├── vector_search.py            # Búsqueda vectorial
│   ├── rag_assistant.py            # Asistente RAG
│   ├── main.py                     # CLI
│   └── requirements.txt            # Dependencias Python
│
├── Frontend (TypeScript + React + Vite)
│   ├── src/
│   │   ├── components/
│   │   │   ├── ConfigPanel.tsx
│   │   │   ├── FileUploader.tsx
│   │   │   ├── VectorStoreManager.tsx
│   │   │   └── ChatInterface.tsx
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   └── vite.config.ts
│
├── Scripts de Inicio
│   ├── start_platform.sh           # Inicia backend + frontend
│   ├── start_backend.sh            # Solo backend
│   └── start_frontend.sh           # Solo frontend
│
└── Documentación
    ├── README.md                   # Este archivo
    └── PLATFORM_README.md          # Documentación detallada
```

## ⚙️ Diagramass de Flujo de Trabajo

### 1. Arquitectura General de la API
```mermaid

flowchart TB
    subgraph Cliente["🖥️ Cliente (Frontend)"]
        UI[Interfaz Web]
    end

    subgraph API["⚡ FastAPI Backend"]
        direction TB
        CORS[CORS Middleware]
        
        subgraph Endpoints["Endpoints"]
            CONFIG["/api/config"]
            UPLOAD["/api/upload"]
            FILES["/api/files"]
            VS["/api/vector-store"]
            QUERY["/api/query"]
        end
        
        subgraph State["AppState"]
            CLIENT[OpenAI Client]
            APIKEY[API Key]
            VSID[Vector Store ID]
            UPLOADED[Uploaded Files]
        end
    end

    subgraph OpenAI["☁️ OpenAI API"]
        OFILES[Files API]
        OVS[Vector Stores API]
        OCHAT[Chat Completions]
    end

    UI --> CORS
    CORS --> Endpoints
    Endpoints --> State
    State --> OpenAI
```

### 2. Mapa de Endpoints
```mermaid

flowchart LR
    subgraph Config["⚙️ Configuración"]
        C1["POST /api/config"]
    end

    subgraph Files["📁 Archivos"]
        F1["POST /api/upload"]
        F2["GET /api/files"]
    end

    subgraph VectorStores["🗄️ Vector Stores"]
        VS1["POST /api/vector-store"]
        VS2["GET /api/vector-stores"]
        VS3["GET /api/status/{id}"]
        VS4["GET /{id}/files"]
        VS5["POST /{id}/add-files"]
        VS6["DELETE /{id}/files/{fid}"]
        VS7["GET /{id}/files/{fid}/content"]
        VS8["GET /{id}/batch/{bid}/status"]
    end

    subgraph Query["🔍 Consultas RAG"]
        Q1["POST /api/query"]
    end

    subgraph Health["💚 Salud"]
        H1["GET /"]
        H2["GET /health"]
    end

    C1 --> Files
    Files --> VectorStores
    VectorStores --> Query
```

### 3. Flujo de Trabajo Principal
```mermaid

sequenceDiagram
    autonumber
    participant U as 👤 Usuario
    participant API as ⚡ API
    participant OAI as ☁️ OpenAI

    rect rgb(240, 248, 255)
        Note over U,OAI: 1️⃣ Configuración
        U->>API: POST /api/config {api_key}
        API->>OAI: Validar API Key
        OAI-->>API: ✓ Válida
        API-->>U: {success: true}
    end

    rect rgb(255, 248, 240)
        Note over U,OAI: 2️⃣ Subida de Archivos
        U->>API: POST /api/upload (PDF/MD/TXT)
        API->>OAI: files.create()
        OAI-->>API: file_id
        API-->>U: {file_id, filename, size}
    end

    rect rgb(240, 255, 240)
        Note over U,OAI: 3️⃣ Crear Vector Store
        U->>API: POST /api/vector-store {name}
        API->>OAI: vector_stores.create()
        API->>OAI: file_batches.create(file_ids)
        OAI-->>API: vector_store_id
        API-->>U: {vector_store_id}
    end

    rect rgb(255, 240, 255)
        Note over U,OAI: 4️⃣ Consulta RAG
        U->>API: POST /api/query {query}
        API->>OAI: Vector Store Search
        OAI-->>API: Chunks relevantes
        API->>OAI: chat.completions.create()
        OAI-->>API: Respuesta generada
        API-->>U: {answer, sources, context}
    end
```

### 4. Flujo de Consulta RAG Detallado
```mermaid

flowchart TD
    A[📝 Query del Usuario] --> B{¿API Key configurada?}
    B -->|No| C[❌ Error 400]
    B -->|Sí| D{¿Vector Store existe?}
    D -->|No| E[❌ Error 400]
    D -->|Sí| F[🔍 Búsqueda en Vector Store]
    
    F --> G[Obtener Top 10 Chunks]
    G --> H{¿Hay contexto?}
    
    H -->|No| I[📭 Sin información relevante]
    H -->|Sí| J[📦 Construir Contexto]
    
    J --> K[🧠 System Prompt + Contexto]
    K --> L[🤖 Chat Completion]
    L --> M[✅ Respuesta con Sources]
    
    I --> N[Retornar QueryResponse]
    M --> N
```

### 5. Estados del Vector Store

```mermaid
stateDiagram-v2
    [*] --> SinConfigurar: Inicio
    
    SinConfigurar --> Configurado: POST /api/config
    
    Configurado --> ArchivosSubidos: POST /api/upload
    
    ArchivosSubidos --> ArchivosSubidos: Más uploads
    
    ArchivosSubidos --> Indexando: POST /api/vector-store
    
    Indexando --> Listo: Batch completado
    Indexando --> Error: Fallo en indexación
    
    Listo --> Consultando: POST /api/query
    Consultando --> Listo: Respuesta generada
    
    Listo --> Indexando: POST /{id}/add-files
    
    Error --> ArchivosSubidos: Reintentar
```

### 6. Modelos de Datos
```mermaid

classDiagram
    class ConfigRequest {
        +str api_key
    }
    
    class ConfigResponse {
        +bool success
        +str message
    }
    
    class VectorStoreRequest {
        +str name
    }
    
    class VectorStoreResponse {
        +bool success
        +str vector_store_id
        +str message
    }
    
    class QueryRequest {
        +str query
        +str vector_store_id?
        +str model
    }
    
    class QueryResponse {
        +bool success
        +str answer
        +List~str~ sources
        +str context
    }
    
    class FileInfo {
        +str file_id
        +str filename
        +int size
        +str uploaded_at
    }
    
    class StatusResponse {
        +str vector_store_id?
        +str vector_store_name?
        +int file_count
        +str status
    }
    
    class AppState {
        +OpenAI client
        +str api_key
        +str vector_store_id
        +List~Dict~ uploaded_files
    }

    ConfigRequest --> ConfigResponse : genera
    VectorStoreRequest --> VectorStoreResponse : genera
    QueryRequest --> QueryResponse : genera
```

### 7. Gestión de Archivos en Vector Store
```mermaid

flowchart TD
    subgraph Upload["📤 Subida"]
        A[Usuario sube archivo] --> B{Extensión válida?}
        B -->|.pdf .md .txt| C[Subir a OpenAI Files API]
        B -->|Otra| D[❌ Error 400]
        C --> E[Guardar en state.uploaded_files]
    end

    subgraph Index["📇 Indexación"]
        E --> F[Crear Vector Store]
        F --> G[Crear File Batch]
        G --> H[Indexación en progreso]
        H --> I{Batch status?}
        I -->|completed| J[✅ Listo para consultas]
        I -->|in_progress| H
        I -->|failed| K[❌ Revisar errores]
    end

    subgraph Manage["🔧 Gestión"]
        J --> L[Listar archivos]
        J --> M[Agregar más archivos]
        J --> N[Eliminar archivos]
        J --> O[Ver contenido]
    end
```

### 8. Arquitectura de Componentes
```mermaid

flowchart TB
    subgraph Frontend["🖥️ Frontend"]
        WEB[Aplicación Web]
    end

    subgraph Backend["⚡ FastAPI Backend"]
        direction TB
        
        subgraph Middleware
            CORS[CORS]
            LOG[Logging]
        end
        
        subgraph Controllers["Controladores"]
            CFG[Config Controller]
            FILE[File Controller]
            VS[VectorStore Controller]
            QRY[Query Controller]
        end
        
        subgraph Models["Modelos Pydantic"]
            REQ[Request Models]
            RES[Response Models]
        end
        
        subgraph State["Estado Global"]
            APP[AppState]
        end
    end

    subgraph External["☁️ Servicios Externos"]
        OPENAI[OpenAI API]
    end

    WEB <-->|HTTP/REST| Middleware
    Middleware --> Controllers
    Controllers --> Models
    Controllers --> State
    State <-->|SDK| OPENAI
```

## 🎯 Características

### Plataforma Web
- ✅ Interfaz moderna y responsive
- ✅ Configuración de OpenAI API Key
- ✅ Carga de archivos drag & drop (PDF, MD, TXT)
- ✅ Creación automática de Vector Stores
- ✅ Chat interactivo con RAG
- ✅ Visualización de fuentes consultadas

### API REST
- ✅ Endpoints completos para gestión
- ✅ Subida de archivos multipart
- ✅ Creación de Vector Stores
- ✅ Búsqueda vectorial
- ✅ Consultas RAG con GPT-5+
- ✅ CORS configurado

### CLI
- ✅ Setup automatizado
- ✅ Modo interactivo
- ✅ Tests de validación
- ✅ Búsqueda y consultas

## ⚙️ Documentación Completa

Ver [PLATFORM_README.md](PLATFORM_README.md) para:
- Guía de instalación detallada
- Documentación de API endpoints
- Ejemplos de uso
- Solución de problemas
- Arquitectura del sistema

## 🛠️ Requisitos

- Python 3.8+
- Node.js 16+
- OpenAI API Key (con acceso a GPT-5 o superior)

## 📖 Uso de la Plataforma Web

1. **Configurar API Key**: Ingresa tu OpenAI API key
2. **Subir Archivos**: Arrastra o selecciona archivos PDF/MD/TXT
3. **Crear Vector Store**: Dale un nombre a tu base de conocimiento
4. **Hacer Consultas**: Pregunta sobre el contenido de tus documentos

## 💡 Ejemplos de Consultas

- "¿Cuál es la política de devoluciones?"
- "¿Cuánto cuesta el envío?"
- "¿Qué productos tienen garantía extendida?"
- "Resume las características principales"

## 🔧 Desarrollo

### Backend
```bash
# Instalar dependencias
pip install -r requirements.txt

# Iniciar con hot-reload
uvicorn api:app --reload --port 8000
```

### Frontend
```bash
cd frontend

# Instalar dependencias
npm install

# Iniciar con hot-reload
npm run dev
```

## 📝 Licencia

Código abierto - Uso libre

---

**Desarrollado con OpenAI API + FastAPI + React + TypeScript**
