import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import { useForm } from 'react-hook-form'
import { Save, Upload, Trash2, AlertCircle } from 'lucide-react'
import { api } from '../lib/api'
import { LoadingSpinner } from '../components/LoadingSpinner'
import toast from 'react-hot-toast'

interface WorkspaceSettings {
  id: string
  name: string
  description?: string
  logo_url?: string
  website_url?: string
  support_email?: string
  timezone: string
  created_at: string
  updated_at: string
}

interface WorkspaceUpdateData {
  name: string
  description?: string
  website_url?: string
  support_email?: string
  timezone: string
}

const timezones = [
  'UTC',
  'America/New_York',
  'America/Chicago',
  'America/Denver',
  'America/Los_Angeles',
  'Europe/London',
  'Europe/Paris',
  'Europe/Berlin',
  'Asia/Tokyo',
  'Asia/Shanghai',
  'Asia/Kolkata',
  'Australia/Sydney'
]

export function SettingsPage() {
  const [isUploading, setIsUploading] = useState(false)
  const queryClient = useQueryClient()

  const { data: settings, isLoading: settingsLoading } = useQuery<WorkspaceSettings>(
    'workspace-settings',
    async () => {
      const response = await api.get('/api/v1/workspace/settings')
      return response.data
    }
  )

  const { register, handleSubmit, formState: { errors }, reset } = useForm<WorkspaceUpdateData>({
    defaultValues: settings
  })

  const updateSettingsMutation = useMutation(
    async (data: WorkspaceUpdateData) => {
      const response = await api.patch('/api/v1/workspace/settings', data)
      return response.data
    },
    {
      onSuccess: () => {
        toast.success('Settings updated successfully')
        queryClient.invalidateQueries('workspace-settings')
      },
      onError: () => {
        toast.error('Failed to update settings')
      }
    }
  )

  const handleLogoUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    if (file.size > 5 * 1024 * 1024) { // 5MB limit
      toast.error('Logo file size must be less than 5MB')
      return
    }

    if (!file.type.startsWith('image/')) {
      toast.error('Please upload an image file')
      return
    }

    setIsUploading(true)
    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('type', 'workspace_logo')

      const response = await api.post('/api/v1/workspace/upload-logo', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })

      toast.success('Logo uploaded successfully')
      queryClient.invalidateQueries('workspace-settings')
    } catch (error) {
      toast.error('Failed to upload logo')
    } finally {
      setIsUploading(false)
    }
  }

  const handleDeleteLogo = async () => {
    try {
      await api.delete('/api/v1/workspace/logo')
      toast.success('Logo deleted successfully')
      queryClient.invalidateQueries('workspace-settings')
    } catch (error) {
      toast.error('Failed to delete logo')
    }
  }

  const onSubmit = (data: WorkspaceUpdateData) => {
    updateSettingsMutation.mutate(data)
  }

  if (settingsLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Workspace Settings</h2>
        <p className="text-gray-500">Manage your workspace configuration and preferences</p>
      </div>

      {/* General Settings */}
      <div className="card p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">General Information</h3>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Workspace Name *
              </label>
              <input
                {...register('name', { required: 'Workspace name is required' })}
                type="text"
                className="input"
                placeholder="Enter workspace name"
              />
              {errors.name && (
                <p className="mt-1 text-sm text-red-600">{errors.name.message}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Timezone
              </label>
              <select
                {...register('timezone')}
                className="input"
              >
                {timezones.map((tz) => (
                  <option key={tz} value={tz}>{tz}</option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Description
            </label>
            <textarea
              {...register('description')}
              rows={3}
              className="input"
              placeholder="Enter workspace description"
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Website URL
              </label>
              <input
                {...register('website_url')}
                type="url"
                className="input"
                placeholder="https://example.com"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Support Email
              </label>
              <input
                {...register('support_email')}
                type="email"
                className="input"
                placeholder="support@example.com"
              />
            </div>
          </div>

          <div className="flex justify-end">
            <button
              type="submit"
              disabled={updateSettingsMutation.isLoading}
              className="btn btn-primary"
            >
              {updateSettingsMutation.isLoading ? (
                <>
                  <LoadingSpinner size="sm" className="mr-2" />
                  Saving...
                </>
              ) : (
                <>
                  <Save className="h-4 w-4 mr-2" />
                  Save Changes
                </>
              )}
            </button>
          </div>
        </form>
      </div>

      {/* Logo Settings */}
      <div className="card p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Workspace Logo</h3>
        <div className="flex items-start space-x-6">
          <div className="flex-shrink-0">
            {settings?.logo_url ? (
              <img
                src={settings.logo_url}
                alt="Workspace logo"
                className="h-20 w-20 rounded-lg object-cover border border-gray-200"
              />
            ) : (
              <div className="h-20 w-20 rounded-lg bg-gray-100 border border-gray-200 flex items-center justify-center">
                <span className="text-gray-400 text-sm">No logo</span>
              </div>
            )}
          </div>
          <div className="flex-1">
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Upload Logo
                </label>
                <input
                  type="file"
                  accept="image/*"
                  onChange={handleLogoUpload}
                  disabled={isUploading}
                  className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                />
                <p className="mt-1 text-sm text-gray-500">
                  PNG, JPG, GIF up to 5MB. Recommended size: 200x200px
                </p>
              </div>
              {settings?.logo_url && (
                <button
                  onClick={handleDeleteLogo}
                  className="btn btn-outline btn-sm text-red-600 hover:text-red-700"
                >
                  <Trash2 className="h-4 w-4 mr-2" />
                  Remove Logo
                </button>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* API Keys */}
      <div className="card p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">API Keys</h3>
        <div className="space-y-4">
          <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
            <div>
              <h4 className="text-sm font-medium text-gray-900">Workspace API Key</h4>
              <p className="text-sm text-gray-500">Used for backend API access</p>
            </div>
            <button className="btn btn-outline btn-sm">
              Regenerate
            </button>
          </div>
          <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
            <div>
              <h4 className="text-sm font-medium text-gray-900">Client API Keys</h4>
              <p className="text-sm text-gray-500">Used for embeddable widgets</p>
            </div>
            <button className="btn btn-outline btn-sm">
              Manage
            </button>
          </div>
        </div>
      </div>

      {/* Danger Zone */}
      <div className="card p-6 border-red-200 bg-red-50">
        <h3 className="text-lg font-medium text-red-900 mb-4">Danger Zone</h3>
        <div className="space-y-4">
          <div className="flex items-center justify-between p-4 bg-white rounded-lg border border-red-200">
            <div>
              <h4 className="text-sm font-medium text-red-900">Delete Workspace</h4>
              <p className="text-sm text-red-600">
                Permanently delete this workspace and all associated data. This action cannot be undone.
              </p>
            </div>
            <button className="btn btn-outline btn-sm text-red-600 hover:text-red-700 border-red-300">
              Delete Workspace
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}