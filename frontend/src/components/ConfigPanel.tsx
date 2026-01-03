import { useState } from 'react'
import axios from 'axios'

interface ConfigPanelProps {
  onConfigured: () => void
}

function ConfigPanel({ onConfigured }: ConfigPanelProps) {
  const [apiKey, setApiKey] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    setSuccess('')

    try {
      const response = await axios.post('/api/config', {
        api_key: apiKey
      })

      if (response.data.success) {
        setSuccess('API Key configurada correctamente')
        setTimeout(() => {
          onConfigured()
        }, 1000)
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error al configurar API Key')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="card">
      <h2>Configuración de OpenAI</h2>

      {error && <div className="error">{error}</div>}
      {success && <div className="success">{success}</div>}

      <form onSubmit={handleSubmit}>
        <div className="input-group">
          <label htmlFor="apiKey">OpenAI API Key</label>
          <input
            id="apiKey"
            type="password"
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            placeholder="sk-proj-..."
            required
          />
          <small style={{ color: '#666', marginTop: '5px', display: 'block' }}>
            Ingresa tu OpenAI API Key para comenzar. Tu key se mantiene segura y solo se usa en esta sesión.
          </small>
        </div>

        <button
          type="submit"
          className="btn btn-primary"
          disabled={loading || !apiKey}
        >
          {loading ? 'Configurando...' : 'Configurar API Key'}
        </button>
      </form>
    </div>
  )
}

export default ConfigPanel
