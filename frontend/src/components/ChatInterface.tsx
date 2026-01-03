import { useState, useRef, useEffect } from 'react'
import axios from 'axios'

interface Message {
  role: 'user' | 'assistant'
  content: string
  sources?: string[]
}

interface VectorStore {
  id: string
  name: string
  status: string
  file_counts: {
    completed: number
    in_progress: number
    failed: number
  }
}

interface ChatInterfaceProps {
  vectorStoreId?: string | null
}

function ChatInterface({ vectorStoreId: initialVectorStoreId }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Vector Store selection
  const [vectorStores, setVectorStores] = useState<VectorStore[]>([])
  const [selectedVS, setSelectedVS] = useState<string | null>(initialVectorStoreId || null)
  const [loadingVS, setLoadingVS] = useState(false)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  useEffect(() => {
    loadVectorStores()
  }, [])

  useEffect(() => {
    if (initialVectorStoreId && !selectedVS) {
      setSelectedVS(initialVectorStoreId)
    }
  }, [initialVectorStoreId])

  const loadVectorStores = async () => {
    setLoadingVS(true)
    try {
      const response = await axios.get('/api/vector-stores')
      if (response.data.success) {
        setVectorStores(response.data.vector_stores)
      }
    } catch (err: any) {
      console.error('Error loading vector stores:', err)
    } finally {
      setLoadingVS(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || loading) return

    if (!selectedVS) {
      setError('Selecciona un Vector Store primero')
      return
    }

    const userMessage: Message = {
      role: 'user',
      content: input
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setLoading(true)
    setError('')

    try {
      const response = await axios.post('/api/query', {
        query: input,
        vector_store_id: selectedVS,
        model: 'gpt-4.1'
      })

      if (response.data.success) {
        const assistantMessage: Message = {
          role: 'assistant',
          content: response.data.answer,
          sources: response.data.sources
        }
        setMessages(prev => [...prev, assistantMessage])
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error al procesar consulta')
      // Agregar mensaje de error
      const errorMessage: Message = {
        role: 'assistant',
        content: 'Lo siento, hubo un error al procesar tu consulta. Por favor intenta de nuevo.'
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="card" style={{ marginTop: '20px' }}>
      <h2>Chat - Consultas RAG</h2>

      {error && <div className="error">{error}</div>}

      {/* Selector de Vector Store */}
      <div className="input-group" style={{ marginBottom: '20px' }}>
        <label htmlFor="vsSelector">Vector Store para Consultas</label>
        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          <select
            id="vsSelector"
            value={selectedVS || ''}
            onChange={(e) => setSelectedVS(e.target.value)}
            style={{
              flex: 1,
              padding: '12px',
              border: '2px solid #e0e0e0',
              borderRadius: '8px',
              fontSize: '1rem'
            }}
            disabled={loadingVS}
          >
            <option value="">-- Selecciona un Vector Store --</option>
            {vectorStores.map(vs => (
              <option key={vs.id} value={vs.id}>
                {vs.name} ({vs.file_counts.completed} archivos)
              </option>
            ))}
          </select>
          <button
            onClick={loadVectorStores}
            className="btn btn-secondary"
            disabled={loadingVS}
            title="Refrescar lista"
          >
            🔄
          </button>
        </div>
        {!selectedVS && (
          <small style={{ color: '#666', marginTop: '5px', display: 'block' }}>
            Selecciona un Vector Store para hacer consultas sobre sus documentos
          </small>
        )}
      </div>

      <div className="chat-container">
        <div className="messages">
          {messages.length === 0 && (
            <div style={{ textAlign: 'center', color: '#666', padding: '40px' }}>
              <p>Haz una pregunta sobre tus documentos</p>
              <p style={{ fontSize: '0.9rem', marginTop: '10px' }}>
                Ejemplos: "¿Cuál es la política de devoluciones?", "¿Cuánto cuesta el envío?"
              </p>
            </div>
          )}

          {messages.map((message, index) => (
            <div
              key={index}
              className={`message message-${message.role}`}
            >
              <div className="message-content">
                {message.content}
              </div>
              {message.sources && message.sources.length > 0 && (
                <div className="message-sources">
                  Fuentes: {message.sources.join(', ')}
                </div>
              )}
            </div>
          ))}

          {loading && (
            <div className="loading">
              Pensando...
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        <form onSubmit={handleSubmit}>
          <div className="input-row">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={selectedVS ? "Escribe tu pregunta..." : "Selecciona un Vector Store primero"}
              disabled={loading || !selectedVS}
            />
            <button
              type="submit"
              className="btn btn-primary"
              disabled={loading || !input.trim() || !selectedVS}
            >
              {loading ? 'Enviando...' : 'Enviar'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default ChatInterface
