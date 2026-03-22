import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useDropzone } from 'react-dropzone'
import {
  Scale, Upload, FileText, LogOut, Trash2, ChevronRight,
  Clock, CheckCircle, AlertTriangle, XCircle, Loader2, User
} from 'lucide-react'
import api from '../api/client'

const STATUS_ICON = {
  ready:    <CheckCircle className="w-4 h-4 text-green-400" />,
  indexing: <Loader2 className="w-4 h-4 text-indigo-400 animate-spin" />,
  processing: <Loader2 className="w-4 h-4 text-indigo-400 animate-spin" />,
  failed:   <XCircle className="w-4 h-4 text-red-400" />,
}

const STATUS_COLOR = {
  ready:    'text-green-400 bg-green-400/10',
  indexing: 'text-indigo-400 bg-indigo-400/10',
  processing: 'text-indigo-400 bg-indigo-400/10',
  failed:   'text-red-400 bg-red-400/10',
}

function formatBytes(bytes) {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

function formatDate(iso) {
  return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

export default function Dashboard() {
  const navigate = useNavigate()
  const user = JSON.parse(localStorage.getItem('user') || '{}')
  const [docs, setDocs] = useState([])
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [uploadError, setUploadError] = useState('')

  async function fetchDocs() {
    try {
      const { data } = await api.get('/documents')
      setDocs(data)
    } catch {
      // handled by interceptor
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchDocs() }, [])

  const onDrop = useCallback(async (files) => {
    const file = files[0]
    if (!file) return
    setUploadError('')
    setUploading(true)
    try {
      const form = new FormData()
      form.append('file', file)
      await api.post('/documents/upload', form)
      await fetchDocs()
    } catch (err) {
      setUploadError(err.response?.data?.detail || 'Upload failed.')
    } finally {
      setUploading(false)
    }
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'] },
    maxFiles: 1,
    disabled: uploading,
  })

  async function deleteDoc(e, id) {
    e.stopPropagation()
    if (!confirm('Delete this document?')) return
    await api.delete(`/documents/${id}`)
    setDocs(docs.filter((d) => d.document_id !== id))
  }

  function logout() {
    localStorage.clear()
    navigate('/')
  }

  return (
    <div className="min-h-screen">
      {/* Navbar */}
      <nav className="glass border-b border-white/5 sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Scale className="w-6 h-6 text-indigo-400" />
            <span className="font-bold text-lg gradient-text">LegalDoc AI</span>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 text-sm text-gray-400">
              <div className="w-8 h-8 rounded-full bg-indigo-500/20 flex items-center justify-center">
                <User className="w-4 h-4 text-indigo-400" />
              </div>
              <span className="hidden sm:inline">{user.name}</span>
            </div>
            <button onClick={logout} className="flex items-center gap-1 text-sm text-gray-500 hover:text-white transition-colors">
              <LogOut className="w-4 h-4" />
              <span className="hidden sm:inline">Sign out</span>
            </button>
          </div>
        </div>
      </nav>

      <main className="max-w-6xl mx-auto px-6 py-10">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white mb-1">
            Welcome back, <span className="gradient-text">{user.name?.split(' ')[0]}</span>
          </h1>
          <p className="text-gray-400">Upload a legal document to get started.</p>
        </div>

        {/* Upload zone */}
        <div
          {...getRootProps()}
          className={`border-2 border-dashed rounded-2xl p-10 text-center cursor-pointer transition-all mb-10
            ${isDragActive
              ? 'border-indigo-500 bg-indigo-500/10'
              : 'border-white/10 hover:border-indigo-500/50 hover:bg-white/[0.03]'
            }
            ${uploading ? 'opacity-60 cursor-not-allowed' : ''}
          `}
        >
          <input {...getInputProps()} />
          <div className="flex flex-col items-center gap-3">
            {uploading ? (
              <>
                <Loader2 className="w-10 h-10 text-indigo-400 animate-spin" />
                <p className="text-white font-medium">Uploading and indexing…</p>
                <p className="text-gray-500 text-sm">This may take a moment</p>
              </>
            ) : (
              <>
                <div className="w-14 h-14 rounded-2xl bg-indigo-500/10 flex items-center justify-center">
                  <Upload className="w-7 h-7 text-indigo-400" />
                </div>
                <p className="text-white font-medium text-lg">
                  {isDragActive ? 'Drop your PDF here' : 'Drag & drop a PDF, or click to browse'}
                </p>
                <p className="text-gray-500 text-sm">Supports scanned PDFs with OCR · Max 50MB</p>
              </>
            )}
          </div>
        </div>

        {uploadError && (
          <div className="flex items-center gap-2 bg-red-500/10 border border-red-500/20 text-red-400 rounded-xl px-4 py-3 mb-6 text-sm">
            <AlertTriangle className="w-4 h-4" /> {uploadError}
          </div>
        )}

        {/* Documents list */}
        <div>
          <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <FileText className="w-5 h-5 text-indigo-400" />
            Your Documents
            {!loading && (
              <span className="text-sm font-normal text-gray-500 ml-1">({docs.length})</span>
            )}
          </h2>

          {loading ? (
            <div className="flex items-center justify-center py-20 text-gray-500">
              <Loader2 className="w-6 h-6 animate-spin mr-2" /> Loading documents…
            </div>
          ) : docs.length === 0 ? (
            <div className="glass rounded-2xl p-16 text-center text-gray-500">
              <FileText className="w-12 h-12 mx-auto mb-4 opacity-30" />
              <p className="text-lg">No documents yet</p>
              <p className="text-sm mt-1">Upload your first PDF above to get started</p>
            </div>
          ) : (
            <div className="space-y-3">
              {docs.map((doc) => (
                <div
                  key={doc.document_id}
                  onClick={() => doc.status === 'ready' && navigate(`/documents/${doc.document_id}`)}
                  className={`glass glass-hover rounded-2xl p-5 flex items-center gap-4 transition-all group
                    ${doc.status === 'ready' ? 'cursor-pointer' : 'cursor-default'}`}
                >
                  <div className="w-10 h-10 rounded-xl bg-indigo-500/10 flex items-center justify-center flex-shrink-0">
                    <FileText className="w-5 h-5 text-indigo-400" />
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <p className="font-medium text-white truncate">{doc.filename}</p>
                      <span className={`flex items-center gap-1 text-xs px-2 py-0.5 rounded-full font-medium flex-shrink-0 ${STATUS_COLOR[doc.status] || 'text-gray-400 bg-white/5'}`}>
                        {STATUS_ICON[doc.status]}
                        {doc.status}
                      </span>
                    </div>
                    <div className="flex items-center gap-4 text-xs text-gray-500">
                      <span>{doc.page_count} pages</span>
                      <span>{doc.chunk_count} clauses</span>
                      <span>{formatBytes(doc.file_size_bytes)}</span>
                      <span className="flex items-center gap-1">
                        <Clock className="w-3 h-3" /> {formatDate(doc.created_at)}
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 flex-shrink-0">
                    <button
                      onClick={(e) => deleteDoc(e, doc.document_id)}
                      className="opacity-0 group-hover:opacity-100 w-8 h-8 flex items-center justify-center rounded-lg hover:bg-red-500/10 text-gray-500 hover:text-red-400 transition-all"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                    {doc.status === 'ready' && (
                      <ChevronRight className="w-5 h-5 text-gray-600 group-hover:text-indigo-400 transition-colors" />
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  )
}
