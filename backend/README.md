# Vector Store Platform API

A **FastAPI**-based REST API for managing **OpenAI Vector Stores** with **RAG (Retrieval-Augmented Generation)** capabilities.

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)
![OpenAI](https://img.shields.io/badge/OpenAI-API-orange.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Requirements](#-requirements)
- [Installation](#-installation)
- [Quick Start](#-quick-start)
- [API Endpoints](#-api-endpoints)
- [Usage Examples](#-usage-examples)
- [Configuration](#-configuration)
- [Architecture](#-architecture)
- [Error Handling](#-error-handling)
- [Development](#-development)
- [Security Considerations](#-security-considerations)
- [Notes](#-notes)
- [Contributing](#-contributing)
- [License](#-license)
- [Author](#-author)

## 🎯 Overview

Vector Store Platform API is a backend service that enables you to:

- Upload documents (PDF, Markdown, TXT) to OpenAI
- Create and manage Vector Stores for semantic search
- Perform RAG queries against your knowledge base
- Monitor indexing status and manage files

This API serves as a complete backend for building knowledge base applications powered by OpenAI's vector search capabilities.

## ✨ Features

- **🔐 API Key Management** — Secure configuration of OpenAI credentials
- **📄 Multi-format File Upload** — Support for PDF, Markdown, and TXT files
- **🗄️ Vector Store Management** — Create, list, and monitor Vector Stores
- **📁 File Operations** — Add, list, view content, and delete files from Vector Stores
- **🔍 RAG Queries** — Semantic search with AI-powered responses
- **📊 Batch Processing** — Monitor file indexing status
- **🏥 Health Checks** — Built-in health and status endpoints
- **🌐 CORS Support** — Ready for frontend integration

## 📦 Requirements

- Python 3.8+
- OpenAI API key with access to:
  - Files API
  - Vector Stores API
  - Chat Completions API

### Dependencies

```txt
fastapi>=0.100.0
uvicorn>=0.23.0
openai>=1.0.0
httpx>=0.24.0
pydantic>=2.0.0
python-multipart>=0.0.6
```

## 🚀 Installation

### 1) Clone the repository

```bash
git clone https://github.com/yourusername/vector-store-platform.git
cd vector-store-platform
```

### 2) Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3) Install dependencies

```bash
pip install fastapi uvicorn openai httpx pydantic python-multipart
```

Or using `requirements.txt`:

```bash
pip install -r requirements.txt
```

### 4) Run the server

```bash
python api.py
```

Or with uvicorn directly:

```bash
uvicorn api:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`.

## 🏁 Quick Start

### 1) Configure your API key

```bash
curl -X POST http://localhost:8000/api/config \
  -H "Content-Type: application/json" \
  -d '{"api_key": "sk-proj-your-openai-key"}'
```

### 2) Upload a document

> Note: The endpoint expects a `multipart/form-data` field named `file`.

```bash
curl -X POST http://localhost:8000/api/upload \
  -F "file=@/absolute/or/relative/path/to/document.pdf"
```

### 3) Create a Vector Store

```bash
curl -X POST http://localhost:8000/api/vector-store \
  -H "Content-Type: application/json" \
  -d '{"name": "My Knowledge Base"}'
```

### 4) Query your knowledge base

```bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the main topic of the document?"}'
```

## 📚 API Endpoints

### Configuration

| Method | Endpoint      | Description               |
|-------:|---------------|---------------------------|
| POST   | `/api/config` | Configure OpenAI API key  |

### Files

| Method | Endpoint       | Description                     |
|-------:|----------------|---------------------------------|
| POST   | `/api/upload`  | Upload a file (PDF/MD/TXT)      |
| GET    | `/api/files`   | List all uploaded files         |

### Vector Stores

| Method | Endpoint                                         | Description                              |
|-------:|--------------------------------------------------|------------------------------------------|
| POST   | `/api/vector-store`                              | Create a new Vector Store                 |
| GET    | `/api/vector-stores`                             | List all Vector Stores                    |
| GET    | `/api/status/{vs_id}`                            | Get Vector Store status                   |
| GET    | `/api/vector-stores/{vs_id}/files`               | List files in Vector Store                |
| POST   | `/api/vector-stores/{vs_id}/add-files`           | Add files to existing Vector Store        |
| DELETE | `/api/vector-stores/{vs_id}/files/{file_id}`     | Delete file from Vector Store             |
| GET    | `/api/vector-stores/{vs_id}/files/{file_id}/content` | Get file content                      |
| GET    | `/api/vector-stores/{vs_id}/batch/{batch_id}/status`  | Get batch indexing status             |

### Queries

| Method | Endpoint      | Description        |
|-------:|--------------|--------------------|
| POST   | `/api/query`  | Perform RAG query  |

### Health

| Method | Endpoint   | Description               |
|-------:|------------|---------------------------|
| GET    | `/`        | API info and status       |
| GET    | `/health`  | Detailed health check     |

## 💡 Usage Examples

### Configure API Key (Python)

```python
import requests

response = requests.post(
    "http://localhost:8000/api/config",
    json={"api_key": "sk-proj-your-key-here"}
)
print(response.json())
# {"success": true, "message": "API key configurada correctamente"}
```

### Upload Multiple Files (Python)

```python
import requests

files_to_upload = ["doc1.pdf", "doc2.md", "doc3.txt"]

for filename in files_to_upload:
    with open(filename, "rb") as f:
        response = requests.post(
            "http://localhost:8000/api/upload",
            files={"file": (filename, f)}
        )
        print(f"Uploaded {filename}: {response.json()}")
```

### Create Vector Store and Wait for Indexing (Python)

```python
import requests
import time

# Create Vector Store
response = requests.post(
    "http://localhost:8000/api/vector-store",
    json={"name": "My Knowledge Base"}
)
vs_data = response.json()
vs_id = vs_data["vector_store_id"]

# Poll for completion
while True:
    status = requests.get(f"http://localhost:8000/api/status/{vs_id}").json()
    print(f"Status: {status['status']}, Files: {status['file_count']}")

    if status["status"] == "completed":
        break
    time.sleep(2)

print("Vector Store ready!")
```

### Perform RAG Query (Python)

```python
import requests

response = requests.post(
    "http://localhost:8000/api/query",
    json={
        "query": "What are the key features mentioned in the documentation?",
        "vector_store_id": "vs_abc123",  # Optional
        "model": "gpt-4o-mini"  # Optional, defaults to gpt-5-mini
    }
)

result = response.json()
print(f"Answer: {result['answer']}")
print(f"Sources: {result['sources']}")
```

### JavaScript / Fetch Example

```js
// Configure API
await fetch('http://localhost:8000/api/config', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ api_key: 'sk-proj-...' })
});

// Upload file
const formData = new FormData();
formData.append('file', fileInput.files[0]);

await fetch('http://localhost:8000/api/upload', {
  method: 'POST',
  body: formData
});

// Query
const response = await fetch('http://localhost:8000/api/query', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ query: 'Your question here' })
});

const data = await response.json();
console.log(data.answer);
```

## ⚙️ Configuration

### Environment Variables

You can optionally set environment variables:

```bash
export OPENAI_API_KEY="sk-proj-..."  # Optional: Pre-configure API key
export HOST="0.0.0.0"                # Server host (default: 0.0.0.0)
export PORT="8000"                   # Server port (default: 8000)
```

### CORS Configuration

For production, update the CORS settings in `api.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Specific domains
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)
```

## 🏗️ Architecture

```text
┌─────────────────────────────────────────────────────────────┐
│                     Frontend Application                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Application                       │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────┐  │
│  │   Config    │  │    Files     │  │   Vector Stores    │  │
│  │  Endpoints  │  │   Upload     │  │    Management      │  │
│  └─────────────┘  └──────────────┘  └────────────────────┘  │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────┐  │
│  │    RAG      │  │    Health    │  │     App State      │  │
│  │   Query     │  │    Check     │  │    (In-Memory)     │  │
│  └─────────────┘  └──────────────┘  └────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      OpenAI API                              │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────┐  │
│  │   Files     │  │    Vector    │  │       Chat         │  │
│  │    API      │  │   Stores     │  │   Completions      │  │
│  └─────────────┘  └──────────────┘  └────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## ⚠️ Error Handling

The API returns consistent error responses:

```json
{
  "detail": "Error message description"
}
```

### Common HTTP Status Codes

| Code | Description                                  |
|-----:|----------------------------------------------|
| 200  | Success                                      |
| 400  | Bad Request (missing config, invalid input)  |
| 404  | Resource not found                           |
| 500  | Server error                                 |

### Example Error Handling (Python)

```python
import requests

response = requests.post("http://localhost:8000/api/query", json={"query": "test"})

if response.status_code != 200:
    error = response.json()
    print(f"Error: {error['detail']}")
else:
    result = response.json()
    print(result["answer"])
```

## 🛠️ Development

### Running in Development Mode

```bash
uvicorn api:app --reload --log-level debug
```

### API Documentation

FastAPI automatically generates interactive documentation:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

### Logging

The application uses Python's logging module. Adjust the log level in `api.py`:

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,  # Change to INFO, WARNING, ERROR as needed
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
```

### Testing

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest tests/
```

## 🔒 Security Considerations

1. **API Key Storage**: The API key is stored in memory. For production, consider:
   - Using environment variables
   - Implementing proper secrets management
   - Adding authentication middleware

2. **CORS**: Configure specific origins in production instead of `"*"`

3. **Rate Limiting**: Consider adding rate limiting for production use

4. **Input Validation**: All inputs are validated through Pydantic models

## 📝 Notes

- **State Persistence**: Current state is in-memory and resets on server restart
- **File Size**: Large files may require timeout adjustments
- **Model Default**: The default model is `gpt-5-mini` for cost-effectiveness

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License — see the `LICENSE` file for details.

## 👤 Author

**Knowledge Base Manager**

---

Made with ❤️ using FastAPI and OpenAI
