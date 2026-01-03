import { useState, useRef } from 'react'
import axios from 'axios'

interface FileUploaderProps {
  onFilesUploaded: (files: any[]) => void
  uploadedFiles: any[]
}

function FileUploader({ onFilesUploaded, uploadedFiles }: FileUploaderProps) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (!files || files.length === 0) return

    setLoading(true)
    setError('')

    try {
      const newFiles = []

      for (let i = 0; i < files.length; i++) {
        const file = files[i]

        // Validar extensión
        if (!file.name.endsWith('.pdf') && !file.name.endsWith('.md') && !file.name.endsWith('.txt')) {
          setError(`Archivo ${file.name} no soportado. Solo se permiten .pdf, .md o .txt`)
          continue
        }

        const formData = new FormData()
        formData.append('file', file)

        const response = await axios.post('/api/upload', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        })

        if (response.data.success) {
          newFiles.push(response.data)
        }
      }

      onFilesUploaded([...uploadedFiles, ...newFiles])
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error al subir archivos')
    } finally {
      setLoading(false)
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    }
  }

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
  }

  return (
    <div className="card">
      <h2>Subir Archivos</h2>

      {error && <div className="error">{error}</div>}

      <div
        className="file-upload"
        onClick={() => fileInputRef.current?.click()}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept=".pdf,.md,.txt"
          onChange={handleFileSelect}
        />
        <div>
          <svg
            width="64"
            height="64"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            style={{ margin: '0 auto', color: '#667eea' }}
          >
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
            <polyline points="17 8 12 3 7 8"></polyline>
            <line x1="12" y1="3" x2="12" y2="15"></line>
          </svg>
          <p style={{ marginTop: '10px', fontWeight: 600 }}>
            {loading ? 'Subiendo...' : 'Click para seleccionar archivos'}
          </p>
          <p style={{ fontSize: '0.9rem', color: '#666', marginTop: '5px' }}>
            Formatos: PDF, MD, TXT
          </p>
        </div>
      </div>

      {uploadedFiles.length > 0 && (
        <div className="file-list">
          <h3 style={{ marginBottom: '10px', fontSize: '1.1rem' }}>
            Archivos Subidos ({uploadedFiles.length})
          </h3>
          {uploadedFiles.map((file, index) => (
            <div key={index} className="file-item">
              <div className="file-item-info">
                <span className="file-item-name">{file.filename}</span>
                <span className="file-item-size">{formatBytes(file.size)}</span>
              </div>
              <span className="status-badge status-success">Subido</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default FileUploader
