import { useState, useRef, useEffect } from 'react'
import axios from 'axios'

interface Message {
  role: 'user' | 'assistant'
  content: string
  sources?: string[]
}

interface ChatInterfaceProps {
  vectorStoreId: string
}

function ChatInterface({ vectorStoreId }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || loading) return

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
        vector_store_id: vectorStoreId,
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
              placeholder="Escribe tu pregunta..."
              disabled={loading}
            />
            <button
              type="submit"
              className="btn btn-primary"
              disabled={loading || !input.trim()}
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
