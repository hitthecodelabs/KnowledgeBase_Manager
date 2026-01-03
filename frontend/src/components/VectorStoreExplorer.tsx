import { useState, useEffect } from 'react'
import axios from 'axios'

interface VectorStore {
  id: string
  name: string
  status: string
  file_counts: {
    completed: number
    in_progress: number
    failed: number
  }
  created_at: number
}

interface VSFile {
  id: string
  status: string
  filename: string
  purpose: string
  bytes: number
  created_at: number
}

interface FileContent {
  success: boolean
  filename: string
  file_id: string
  content: string
  size: number
  message?: string
}

function VectorStoreExplorer() {
  const [vectorStores, setVectorStores] = useState<VectorStore[]>([])
  const [selectedVS, setSelectedVS] = useState<VectorStore | null>(null)
  const [files, setFiles] = useState<VSFile[]>([])
  const [selectedFile, setSelectedFile] = useState<VSFile | null>(null)
  const [fileContent, setFileContent] = useState<FileContent | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    loadVectorStores()
  }, [])

  const loadVectorStores = async () => {
    setLoading(true)
    setError('')
    try {
      const response = await axios.get('/api/vector-stores')
      if (response.data.success) {
        setVectorStores(response.data.vector_stores)
      }
    } catch (err: any) {
      setError('Error al cargar Vector Stores')
    } finally {
      setLoading(false)
    }
  }

  const handleVSClick = async (vs: VectorStore) => {
    setSelectedVS(vs)
    setSelectedFile(null)
    setFileContent(null)
    setLoading(true)
    setError('')

    try {
      const response = await axios.get(`/api/vector-stores/${vs.id}/files`)
      if (response.data.success) {
        setFiles(response.data.files)
      }
    } catch (err: any) {
      setError('Error al cargar archivos')
    } finally {
      setLoading(false)
    }
  }

  const handleFileClick = async (file: VSFile) => {
    if (!selectedVS) return

    setSelectedFile(file)
    setLoading(true)
    setError('')

    try {
      const response = await axios.get(`/api/vector-stores/${selectedVS.id}/files/${file.id}/content`)
      setFileContent(response.data)
    } catch (err: any) {
      setError('Error al cargar contenido del archivo')
    } finally {
      setLoading(false)
    }
  }

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
  }

  const formatDate = (timestamp: number) => {
    return new Date(timestamp * 1000).toLocaleString()
  }

  return (
    <div className="card" style={{ marginTop: '20px' }}>
      <h2>Explorador de Vector Stores</h2>

      {error && <div className="error">{error}</div>}

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 2fr', gap: '20px', marginTop: '20px' }}>
        {/* Lista de Vector Stores */}
        <div>
          <h3 style={{ fontSize: '1.1rem', marginBottom: '10px' }}>Vector Stores</h3>
          <div style={{ maxHeight: '500px', overflowY: 'auto' }}>
            {loading && !selectedVS && <div className="loading">Cargando...</div>}
            {vectorStores.map(vs => (
              <div
                key={vs.id}
                onClick={() => handleVSClick(vs)}
                style={{
                  padding: '12px',
                  background: selectedVS?.id === vs.id ? '#667eea' : '#f8f9ff',
                  color: selectedVS?.id === vs.id ? 'white' : '#333',
                  borderRadius: '8px',
                  marginBottom: '8px',
                  cursor: 'pointer',
                  transition: 'all 0.2s'
                }}
                onMouseEnter={(e) => {
                  if (selectedVS?.id !== vs.id) {
                    e.currentTarget.style.background = '#e8eaff'
                  }
                }}
                onMouseLeave={(e) => {
                  if (selectedVS?.id !== vs.id) {
                    e.currentTarget.style.background = '#f8f9ff'
                  }
                }}
              >
                <div style={{ fontWeight: 600, marginBottom: '5px', fontSize: '0.95rem' }}>
                  {vs.name}
                </div>
                <div style={{ fontSize: '0.85rem', opacity: 0.9 }}>
                  {vs.file_counts.completed} archivos
                </div>
                <div style={{ fontSize: '0.75rem', opacity: 0.8, marginTop: '3px' }}>
                  {vs.status}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Lista de Archivos */}
        <div>
          <h3 style={{ fontSize: '1.1rem', marginBottom: '10px' }}>
            Archivos {selectedVS && `(${files.length})`}
          </h3>
          <div style={{ maxHeight: '500px', overflowY: 'auto' }}>
            {!selectedVS && (
              <p style={{ color: '#666', fontSize: '0.9rem', padding: '20px', textAlign: 'center' }}>
                Selecciona un Vector Store
              </p>
            )}
            {selectedVS && loading && <div className="loading">Cargando...</div>}
            {selectedVS && !loading && files.map(file => (
              <div
                key={file.id}
                onClick={() => handleFileClick(file)}
                style={{
                  padding: '10px',
                  background: selectedFile?.id === file.id ? '#667eea' : '#f8f9ff',
                  color: selectedFile?.id === file.id ? 'white' : '#333',
                  borderRadius: '8px',
                  marginBottom: '6px',
                  cursor: 'pointer',
                  transition: 'all 0.2s'
                }}
                onMouseEnter={(e) => {
                  if (selectedFile?.id !== file.id) {
                    e.currentTarget.style.background = '#e8eaff'
                  }
                }}
                onMouseLeave={(e) => {
                  if (selectedFile?.id !== file.id) {
                    e.currentTarget.style.background = '#f8f9ff'
                  }
                }}
              >
                <div style={{ fontWeight: 600, fontSize: '0.9rem', marginBottom: '3px' }}>
                  {file.filename}
                </div>
                <div style={{ fontSize: '0.8rem', opacity: 0.9 }}>
                  {formatBytes(file.bytes)}
                </div>
                <div style={{ fontSize: '0.75rem', opacity: 0.8, marginTop: '2px' }}>
                  {file.status}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Contenido del Archivo */}
        <div>
          <h3 style={{ fontSize: '1.1rem', marginBottom: '10px' }}>Contenido</h3>
          <div style={{
            maxHeight: '500px',
            overflowY: 'auto',
            background: '#f8f9ff',
            padding: '15px',
            borderRadius: '8px'
          }}>
            {!selectedFile && (
              <p style={{ color: '#666', fontSize: '0.9rem', textAlign: 'center', padding: '20px' }}>
                Selecciona un archivo para ver su contenido
              </p>
            )}
            {selectedFile && loading && <div className="loading">Cargando contenido...</div>}
            {selectedFile && !loading && fileContent && (
              <>
                <div style={{
                  marginBottom: '15px',
                  paddingBottom: '10px',
                  borderBottom: '2px solid #e0e0e0'
                }}>
                  <h4 style={{ fontSize: '1rem', marginBottom: '5px' }}>
                    {fileContent.filename}
                  </h4>
                  <div style={{ fontSize: '0.85rem', color: '#666' }}>
                    ID: <code style={{ background: '#fff', padding: '2px 6px', borderRadius: '4px' }}>
                      {fileContent.file_id}
                    </code>
                  </div>
                  <div style={{ fontSize: '0.85rem', color: '#666', marginTop: '3px' }}>
                    Tamaño: {formatBytes(fileContent.size)}
                  </div>
                </div>

                {fileContent.success ? (
                  <pre style={{
                    whiteSpace: 'pre-wrap',
                    wordWrap: 'break-word',
                    fontSize: '0.85rem',
                    lineHeight: '1.6',
                    background: 'white',
                    padding: '15px',
                    borderRadius: '6px',
                    border: '1px solid #e0e0e0'
                  }}>
                    {fileContent.content}
                  </pre>
                ) : (
                  <div style={{
                    padding: '20px',
                    background: '#fff3cd',
                    color: '#856404',
                    borderRadius: '6px',
                    textAlign: 'center'
                  }}>
                    {fileContent.message || 'No se puede mostrar el contenido de este archivo'}
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default VectorStoreExplorer