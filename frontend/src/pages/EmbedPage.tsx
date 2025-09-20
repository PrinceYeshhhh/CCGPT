import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import { useForm } from 'react-hook-form'
import { Code, Copy, Plus, Settings, Eye, Trash2, RefreshCw } from 'lucide-react'
import { api } from '../lib/api'
import { EmbedCode, WidgetConfig } from '../types'
import { LoadingSpinner } from '../components/LoadingSpinner'
import { formatDate } from '../lib/utils'
import toast from 'react-hot-toast'

interface CreateEmbedCodeFormProps {
  onSubmit: (data: { code_name: string; config: WidgetConfig }) => void
  onCancel: () => void
  isLoading: boolean
}

function CreateEmbedCodeForm({ onSubmit, onCancel, isLoading }: CreateEmbedCodeFormProps) {
  const { register, handleSubmit, watch } = useForm<{
    code_name: string
    title: string
    primary_color: string
    position: string
    welcome_message: string
    placeholder: string
  }>({
    defaultValues: {
      code_name: '',
      title: 'Customer Support',
      primary_color: '#4f46e5',
      position: 'bottom-right',
      welcome_message: 'Hello! How can I help you today?',
      placeholder: 'Ask me anything...'
    }
  })

  const watchedColor = watch('primary_color')

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex min-h-screen items-center justify-center p-4">
        <div className="fixed inset-0 bg-gray-500 bg-opacity-75" onClick={onCancel} />
        <div className="relative bg-white rounded-lg p-6 w-full max-w-md">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Create Embed Code</h3>
          <form onSubmit={handleSubmit((data) => onSubmit({
            code_name: data.code_name,
            config: {
              title: data.title,
              primary_color: data.primary_color,
              position: data.position as any,
              welcome_message: data.welcome_message,
              placeholder: data.placeholder,
              show_avatar: true,
              max_messages: 50,
              enable_sound: true,
              enable_typing_indicator: true
            }
          }))}>
            <div className="space-y-4">
              <div>
                <label className="label">Code Name</label>
                <input
                  {...register('code_name', { required: true })}
                  type="text"
                  className="input mt-1"
                  placeholder="e.g., Main Website Widget"
                />
              </div>
              <div>
                <label className="label">Widget Title</label>
                <input
                  {...register('title')}
                  type="text"
                  className="input mt-1"
                  placeholder="e.g., Customer Support"
                />
              </div>
              <div>
                <label className="label">Welcome Message</label>
                <input
                  {...register('welcome_message')}
                  type="text"
                  className="input mt-1"
                  placeholder="e.g., Hello! How can I help you today?"
                />
              </div>
              <div>
                <label className="label">Placeholder Text</label>
                <input
                  {...register('placeholder')}
                  type="text"
                  className="input mt-1"
                  placeholder="e.g., Ask me anything..."
                />
              </div>
              <div>
                <label className="label">Primary Color</label>
                <div className="flex items-center space-x-2 mt-1">
                  <input
                    {...register('primary_color')}
                    type="color"
                    className="h-10 w-16 rounded border border-gray-300"
                  />
                  <input
                    {...register('primary_color')}
                    type="text"
                    className="input flex-1"
                    placeholder="#4f46e5"
                  />
                </div>
              </div>
              <div>
                <label className="label">Position</label>
                <select {...register('position')} className="input mt-1">
                  <option value="bottom-right">Bottom Right</option>
                  <option value="bottom-left">Bottom Left</option>
                  <option value="top-right">Top Right</option>
                  <option value="top-left">Top Left</option>
                </select>
              </div>
            </div>
            <div className="flex justify-end space-x-3 mt-6">
              <button
                type="button"
                onClick={onCancel}
                className="btn btn-outline"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isLoading}
                className="btn btn-primary"
              >
                {isLoading ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent mr-2" />
                    Creating...
                  </>
                ) : (
                  'Create'
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}

