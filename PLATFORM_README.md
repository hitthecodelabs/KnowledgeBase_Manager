# Vector Store Platform - Documentación Completa

## Descripción

Plataforma web completa para gestionar Vector Stores con OpenAI. Permite subir documentos (PDF, MD, TXT), crear bases de conocimiento vectoriales y hacer consultas usando RAG (Retrieval Augmented Generation) con modelos GPT-4 o superiores.

## Arquitectura

### Backend (Python + FastAPI)
- **Framework**: FastAPI
- **Puerto**: 8000
- **Archivo principal**: `api.py`
- **Características**:
  - API REST completa
  - Gestión de OpenAI API key
  - Subida de archivos a OpenAI
  - Creación y gestión de Vector Stores
  - Consultas RAG con búsqueda vectorial
  - CORS habilitado para desarrollo

### Frontend (TypeScript + React + Vite)
- **Framework**: React 18 con TypeScript
- **Build tool**: Vite
- **Puerto**: 3000
- **Características**:
  - Interfaz moderna y responsive
  - Configuración de API key
  - Carga de archivos drag & drop
  - Gestión de Vector Stores
  - Chat interactivo con RAG
  - Proxy a backend configurado

## Instalación y Configuración

### 1. Requisitos Previos

- Python 3.8+
- Node.js 16+
- npm o yarn
- OpenAI API Key (con acceso a GPT-4 o superior)

### 2. Configuración del Backend

```bash
# Navegar al directorio raíz
cd KnowledgeBase_Manager

# Instalar dependencias Python
pip install -r requirements.txt

# Iniciar el servidor FastAPI
python api.py
```

El servidor estará disponible en: `http://localhost:8000`

### 3. Configuración del Frontend

```bash
# Navegar al directorio frontend
cd frontend

# Instalar dependencias
npm install

# Iniciar servidor de desarrollo
npm run dev
```

El frontend estará disponible en: `http://localhost:3000`

## Uso de la Plataforma

### Paso 1: Configurar OpenAI API Key

1. Abre la aplicación en `http://localhost:3000`
2. En la pantalla inicial, ingresa tu OpenAI API Key
3. Click en "Configurar API Key"
4. La aplicación validará la key y te dará acceso a las funciones

### Paso 2: Subir Archivos

1. En la sección "Subir Archivos":
   - Click en el área de carga
   - Selecciona uno o más archivos (.pdf, .md, .txt)
   - Los archivos se subirán automáticamente a OpenAI
2. Verás la lista de archivos subidos con su tamaño

### Paso 3: Crear Vector Store

1. En la sección "Vector Store":
   - Ingresa un nombre descriptivo (ej: "FAQ de Soporte")
   - Click en "Crear Vector Store"
   - El sistema creará el Vector Store e indexará los archivos
2. La indexación puede tardar unos segundos dependiendo del tamaño

### Paso 4: Hacer Consultas

1. Una vez creado el Vector Store, aparecerá la sección "Chat"
2. Escribe tu pregunta en el campo de texto
3. El sistema:
   - Buscará información relevante en los documentos
   - Generará una respuesta con GPT-4
   - Mostrará las fuentes consultadas
4. Puedes hacer múltiples preguntas en secuencia

## Endpoints de la API

### Configuración

#### `POST /api/config`
Configurar OpenAI API key

**Request:**
```json
{
  "api_key": "sk-proj-..."
}
```

**Response:**
```json
{
  "success": true,
  "message": "API key configurada correctamente"
}
```

### Archivos

#### `POST /api/upload`
Subir un archivo (multipart/form-data)

**Response:**
```json
{
  "success": true,
  "file_id": "file-XXX",
  "filename": "documento.pdf",
  "size": 12345
}
```

#### `GET /api/files`
Listar archivos subidos

**Response:**
```json
[
  {
    "file_id": "file-XXX",
    "filename": "documento.pdf",
    "size": 12345,
    "uploaded_at": "2025-01-03T10:00:00"
  }
]
```

### Vector Stores

#### `POST /api/vector-store`
Crear Vector Store con archivos subidos

**Request:**
```json
{
  "name": "Mi Knowledge Base"
}
```

**Response:**
```json
{
  "success": true,
  "vector_store_id": "vs_XXX",
  "message": "Vector Store creado. Indexando 3 archivos..."
}
```

#### `GET /api/vector-stores`
Listar todos los Vector Stores

#### `GET /api/status/{vector_store_id}`
Obtener estado de un Vector Store

### Consultas

#### `POST /api/query`
Hacer consulta RAG

**Request:**
```json
{
  "query": "¿Cuál es la política de devoluciones?",
  "vector_store_id": "vs_XXX",
  "model": "gpt-4.1"
}
```

**Response:**
```json
{
  "success": true,
  "answer": "Según nuestra política...",
  "sources": ["faq.md", "politicas.pdf"],
  "context": "Fragmentos relevantes encontrados..."
}
```

