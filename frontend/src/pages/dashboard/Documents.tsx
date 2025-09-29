import React, { useCallback, useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { useDropzone } from 'react-dropzone';
import { 
  Upload, 
  File, 
  Trash2, 
  Eye, 
  RotateCcw,
  CheckCircle, 
  Clock, 
  AlertCircle,
  Plus
} from 'lucide-react';
import { api } from '@/lib/api';

interface Document {
  id: string;
  name: string;
  status: 'processing' | 'embedded' | 'active' | 'failed';
  uploadedAt: string;
  size: number;
}

export function Documents() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [workspaceId, setWorkspaceId] = useState<string>('');
  const [askText, setAskText] = useState<string>('');
  const [askLoading, setAskLoading] = useState<boolean>(false);
  const [askAnswer, setAskAnswer] = useState<string>('');
  const [docJobs, setDocJobs] = useState<Record<string, string>>({}); // documentId -> jobId
  const [jobStatuses, setJobStatuses] = useState<Record<string, string>>({}); // jobId -> status

  const fetchDocuments = useCallback(async () => {
    setIsLoading(true);
    try {
      const res = await api.get('/documents/');
      const items = res.data as any[];
      const mapped: Document[] = items.map((d: any) => ({
        id: d.id ?? String(d.document_id ?? d.uuid ?? d.name ?? Math.random()),
        name: d.name ?? d.filename ?? 'Document',
        status: (d.status ?? 'active') as Document['status'],
        uploadedAt: d.created_at ?? d.uploaded_at ?? new Date().toISOString().split('T')[0],
        size: d.size ?? 0,
      }));
      setDocuments(mapped);
    } catch (e) {
      console.error('Failed to fetch documents', e);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    setIsLoading(true);
    try {
      for (const file of acceptedFiles) {
        const form = new FormData();
        form.append('file', file);
        try {
          const res = await api.post('/documents/upload', form, {
            headers: { 'Content-Type': 'multipart/form-data' },
          });
          // Optimistically show processing
          const newId = String(res.data?.document_id ?? Math.random());
          const newJobId = String(res.data?.job_id ?? '');
          setDocuments(prev => [{
            id: newId,
            name: file.name,
            status: 'processing',
            uploadedAt: new Date().toISOString().split('T')[0],
            size: file.size,
          }, ...prev]);
          if (newJobId) {
            setDocJobs(prev => ({ ...prev, [newId]: newJobId }));
            setJobStatuses(prev => ({ ...prev, [newJobId]: 'queued' }));
          }
        } catch (e) {
          console.error('Upload failed', e);
        }
      }
      // Give backend a moment to enqueue, then refresh list
      setTimeout(fetchDocuments, 1000);
    } finally {
      setIsLoading(false);
    }
  }, [fetchDocuments]);

  // Polling for status updates after uploads (reduced frequency for better performance)
  React.useEffect(() => {
    const interval = setInterval(() => {
      fetchDocuments();
    }, 10000); // Changed from 3 seconds to 10 seconds
    return () => clearInterval(interval);
  }, [fetchDocuments]);

  // Poll job statuses for active processing documents
  React.useEffect(() => {
    const activeEntries = Object.entries(docJobs);
    if (activeEntries.length === 0) return;
    let cancelled = false;
    const poll = async () => {
      try {
        const updates: Record<string, string> = {};
        await Promise.all(activeEntries.map(async ([docId, jobId]) => {
          try {
            const res = await api.get(`/documents/jobs/${jobId}`);
            const status = res.data?.status as string;
            updates[jobId] = status || 'unknown';
            if (status === 'finished' || status === 'failed') {
              // Remove mapping and refresh list once
              setDocJobs(prev => {
                const next = { ...prev } as Record<string, string>;
                delete next[docId];
                return next;
              });
              fetchDocuments();
            }
          } catch {}
        }));
        if (!cancelled && Object.keys(updates).length) {
          setJobStatuses(prev => ({ ...prev, ...updates }));
        }
      } catch {}
    };
    const interval = setInterval(poll, 2000);
    return () => { cancelled = true; clearInterval(interval); };
  }, [docJobs, fetchDocuments]);

  // Fetch current user for workspace_id
  React.useEffect(() => {
    (async () => {
      try {
        const res = await api.get('/auth/me');
        const id = res.data?.id;
        if (id) setWorkspaceId(String(id));
      } catch {}
    })();
  }, []);

  const toggleSelect = (id: string) => {
    setSelectedIds(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else next.add(id);
      return next;
    });
  };

  const askAboutSelected = async () => {
    if (!askText.trim() || selectedIds.size === 0 || !workspaceId) return;
    setAskLoading(true);
    setAskAnswer('');
    try {
      const body = {
        workspace_id: workspaceId,
        session_id: undefined,
        query: askText.trim(),
        document_ids: Array.from(selectedIds),
        top_k: 6,
      };
      const res = await api.post('/production_rag/query', body);
      setAskAnswer(res.data?.answer ?? '');
    } catch (e) {
      setAskAnswer('Failed to get answer');
    } finally {
      setAskLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/msword': ['.doc'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'text/plain': ['.txt'],
      'text/markdown': ['.md']
    }
  });

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'processing':
        return <Clock className="h-5 w-5 text-yellow-500 animate-spin" />;
      case 'embedded':
        return <CheckCircle className="h-5 w-5 text-blue-500" />;
      case 'failed':
        return <AlertCircle className="h-5 w-5 text-red-500" />;
      default:
        return <File className="h-5 w-5 text-gray-400" />;
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'active':
        return 'Active';
      case 'processing':
        return 'Processing...';
      case 'embedded':
      case 'done':
        return 'Ready';
      case 'failed':
        return 'Failed';
      default:
        return 'Unknown';
    }
  };

  const deleteDocument = async (id: string) => {
    try {
      await api.delete(`/documents/${id}`);
      setDocuments(prev => prev.filter(doc => doc.id !== id));
      setDocJobs(prev => {
        const next = { ...prev } as Record<string, string>;
        delete next[id];
        return next;
      });
    } catch (e) {
      console.error('Failed to delete', e);
    }
  };

  const reprocessDocument = async (id: string) => {
    try {
      const res = await api.post(`/documents/${id}/reprocess`);
      const jobId = res.data?.job_id as string | undefined;
      setDocuments(prev => prev.map(d => d.id === id ? { ...d, status: 'processing' } as Document : d));
      if (jobId) {
        setDocJobs(prev => ({ ...prev, [id]: jobId }));
        setJobStatuses(prev => ({ ...prev, [jobId]: 'queued' }));
      }
    } catch (e) {
      console.error('Failed to reprocess', e);
    }
  };

  const formatFileSize = (bytes: number) => {
    const kb = bytes / 1024;
    return `${kb.toFixed(1)} KB`;
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl sm:text-3xl font-bold text-foreground">Document Manager</h1>
        <div className="text-sm text-muted-foreground">
          {documents.length} / 50 documents uploaded
        </div>
      </div>

      {/* Upload Area */}
      <Card>
        <CardHeader>
          <CardTitle>Upload Documents</CardTitle>
          <CardDescription>
            Upload your FAQs, documentation, or knowledge base files to train your AI chatbot
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div
            {...getRootProps()}
            className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
              isDragActive 
                ? 'border-blue-500 bg-blue-50' 
                : 'border-gray-300 hover:border-gray-400'
            }`}
          >
            <input {...getInputProps()} />
            <Upload className="mx-auto h-12 w-12 text-gray-400 mb-4" />
            {isDragActive ? (
              <p className="text-lg text-blue-600">Drop the files here...</p>
            ) : (
              <>
                <p className="text-lg text-gray-600 mb-2">
                  Drag & drop files here, or click to select
                </p>
                <p className="text-sm text-gray-500">
                  Supports PDF, DOC, DOCX, TXT, MD files (max 10MB each)
                </p>
              </>
            )}
            <Button variant="outline" className="mt-4">
              <Plus className="mr-2 h-4 w-4" />
              Select Files
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Document List */}
      <Card>
        <CardHeader>
          <CardTitle>Uploaded Documents</CardTitle>
          <CardDescription>
            Manage your uploaded documents and their processing status
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="text-center py-8 text-muted-foreground">Loading...</div>
          ) : documents.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              No documents uploaded yet. Upload your first document to get started.
            </div>
          ) : (
            <div className="space-y-4">
              {documents.map((doc) => (
                <div key={doc.id} className="flex items-center justify-between p-4 border rounded-lg hover:bg-accent/50 transition-colors">
                  <div className="flex items-center space-x-4 flex-1">
                    <input type="checkbox" className="mr-2" checked={selectedIds.has(doc.id)} onChange={() => toggleSelect(doc.id)} />
                    <File className="h-8 w-8 text-blue-500" />
                    <div className="flex-1">
                      <h3 className="font-medium text-foreground">{doc.name}</h3>
                      <div className="flex items-center space-x-4 text-sm text-muted-foreground mt-1">
                        <span>Uploaded: {doc.uploadedAt}</span>
                        <span>Size: {formatFileSize(doc.size)}</span>
                        <div className="flex items-center space-x-1">
                      {getStatusIcon(doc.status)}
                      <span>
                        {doc.status === 'processing' && docJobs[doc.id] && jobStatuses[docJobs[doc.id]]
                          ? `Processing... (${jobStatuses[docJobs[doc.id]]})`
                          : getStatusText(doc.status)}
                      </span>
                        </div>
                      </div>
                      {doc.status === 'processing' && (
                        <div className="mt-2">
                          <Progress
                            value={(() => {
                              const jid = docJobs[doc.id];
                              const st = jid ? jobStatuses[jid] : undefined;
                              if (st === 'finished') return 100;
                              if (st === 'failed') return 0;
                              if (st === 'started') return 75;
                              if (st === 'queued') return 25;
                              return 50;
                            })()}
                            className="h-2 w-48"
                          />
                          <span className="text-xs text-muted-foreground mt-1">Processing content...</span>
                        </div>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Button variant="ghost" size="sm">
                      <Eye className="h-4 w-4" />
                    </Button>
                    <Button 
                      variant="ghost" 
                      size="sm"
                      onClick={() => reprocessDocument(doc.id)}
                      title="Reprocess"
                    >
                      <RotateCcw className="h-4 w-4" />
                    </Button>
                    <Button 
                      variant="ghost" 
                      size="sm"
                      onClick={() => deleteDocument(doc.id)}
                      className="text-red-600 hover:text-red-700"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Processing Info */}
      <Card className="bg-blue-50 border-blue-200">
        <CardContent className="pt-6">
          <div className="flex items-start space-x-3">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                <CheckCircle className="h-5 w-5 text-blue-600" />
              </div>
            </div>
            <div>
              <h3 className="text-sm font-medium text-blue-800">How document processing works</h3>
              <div className="mt-2 text-sm text-blue-700">
                <p>1. <strong>Upload:</strong> Your documents are securely uploaded and stored</p>
                <p>2. <strong>Processing:</strong> Our AI analyzes and chunks your content</p>
                <p>3. <strong>Embedding:</strong> Content is converted into searchable embeddings</p>
                <p>4. <strong>Active:</strong> Your chatbot can now answer questions using this content</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Ask about selected documents */}
      <Card>
        <CardHeader>
          <CardTitle>Ask about Selected Documents</CardTitle>
          <CardDescription>
            Select one or more documents above, then ask a question to get an answer limited to those documents.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col sm:flex-row gap-2">
            <input
              className="flex-1 border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm bg-background text-foreground"
              placeholder="Type your question..."
              value={askText}
              onChange={(e) => setAskText(e.target.value)}
            />
            <Button onClick={askAboutSelected} disabled={askLoading || selectedIds.size === 0 || !askText.trim()}>
              {askLoading ? 'Asking...' : 'Ask'}
            </Button>
          </div>
          {askAnswer && (
            <div className="mt-4 p-3 rounded border bg-muted/50 text-sm whitespace-pre-wrap">
              {askAnswer}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}