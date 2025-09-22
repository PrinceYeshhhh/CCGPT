import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { useDropzone } from 'react-dropzone'
import { Upload, File, Trash2, Eye, CheckCircle, Clock, AlertCircle, Plus, RefreshCw } from 'lucide-react'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import { api } from '@/lib/api'
import toast from 'react-hot-toast'

interface DocumentItem { id: number; title?: string; original_filename: string; file_size: number; file_type: string; created_at: string; status: string; processing_error?: string; chunks_count?: number }
interface DocumentChunk { id: number; chunk_index: number; page_number?: number; word_count?: number; section_title?: string; content: string }

export function Documents() {
  const [uploading, setUploading] = useState(false)
  const [expandedDocument, setExpandedDocument] = useState<number | null>(null)
  const queryClient = useQueryClient()

  const { data: documents, isLoading } = useQuery<DocumentItem[]>('documents', async () => {
    const response = await api.get('/api/v1/documents/')
    return response.data
  })

  const deleteDocument = useMutation(async (id: number) => {
    await api.delete(`/api/v1/documents/${id}`)
  }, {
    onSuccess: () => { queryClient.invalidateQueries('documents'); toast.success('Document deleted successfully') },
    onError: () => { toast.error('Failed to delete document') }
  })

  const reprocessDocument = useMutation(async (id: number) => {
    await api.post(`/api/v1/documents/${id}/reprocess`)
  }, {
    onSuccess: () => { queryClient.invalidateQueries('documents'); toast.success('Document reprocessing started') },
    onError: () => { toast.error('Failed to reprocess document') }
  })

  const { data: documentChunks } = useQuery<DocumentChunk[]>(['document-chunks', expandedDocument], async () => {
    if (!expandedDocument) return []
    const response = await api.get(`/api/v1/documents/${expandedDocument}/chunks?limit=3`)
    return response.data
  }, { enabled: !!expandedDocument })

  const onDrop = async (acceptedFiles: File[]) => {
    setUploading(true)
    try {
      for (const file of acceptedFiles) {
        const formData = new FormData()
        formData.append('file', file)
        await api.post('/api/v1/documents/upload', formData, { headers: { 'Content-Type': 'multipart/form-data' } })
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
      'text/csv': ['.csv']
    },
    multiple: true
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

  const getStatusText = (status: string) => {
    switch (status) {
      case 'processed':
        return 'Processed'
      case 'processing':
        return 'Processing...'
      case 'error':
        return 'Error'
      default:
        return 'Unknown'
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl sm:text-3xl font-bold text-foreground">Document Manager</h1>
        <div className="text-sm text-muted-foreground">{documents?.length || 0} documents</div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Upload Documents</CardTitle>
          <CardDescription>Upload your FAQs, documentation, or knowledge base files to train your AI chatbot</CardDescription>
        </CardHeader>
        <CardContent>
          <div {...getRootProps()} className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${isDragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-gray-400'} ${uploading ? 'opacity-50 cursor-not-allowed' : ''}`}>
            <input {...getInputProps()} disabled={uploading} />
            <Upload className="mx-auto h-12 w-12 text-gray-400 mb-4" />
            {isDragActive ? (
              <p className="text-lg text-blue-600">Drop the files here...</p>
            ) : (
              <>
                <p className="text-lg text-gray-600 mb-2">Drag & drop files here, or click to select</p>
                <p className="text-sm text-gray-500">Supports PDF, DOCX, and CSV files</p>
              </>
            )}
            <Button variant="outline" className="mt-4"><Plus className="mr-2 h-4 w-4" />Select Files</Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Uploaded Documents</CardTitle>
          <CardDescription>Manage your uploaded documents and their processing status</CardDescription>
        </CardHeader>
        <CardContent>
          {!isLoading && (!documents || documents.length === 0) ? (
            <div className="text-center py-8 text-gray-500">No documents uploaded yet. Upload your first document to get started.</div>
          ) : (
            <div className="space-y-4">
              {isLoading ? (
                <div className="flex items-center justify-center h-32"><Progress value={35} className="h-2 w-48" /></div>
              ) : (
                documents!.map((doc) => (
                  <div key={doc.id} className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50">
                    <div className="flex items-center space-x-4 flex-1">
                      <File className="h-8 w-8 text-blue-500" />
                      <div className="flex-1">
                        <h3 className="font-medium text-gray-900">{doc.title || doc.original_filename}</h3>
                        <div className="flex items-center space-x-4 text-sm text-gray-500 mt-1">
                          <span>{(doc.file_size / 1024).toFixed(1)} KB</span>
                          <span>{doc.file_type.toUpperCase()}</span>
                          <div className="flex items-center space-x-1">
                            {getStatusIcon(doc.status)}
                            <span>{getStatusText(doc.status)}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Button variant="ghost" size="sm" onClick={() => setExpandedDocument(expandedDocument === doc.id ? null : doc.id)} title="Preview chunks"><Eye className="h-4 w-4" /></Button>
                      <Button variant="ghost" size="sm" onClick={() => reprocessDocument.mutate(doc.id)} title="Reprocess" disabled={reprocessDocument.isLoading}><RefreshCw className="h-4 w-4" /></Button>
                      <Button variant="ghost" size="sm" onClick={() => deleteDocument.mutate(doc.id)} title="Delete" className="text-red-600 hover:text-red-700" disabled={deleteDocument.isLoading}><Trash2 className="h-4 w-4" /></Button>
                    </div>
                  </div>
                ))
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {expandedDocument && (
        <Card>
          <CardHeader>
            <CardTitle>Document Chunks Preview</CardTitle>
            <CardDescription>First 3 chunks</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {(documentChunks || []).map((chunk) => (
                <div key={chunk.id} className="p-3 bg-white rounded border">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-medium text-gray-500">Chunk {chunk.chunk_index + 1}{chunk.page_number ? ` • Page ${chunk.page_number}` : ''}{chunk.word_count ? ` • ${chunk.word_count} words` : ''}</span>
                    {chunk.section_title && <span className="text-xs text-blue-600 bg-blue-100 px-2 py-1 rounded">{chunk.section_title}</span>}
                  </div>
                  <p className="text-sm text-gray-700 line-clamp-3">{chunk.content}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
