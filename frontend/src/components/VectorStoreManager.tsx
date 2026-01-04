import { useState, useEffect } from 'react'
import axios from 'axios'

interface VectorStoreManagerProps {
  uploadedFiles: any[]
  onVectorStoreCreated: (vsId: string) => void
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

interface BatchStatus {
  batch_id: string
  status: string
  file_counts: {
    completed: number
    in_progress: number
    failed: number
    cancelled: number
    total: number
  }
  is_complete: boolean
}

function VectorStoreManager({ uploadedFiles, onVectorStoreCreated }: VectorStoreManagerProps) {
  const [mode, setMode] = useState<'create' | 'existing' | null>(null)
  const [name, setName] = useState('Mi Knowledge Base')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [vectorStoreId, setVectorStoreId] = useState<string | null>(null)

  // Para modo "existing"
  const [existingVectorStores, setExistingVectorStores] = useState<VectorStore[]>([])
  const [selectedVS, setSelectedVS] = useState<string | null>(null)

  // Para monitorear batch
  const [batchId, setBatchId] = useState<string | null>(null)
  const [batchStatus, setBatchStatus] = useState<BatchStatus | null>(null)

  useEffect(() => {
    if (mode === 'existing') {
      loadVectorStores()
    }
  }, [mode])

  useEffect(() => {
    if (batchId && vectorStoreId) {
      const interval = setInterval(() => {
        checkBatchStatus()
      }, 2000) // Check every 2 seconds

      return () => clearInterval(interval)
    }
  }, [batchId, vectorStoreId])

  const loadVectorStores = async () => {
    try {
      const response = await axios.get('/api/vector-stores')
      if (response.data.success) {
        setExistingVectorStores(response.data.vector_stores)
      }
    } catch (err: any) {
      setError('Error al cargar Vector Stores')
    }
  }

  const checkBatchStatus = async () => {
    if (!batchId || !vectorStoreId) return

    try {
      const response = await axios.get(`/api/vector-stores/${vectorStoreId}/batch/${batchId}/status`)
      if (response.data.success) {
        setBatchStatus(response.data)

        if (response.data.is_complete) {
          if (response.data.status === 'completed') {
            setSuccess(`Batch completado: ${response.data.file_counts.completed}/${response.data.file_counts.total} archivos indexados`)
          } else {
            setError(`Batch terminó con estado: ${response.data.status}`)
          }
          setBatchId(null) // Stop monitoring
        }
      }
    } catch (err: any) {
      console.error('Error checking batch status:', err)
    }
  }

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

  const handleAddToExisting = async () => {
    if (!selectedVS) {
      setError('Selecciona un Vector Store')
      return
    }

    if (uploadedFiles.length === 0) {
      setError('Debes subir al menos un archivo primero')
      return
    }

    setLoading(true)
    setError('')
    setSuccess('')

    try {
      const response = await axios.post(`/api/vector-stores/${selectedVS}/add-files`)

      if (response.data.success) {
        setVectorStoreId(response.data.vector_store_id)
        setBatchId(response.data.batch_id)
        setSuccess(response.data.message)
        onVectorStoreCreated(response.data.vector_store_id)
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error al agregar archivos')
    } finally {
      setLoading(false)
    }
  }

  const resetSelection = () => {
    setMode(null)
    setVectorStoreId(null)
    setBatchId(null)
    setBatchStatus(null)
    setSuccess('')
    setError('')
  }

  return (
    <div className="card">
      <h2>Vector Store</h2>

      {error && <div className="error">{error}</div>}
      {success && <div className="success">{success}</div>}

      {!mode && !vectorStoreId && (
        <div>
          <p style={{ marginBottom: '15px', color: '#666' }}>
            ¿Qué deseas hacer?
          </p>
          <div style={{ display: 'flex', gap: '10px' }}>
            <button
              onClick={() => setMode('create')}
              className="btn btn-primary"
              disabled={uploadedFiles.length === 0}
            >
              Crear Nuevo Vector Store
            </button>
            <button
              onClick={() => setMode('existing')}
              className="btn btn-secondary"
              disabled={uploadedFiles.length === 0}
            >
              Agregar a Existente
            </button>
          </div>
          {uploadedFiles.length === 0 && (
            <p style={{ marginTop: '10px', color: '#666', fontSize: '0.9rem' }}>
              Sube archivos primero
            </p>
          )}
        </div>
      )}

      {mode === 'create' && !vectorStoreId && (
        <>
          <button
            onClick={resetSelection}
            style={{
              background: 'none',
              border: 'none',
              color: '#667eea',
              cursor: 'pointer',
              marginBottom: '15px',
              fontSize: '0.9rem'
            }}
          >
            ← Volver
          </button>
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
            disabled={loading}
          >
            {loading ? 'Creando e indexando...' : 'Crear Vector Store'}
          </button>
        </>
      )}

      {mode === 'existing' && !vectorStoreId && (
        <>
          <button
            onClick={resetSelection}
            style={{
              background: 'none',
              border: 'none',
              color: '#667eea',
              cursor: 'pointer',
              marginBottom: '15px',
              fontSize: '0.9rem'
            }}
          >
            ← Volver
          </button>
          <div className="input-group">
            <label>Selecciona un Vector Store</label>
            <select
              value={selectedVS || ''}
              onChange={(e) => setSelectedVS(e.target.value)}
              style={{
                width: '100%',
                padding: '12px',
                border: '2px solid #e0e0e0',
                borderRadius: '8px',
                fontSize: '1rem'
              }}
            >
              <option value="">-- Selecciona --</option>
              {existingVectorStores.map(vs => (
                <option key={vs.id} value={vs.id}>
                  {vs.name} ({vs.file_counts.completed} archivos)
                </option>
              ))}
            </select>
          </div>

          <button
            onClick={handleAddToExisting}
            className="btn btn-primary"
            disabled={loading || !selectedVS}
          >
            {loading ? 'Agregando archivos...' : 'Agregar Archivos'}
          </button>
        </>
      )}

      {vectorStoreId && (
        <div>
          <div style={{
            background: '#f8f9ff',
            padding: '15px',
            borderRadius: '8px',
            marginTop: '10px'
          }}>
            <p style={{ fontWeight: 600, marginBottom: '5px' }}>
              {mode === 'create' ? 'Vector Store Creado' : 'Archivos Agregados'}
            </p>
            <p style={{ fontSize: '0.9rem', color: '#666', wordBreak: 'break-all' }}>
              ID: {vectorStoreId}
            </p>
            {mode === 'existing' && batchStatus && (
              <div style={{ marginTop: '10px' }}>
                <p style={{ fontSize: '0.9rem', color: '#666' }}>
                  <strong>Progreso del Batch:</strong>
                </p>
                <p style={{ fontSize: '0.85rem', color: '#666' }}>
                  Estado: {batchStatus.status}
                </p>
                <p style={{ fontSize: '0.85rem', color: '#666' }}>
                  Completados: {batchStatus.file_counts.completed}/{batchStatus.file_counts.total}
                </p>
                <div style={{
                  width: '100%',
                  height: '8px',
                  background: '#e0e0e0',
                  borderRadius: '4px',
                  marginTop: '8px',
                  overflow: 'hidden'
                }}>
                  <div style={{
                    width: `${(batchStatus.file_counts.completed / batchStatus.file_counts.total) * 100}%`,
                    height: '100%',
                    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                    transition: 'width 0.3s'
                  }}></div>
                </div>
              </div>
            )}
          </div>

          <div style={{ marginTop: '15px', padding: '12px', background: '#d1ecf1', borderRadius: '8px' }}>
            <p style={{ fontSize: '0.9rem', color: '#0c5460' }}>
              {batchId
                ? 'La indexación está en progreso. Puedes ver el progreso arriba.'
                : 'Indexación completa. Puedes hacer consultas abajo.'}
            </p>
          </div>

          <button
            onClick={resetSelection}
            className="btn btn-secondary"
            style={{ marginTop: '15px' }}
          >
            Procesar Más Archivos
          </button>
        </div>
      )}
    </div>
  )
}

export default VectorStoreManager