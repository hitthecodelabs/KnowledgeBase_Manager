import { useState } from 'react'
import ConfigPanel from './components/ConfigPanel'
import FileUploader from './components/FileUploader'
import VectorStoreManager from './components/VectorStoreManager'
import ChatInterface from './components/ChatInterface'
import VectorStoreExplorer from './components/VectorStoreExplorer'

function App() {
  const [apiConfigured, setApiConfigured] = useState(false)
  const [vectorStoreId, setVectorStoreId] = useState<string | null>(null)
  const [uploadedFiles, setUploadedFiles] = useState<any[]>([])
  const [refreshExplorer, setRefreshExplorer] = useState(0)

  const handleVectorStoreUpdated = (vsId: string) => {
    setVectorStoreId(vsId)
    // Trigger refresh in VectorStoreExplorer
    setRefreshExplorer(prev => prev + 1)
  }

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
                onVectorStoreCreated={handleVectorStoreUpdated}
              />
            </div>

            {/* Explorador de Vector Stores existentes */}
            <VectorStoreExplorer refreshTrigger={refreshExplorer} />

            {/* Chat Interface siempre visible con selector de Vector Store */}
            <ChatInterface vectorStoreId={vectorStoreId} />
          </>
        )}
      </div>
    </div>
  )
}

export default App
