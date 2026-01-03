import { useState } from 'react'
import axios from 'axios'

interface VectorStoreManagerProps {
  uploadedFiles: any[]
  onVectorStoreCreated: (vsId: string) => void
}

function VectorStoreManager({ uploadedFiles, onVectorStoreCreated }: VectorStoreManagerProps) {
  const [name, setName] = useState('Mi Knowledge Base')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [vectorStoreId, setVectorStoreId] = useState<string | null>(null)

  const handleCreate = async () => {
    if (uploadedFiles.length === 0) {
      setError('Debes subir al menos un archivo primero')
      return
    }

    setLoading(true)
    setError('')
    setSuccess('')

    try {
      const response = await axios.post('/api/vector-store', {
        name
      })

      if (response.data.success) {
        setVectorStoreId(response.data.vector_store_id)
        setSuccess(response.data.message)
        onVectorStoreCreated(response.data.vector_store_id)
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error al crear Vector Store')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="card">
      <h2>Vector Store</h2>

      {error && <div className="error">{error}</div>}
      {success && <div className="success">{success}</div>}

      {!vectorStoreId ? (
        <>
          <div className="input-group">
            <label htmlFor="vsName">Nombre del Vector Store</label>
            <input
              id="vsName"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Mi Knowledge Base"
            />
            <small style={{ color: '#666', marginTop: '5px', display: 'block' }}>
              Dale un nombre descriptivo a tu base de conocimiento
            </small>
          </div>

          <button
            onClick={handleCreate}
            className="btn btn-primary"
            disabled={loading || uploadedFiles.length === 0}
          >
            {loading ? 'Creando e indexando...' : 'Crear Vector Store'}
          </button>

          {uploadedFiles.length === 0 && (
            <p style={{ marginTop: '10px', color: '#666', fontSize: '0.9rem' }}>
              Sube archivos primero para crear un Vector Store
            </p>
          )}
        </>
      ) : (
        <div>
          <div style={{
            background: '#f8f9ff',
            padding: '15px',
            borderRadius: '8px',
            marginTop: '10px'
          }}>
            <p style={{ fontWeight: 600, marginBottom: '5px' }}>Vector Store Creado</p>
            <p style={{ fontSize: '0.9rem', color: '#666', wordBreak: 'break-all' }}>
              ID: {vectorStoreId}
            </p>
            <p style={{ fontSize: '0.9rem', color: '#666', marginTop: '10px' }}>
              {uploadedFiles.length} archivo(s) indexado(s)
            </p>
          </div>

          <div style={{ marginTop: '15px', padding: '12px', background: '#d1ecf1', borderRadius: '8px' }}>
            <p style={{ fontSize: '0.9rem', color: '#0c5460' }}>
              La indexación puede tardar unos segundos. Puedes comenzar a hacer consultas abajo.
            </p>
          </div>
        </div>
      )}
    </div>
  )
}

export default VectorStoreManager
