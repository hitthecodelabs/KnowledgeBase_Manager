import { useState, useEffect } from 'react'
import ConfigPanel from './components/ConfigPanel'
import FileUploader from './components/FileUploader'
import VectorStoreManager from './components/VectorStoreManager'
import ChatInterface from './components/ChatInterface'

function App() {
  const [apiConfigured, setApiConfigured] = useState(false)
  const [vectorStoreId, setVectorStoreId] = useState<string | null>(null)
  const [uploadedFiles, setUploadedFiles] = useState<any[]>([])

  return (
    <div className="app">
      <div className="container">
        <header className="header">
          <h1>Vector Store Platform</h1>
          <p>Gestiona tus documentos y haz consultas con OpenAI</p>
        </header>

        {!apiConfigured ? (
          <ConfigPanel onConfigured={() => setApiConfigured(true)} />
        ) : (
          <>
            <div className="grid">
              <FileUploader
                onFilesUploaded={(files) => setUploadedFiles(files)}
                uploadedFiles={uploadedFiles}
              />

              <VectorStoreManager
                uploadedFiles={uploadedFiles}
                onVectorStoreCreated={(vsId) => setVectorStoreId(vsId)}
              />
            </div>

            {vectorStoreId && (
              <ChatInterface vectorStoreId={vectorStoreId} />
            )}
          </>
        )}
      </div>
    </div>
  )
}

export default App
