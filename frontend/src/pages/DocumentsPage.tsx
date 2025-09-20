import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import { useDropzone } from 'react-dropzone'
import { 
  Upload, 
  FileText, 
  Trash2, 
  RefreshCw, 
  Eye, 
  AlertCircle,
  CheckCircle,
  Clock,
  ChevronDown,
  ChevronUp
} from 'lucide-react'
import { api } from '../lib/api'
import { Document, DocumentChunk } from '../types'
import { LoadingSpinner } from '../components/LoadingSpinner'
import { formatDate, formatFileSize } from '../lib/utils'
import toast from 'react-hot-toast'

export function DocumentsPage() {
  const [uploading, setUploading] = useState(false)
  const [expandedDocument, setExpandedDocument] = useState<number | null>(null)
  const queryClient = useQueryClient()

  const { data: documents, isLoading } = useQuery<Document[]>(
    'documents',
    async () => {
      const response = await api.get('/api/v1/documents/')
      return response.data
    }
  )

  const deleteDocument = useMutation(
    async (id: number) => {
      await api.delete(`/api/v1/documents/${id}`)
    },
    {
      onSuccess: () => {
        queryClient.invalidateQueries('documents')
        toast.success('Document deleted successfully')
      },
      onError: () => {
        toast.error('Failed to delete document')
      },
    }
  )

  const reprocessDocument = useMutation(
    async (id: number) => {
      await api.post(`/api/v1/documents/${id}/reprocess`)
    },
    {
      onSuccess: () => {
        queryClient.invalidateQueries('documents')
        toast.success('Document reprocessing started')
      },
      onError: () => {
        toast.error('Failed to reprocess document')
      },
    }
  )

  const { data: documentChunks } = useQuery<DocumentChunk[]>(
    ['document-chunks', expandedDocument],
    async () => {
      if (!expandedDocument) return []
      const response = await api.get(`/api/v1/documents/${expandedDocument}/chunks?limit=3`)
      return response.data
    },
    {
      enabled: !!expandedDocument
    }
  )

  const onDrop = async (acceptedFiles: File[]) => {
    setUploading(true)
    try {
      for (const file of acceptedFiles) {
        const formData = new FormData()
        formData.append('file', file)
        
        await api.post('/api/v1/documents/upload', formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        })
      }
      
      queryClient.invalidateQueries('documents')
      toast.success('Documents uploaded successfully')
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Upload failed')
    } finally {
      setUploading(false)
    }
  }

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'text/csv': ['.csv'],
    },
    multiple: true,
  })

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'processed':
        return <CheckCircle className="h-5 w-5 text-green-500" />
      case 'processing':
        return <Clock className="h-5 w-5 text-yellow-500" />
      case 'error':
        return <AlertCircle className="h-5 w-5 text-red-500" />
      default:
        return <Clock className="h-5 w-5 text-gray-400" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'processed':
        return 'text-green-600 bg-green-100'
      case 'processing':
        return 'text-yellow-600 bg-yellow-100'
      case 'error':
        return 'text-red-600 bg-red-100'
      default:
        return 'text-gray-600 bg-gray-100'
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="md:flex md:items-center md:justify-between">
        <div className="min-w-0 flex-1">
          <h2 className="text-2xl font-bold leading-7 text-gray-900 sm:truncate sm:text-3xl sm:tracking-tight">
            Documents
          </h2>
          <p className="mt-1 text-sm text-gray-500">
            Manage your knowledge base documents
          </p>
        </div>
      </div>

      {/* Upload Area */}
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
          isDragActive
            ? 'border-primary bg-primary/5'
            : 'border-gray-300 hover:border-gray-400'
        } ${uploading ? 'opacity-50 cursor-not-allowed' : ''}`}
      >
        <input {...getInputProps()} disabled={uploading} />
        <Upload className="mx-auto h-12 w-12 text-gray-400" />
        <div className="mt-4">
          <p className="text-lg font-medium text-gray-900">
            {uploading ? 'Uploading...' : 'Upload Documents'}
          </p>
          <p className="text-sm text-gray-500">
            Drag and drop files here, or click to select files
          </p>
          <p className="text-xs text-gray-400 mt-2">
            Supports PDF, DOCX, and CSV files
          </p>
        </div>
      </div>

      {/* Documents List */}
      <div className="card">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">Your Documents</h3>
        </div>
        <div className="divide-y divide-gray-200">
          {documents && documents.length > 0 ? (
            documents.map((document) => (
              <div key={document.id} className="px-6 py-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <FileText className="h-8 w-8 text-gray-400" />
                    <div>
                      <h4 className="text-sm font-medium text-gray-900">
                        {document.title || document.original_filename}
                      </h4>
                      <p className="text-sm text-gray-500">
                        {formatFileSize(document.file_size)} • {document.file_type.toUpperCase()}
                      </p>
                      <p className="text-xs text-gray-400">
                        Uploaded {formatDate(document.created_at)}
                      </p>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-4">
                    <div className="flex items-center space-x-2">
                      {getStatusIcon(document.status)}
                      <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(document.status)}`}>
                        {document.status}
                      </span>
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => setExpandedDocument(expandedDocument === document.id ? null : document.id)}
                        className="p-2 text-gray-400 hover:text-gray-600"
                        title="Preview chunks"
                      >
                        {expandedDocument === document.id ? (
                          <ChevronUp className="h-4 w-4" />
                        ) : (
                          <Eye className="h-4 w-4" />
                        )}
                      </button>
                      <button
                        onClick={() => reprocessDocument.mutate(document.id)}
                        disabled={reprocessDocument.isLoading}
                        className="p-2 text-gray-400 hover:text-gray-600"
                        title="Reprocess document"
                      >
                        <RefreshCw className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => deleteDocument.mutate(document.id)}
                        disabled={deleteDocument.isLoading}
                        className="p-2 text-gray-400 hover:text-red-600"
                        title="Delete document"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                </div>
                
                {document.processing_error && (
                  <div className="mt-2 p-3 bg-red-50 border border-red-200 rounded-md">
                    <p className="text-sm text-red-600">
                      <strong>Error:</strong> {document.processing_error}
                    </p>
                  </div>
                )}

                {/* Document Chunks Preview */}
                {expandedDocument === document.id && (
                  <div className="mt-4 p-4 bg-gray-50 rounded-lg">
                    <h4 className="text-sm font-medium text-gray-900 mb-3">Document Chunks Preview (First 3)</h4>
                    {documentChunks && documentChunks.length > 0 ? (
                      <div className="space-y-3">
                        {documentChunks.map((chunk, index) => (
                          <div key={chunk.id} className="p-3 bg-white rounded border">
                            <div className="flex items-center justify-between mb-2">
                              <span className="text-xs font-medium text-gray-500">
                                Chunk {chunk.chunk_index + 1}
                                {chunk.page_number && ` • Page ${chunk.page_number}`}
                                {chunk.word_count && ` • ${chunk.word_count} words`}
                              </span>
                              {chunk.section_title && (
                                <span className="text-xs text-blue-600 bg-blue-100 px-2 py-1 rounded">
                                  {chunk.section_title}
                                </span>
                              )}
                            </div>
                            <p className="text-sm text-gray-700 line-clamp-3">
                              {chunk.content}
                            </p>
                          </div>
                        ))}
                        {document.chunks_count && document.chunks_count > 3 && (
                          <p className="text-xs text-gray-500 text-center">
                            Showing first 3 of {document.chunks_count} chunks
                          </p>
                        )}
                      </div>
                    ) : (
                      <p className="text-sm text-gray-500">No chunks available</p>
                    )}
                  </div>
                )}
              </div>
            ))
          ) : (
            <div className="px-6 py-12 text-center">
              <FileText className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">No documents</h3>
              <p className="mt-1 text-sm text-gray-500">
                Get started by uploading your first document.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