export function EmbedPage() {
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [showPreview, setShowPreview] = useState<string | null>(null)
  const queryClient = useQueryClient()

  const { data: embedCodes, isLoading } = useQuery<EmbedCode[]>(
    'embed-codes',
    async () => {
      const response = await api.get('/api/v1/embed/codes')
      return response.data
    }
  )

  const createEmbedCode = useMutation(
    async (data: { code_name: string; config: WidgetConfig }) => {
      const response = await api.post('/api/v1/embed/generate', {
        workspace_id: 'default', // This should come from user context
        code_name: data.code_name,
        config: data.config
      })
      return response.data
    },
    {
      onSuccess: () => {
        queryClient.invalidateQueries('embed-codes')
        setShowCreateForm(false)
        toast.success('Embed code created successfully!')
      },
      onError: (error: any) => {
        toast.error(error.response?.data?.detail || 'Failed to create embed code')
      }
    }
  )

  const deleteEmbedCode = useMutation(
    async (id: string) => {
      await api.delete(`/api/v1/embed/codes/${id}`)
    },
    {
      onSuccess: () => {
        queryClient.invalidateQueries('embed-codes')
        toast.success('Embed code deleted successfully!')
      },
      onError: () => {
        toast.error('Failed to delete embed code')
      }
    }
  )

  const regenerateEmbedCode = useMutation(
    async (id: string) => {
      await api.post(`/api/v1/embed/codes/${id}/regenerate`)
    },
    {
      onSuccess: () => {
        queryClient.invalidateQueries('embed-codes')
        toast.success('Embed code regenerated successfully!')
      },
      onError: () => {
        toast.error('Failed to regenerate embed code')
      }
    }
  )

  const copyEmbedCode = (code: string) => {
    navigator.clipboard.writeText(code)
    toast.success('Embed code copied to clipboard!')
  }

  const handleCreateEmbedCode = (formData: { code_name: string; config: WidgetConfig }) => {
    createEmbedCode.mutate(formData)
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
      <div className="md:flex md:items-center md:justify-between">
        <div className="min-w-0 flex-1">
          <h2 className="text-2xl font-bold text-gray-900">Embed Codes</h2>
          <p className="text-gray-500">Create and manage embed codes for your website</p>
        </div>
        <button
          onClick={() => setShowCreateForm(true)}
          className="btn btn-primary"
        >
          <Plus className="mr-2 h-4 w-4" />
          Create Embed Code
        </button>
      </div>

      {/* Embed Codes List */}
      <div className="grid gap-6">
        {embedCodes && embedCodes.length > 0 ? (
          embedCodes.map((code) => (
            <div key={code.id} className="card p-6">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-lg font-medium text-gray-900">{code.code_name}</h3>
                  <p className="text-sm text-gray-500">
                    Used {code.usage_count} times • Last used {code.last_used ? formatDate(code.last_used) : 'Never'}
                  </p>
                </div>
                <div className="flex items-center space-x-2">
                  <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                    code.is_active 
                      ? 'text-green-600 bg-green-100' 
                      : 'text-gray-600 bg-gray-100'
                  }`}>
                    {code.is_active ? 'Active' : 'Inactive'}
                  </span>
                  <button 
                    onClick={() => setShowPreview(showPreview === code.id.toString() ? null : code.id.toString())}
                    className="p-2 text-gray-400 hover:text-gray-600"
                    title="Preview widget"
                  >
                    <Eye className="h-4 w-4" />
                  </button>
                  <button 
                    onClick={() => regenerateEmbedCode.mutate(code.id.toString())}
                    disabled={regenerateEmbedCode.isLoading}
                    className="p-2 text-gray-400 hover:text-gray-600"
                    title="Regenerate code"
                  >
                    <RefreshCw className="h-4 w-4" />
                  </button>
                  <button 
                    onClick={() => deleteEmbedCode.mutate(code.id.toString())}
                    disabled={deleteEmbedCode.isLoading}
                    className="p-2 text-gray-400 hover:text-red-600"
                    title="Delete embed code"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="label">Embed Code</label>
                  <div className="mt-1 relative">
                    <textarea
                      value={code.embed_html || code.embed_script}
                      readOnly
                      className="input font-mono text-sm h-20 resize-none"
                    />
                    <button
                      onClick={() => copyEmbedCode(code.embed_html || code.embed_script)}
                      className="absolute top-2 right-2 p-1 text-gray-400 hover:text-gray-600"
                    >
                      <Copy className="h-4 w-4" />
                    </button>
                  </div>
                  <p className="mt-1 text-xs text-gray-500">
                    Copy this code and paste it before the closing &lt;/body&gt; tag of your website
                  </p>
                </div>

                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <span className="text-gray-500">Title:</span>
                    <span className="ml-2 font-medium">{code.widget_config.title}</span>
                  </div>
                  <div>
                    <span className="text-gray-500">Color:</span>
                    <span className="ml-2 font-medium">{code.widget_config.primary_color}</span>
                  </div>
                  <div>
                    <span className="text-gray-500">Position:</span>
                    <span className="ml-2 font-medium">{code.widget_config.position}</span>
                  </div>
                </div>

                {/* Widget Preview */}
                {showPreview === code.id.toString() && (
                  <div className="mt-4 p-4 bg-gray-50 rounded-lg">
                    <h4 className="text-sm font-medium text-gray-900 mb-3">Widget Preview</h4>
                    <div className="bg-white border rounded-lg p-4 h-64 overflow-auto">
                      <div className="text-sm text-gray-500">
                        Widget preview would be rendered here in a real implementation.
                        This would show the actual widget with the configured settings.
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))
        ) : (
          <div className="text-center py-12">
            <Code className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No embed codes</h3>
            <p className="mt-1 text-sm text-gray-500">
              Get started by creating your first embed code.
            </p>
          </div>
        )}
      </div>

      {/* Create Form Modal */}
      {showCreateForm && (
        <CreateEmbedCodeForm
          onSubmit={handleCreateEmbedCode}
          onCancel={() => setShowCreateForm(false)}
          isLoading={createEmbedCode.isLoading}
        />
      )}
    </div>
  )
}