## Modelos Soportados

La plataforma está configurada para usar modelos GPT-4 y superiores:

- `gpt-4.1` (default)
- `gpt-4-turbo`
- `gpt-5` (cuando esté disponible)
- `o4-mini` (para razonamiento complejo)

Para cambiar el modelo, modifica el parámetro `model` en las consultas.

## Formatos de Archivo Soportados

### Documentos de Texto
- **.md** (Markdown) - Recomendado para documentación
- **.txt** (Texto plano)

### Documentos PDF
- **.pdf** - Archivos PDF con texto extraíble

## Estructura del Proyecto

```
KnowledgeBase_Manager/
├── backend (Python)
│   ├── api.py                      # API REST FastAPI
│   ├── config.py                   # Configuración OpenAI
│   ├── vector_store_manager.py     # Gestión de Vector Stores
│   ├── file_uploader.py            # Subida de archivos
│   ├── batch_manager.py            # Gestión de batches
│   ├── vector_search.py            # Búsqueda vectorial
│   ├── rag_assistant.py            # Asistente RAG
│   ├── main.py                     # CLI (opcional)
│   └── requirements.txt            # Dependencias Python
│
└── frontend/ (TypeScript + React)
    ├── src/
    │   ├── components/
    │   │   ├── ConfigPanel.tsx     # Configuración de API key
    │   │   ├── FileUploader.tsx    # Carga de archivos
    │   │   ├── VectorStoreManager.tsx  # Gestión de VS
    │   │   └── ChatInterface.tsx   # Chat RAG
    │   ├── App.tsx                 # Componente principal
    │   ├── main.tsx                # Entry point
    │   └── index.css               # Estilos globales
    ├── package.json
    ├── tsconfig.json
    ├── vite.config.ts
    └── index.html
```

## Flujo de Trabajo Completo

```
1. Usuario ingresa API Key
   ↓
2. Frontend valida con backend (/api/config)
   ↓
3. Usuario sube archivos PDF/MD
   ↓
4. Backend sube a OpenAI Files API
   ↓
5. Usuario crea Vector Store
   ↓
6. Backend crea VS y batch de indexación
   ↓
7. OpenAI indexa archivos (vectorización)
   ↓
8. Usuario hace preguntas en chat
   ↓
9. Backend busca en Vector Store
   ↓
10. GPT-4 genera respuesta con contexto
   ↓
11. Frontend muestra respuesta + fuentes
```

## Características Técnicas

### Backend
- **Validación de API Key**: Verifica conectividad antes de aceptar
- **Gestión de Estado**: Estado en memoria (puede extenderse a DB)
- **Manejo de Errores**: Respuestas detalladas para debugging
- **CORS**: Configurado para desarrollo local
- **Async/Await**: Operaciones asíncronas con httpx

### Frontend
- **TypeScript**: Tipado estático completo
- **React Hooks**: useState, useEffect, useRef
- **Axios**: Cliente HTTP con interceptors
- **Responsive**: CSS adaptable a móviles
- **UX**: Loading states, error handling, success feedback

## Seguridad

### API Key
- La API key se almacena **solo en memoria** del servidor
- No se persiste en disco ni base de datos
- Se pierde al reiniciar el servidor
- El frontend la envía una sola vez

### Archivos
- Solo se aceptan PDF, MD, TXT
- Validación de extensiones en frontend y backend
- Los archivos se suben directamente a OpenAI
- No se almacenan localmente

### CORS
- En desarrollo: `allow_origins=["*"]`
- En producción: especificar dominios exactos

## Solución de Problemas

### Error: "API key no configurada"
- Asegúrate de configurar la API key primero
- Reinicia el servidor si cambiaste la key

### Error: "No hay Vector Store configurado"
- Sube archivos primero
- Crea el Vector Store antes de hacer consultas

### Error: "Error al procesar consulta"
- Verifica que el Vector Store haya terminado de indexar
- Espera unos segundos después de crear el VS
- Verifica que tu API key tenga acceso a GPT-4

### Frontend no conecta con backend
- Verifica que el backend esté corriendo en puerto 8000
- Verifica que el frontend esté en puerto 3000
- El proxy de Vite está configurado automáticamente

## Próximas Mejoras

- [ ] Persistencia de configuración (DB)
- [ ] Autenticación de usuarios
- [ ] Múltiples Vector Stores por usuario
- [ ] Historial de conversaciones
- [ ] Exportar conversaciones
- [ ] Soporte para más formatos (DOCX, XLSX)
- [ ] Análisis de sentimientos
- [ ] Métricas y analytics

## Licencia

Este proyecto es de código abierto.

## Soporte

Para reportar problemas o sugerencias, crear un issue en el repositorio.

---

**Desarrollado con ❤️ usando OpenAI API, FastAPI, React y TypeScript**
