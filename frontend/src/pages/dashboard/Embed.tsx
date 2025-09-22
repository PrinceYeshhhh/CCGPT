import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Copy, Eye, Settings, Palette, Upload, CheckCircle, RefreshCw, Trash2 } from 'lucide-react'
import toast from 'react-hot-toast'
import { useMutation, useQuery, useQueryClient } from 'react-query'
import { api } from '@/lib/api'

interface WidgetConfig { title: string; primary_color: string; position: string; welcome_message: string; placeholder: string; show_avatar?: boolean; max_messages?: number; enable_sound?: boolean; enable_typing_indicator?: boolean }
interface EmbedCode { id: number; code_name: string; embed_html?: string; embed_script: string; is_active: boolean; usage_count: number; last_used?: string; widget_config: WidgetConfig }

export function Embed() {
  const [copied, setCopied] = useState(false)
  const [settings, setSettings] = useState({ primaryColor: '#3b82f6', welcomeMessage: 'Hi! How can I help you today?', botName: 'CustomerCare Assistant', position: 'bottom-right' })
  const queryClient = useQueryClient()

  const { data: embedCodes } = useQuery<EmbedCode[]>('embed-codes', async () => {
    const response = await api.get('/api/v1/embed/codes')
    return response.data
  })

  const createEmbedCode = useMutation(async (payload: { code_name: string; config: WidgetConfig }) => {
    const response = await api.post('/api/v1/embed/generate', { workspace_id: 'default', code_name: payload.code_name, config: payload.config })
    return response.data
  }, { onSuccess: () => { queryClient.invalidateQueries('embed-codes'); toast.success('Embed code created successfully!') }, onError: () => { toast.error('Failed to create embed code') } })

  const regenerateEmbedCode = useMutation(async (id: number) => { await api.post(`/api/v1/embed/codes/${id}/regenerate`) }, { onSuccess: () => { queryClient.invalidateQueries('embed-codes'); toast.success('Embed code regenerated') }, onError: () => { toast.error('Failed to regenerate embed code') } })

  const deleteEmbedCode = useMutation(async (id: number) => { await api.delete(`/api/v1/embed/codes/${id}`) }, { onSuccess: () => { queryClient.invalidateQueries('embed-codes'); toast.success('Embed code deleted') }, onError: () => { toast.error('Failed to delete embed code') } })

  const embedCode = `<script>(function(){var s=document.createElement('script');s.src='${window.location.origin}/widget/widget.js';s.setAttribute('data-widget-id','your-widget-id');s.setAttribute('data-primary-color','${settings.primaryColor}');s.setAttribute('data-position','${settings.position}');document.head.appendChild(s);})();</script>`

  const copyToClipboard = (code?: string) => {
    navigator.clipboard.writeText(code || embedCode)
    setCopied(true)
    toast.success('Embed code copied to clipboard!')
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl sm:text-3xl font-bold text-foreground">Embed Widget</h1>
        <Button variant="outline"><Eye className="mr-2 h-4 w-4" />Preview Widget</Button>
      </div>

      <Card className="lg:col-span-2">
        <CardHeader>
          <CardTitle>Embed Code</CardTitle>
          <CardDescription>Copy and paste this code into your website's HTML to add the chat widget</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="relative">
            <pre className="bg-gray-900 text-green-400 p-4 rounded-lg text-sm overflow-x-auto"><code>{embedCode}</code></pre>
            <Button onClick={() => copyToClipboard()} className="absolute top-2 right-2" size="sm" variant={copied ? 'default' : 'outline'}>
              {copied ? (<><CheckCircle className="mr-2 h-4 w-4" />Copied!</>) : (<><Copy className="mr-2 h-4 w-4" />Copy</>)}
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Manage Codes</CardTitle>
          <CardDescription>Your generated embed codes</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {(embedCodes || []).map((code) => (
              <div key={code.id} className="p-4 border rounded-lg flex items-start justify-between">
                <div>
                  <div className="font-medium">{code.code_name}</div>
                  <div className="text-xs text-muted-foreground">Used {code.usage_count} times • {code.is_active ? 'Active' : 'Inactive'}</div>
                  <div className="mt-2 relative">
                    <textarea value={code.embed_html || code.embed_script} readOnly className="w-full border rounded p-2 text-sm font-mono h-20" />
                    <Button onClick={() => copyToClipboard(code.embed_html || code.embed_script)} className="absolute top-2 right-2" size="sm" variant="outline"><Copy className="h-4 w-4" /></Button>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <Button variant="ghost" size="sm" onClick={() => regenerateEmbedCode.mutate(code.id)}><RefreshCw className="h-4 w-4" /></Button>
                  <Button variant="ghost" size="sm" className="text-red-600" onClick={() => deleteEmbedCode.mutate(code.id)}><Trash2 className="h-4 w-4" /></Button>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Widget Customization</CardTitle>
          <CardDescription>Customize the appearance and behavior of your chat widget</CardDescription>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="appearance" className="w-full">
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="appearance"><Palette className="mr-2 h-4 w-4" />Appearance</TabsTrigger>
              <TabsTrigger value="messages"><Settings className="mr-2 h-4 w-4" />Messages</TabsTrigger>
              <TabsTrigger value="behavior"><Settings className="mr-2 h-4 w-4" />Behavior</TabsTrigger>
            </TabsList>
            <TabsContent value="appearance" className="space-y-6 mt-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <label className="text-sm font-medium">Primary Color</label>
                  <div className="flex space-x-2">
                    <Input type="color" value={settings.primaryColor} onChange={(e) => setSettings({ ...settings, primaryColor: e.target.value })} className="w-16 h-10 p-1" />
                    <Input value={settings.primaryColor} onChange={(e) => setSettings({ ...settings, primaryColor: e.target.value })} placeholder="#3b82f6" />
                  </div>
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Widget Position</label>
                  <select className="w-full p-2 border border-gray-300 rounded-md" value={settings.position} onChange={(e) => setSettings({ ...settings, position: e.target.value })}>
                    <option value="bottom-right">Bottom Right</option>
                    <option value="bottom-left">Bottom Left</option>
                    <option value="top-right">Top Right</option>
                    <option value="top-left">Top Left</option>
                  </select>
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Upload Logo</label>
                  <div className="flex items-center space-x-2">
                    <Button variant="outline" size="sm"><Upload className="mr-2 h-4 w-4" />Upload Logo</Button>
                    <span className="text-sm text-gray-500">Optional - 40x40px recommended</span>
                  </div>
                </div>
              </div>
            </TabsContent>
            <TabsContent value="messages" className="space-y-6 mt-6">
              <div className="space-y-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">Welcome Message</label>
                  <Input value={settings.welcomeMessage} onChange={(e) => setSettings({ ...settings, welcomeMessage: e.target.value })} placeholder="Hi! How can I help you today?" />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Bot Name</label>
                  <Input value={settings.botName} onChange={(e) => setSettings({ ...settings, botName: e.target.value })} placeholder="CustomerCare Assistant" />
                </div>
              </div>
            </TabsContent>
            <TabsContent value="behavior" className="space-y-6 mt-6">
              <div className="space-y-4">
                <div className="flex items-center space-x-3"><input type="checkbox" id="autoOpen" defaultChecked /><label htmlFor="autoOpen" className="text-sm font-medium">Auto-open widget for new visitors</label></div>
                <div className="flex items-center space-x-3"><input type="checkbox" id="showTyping" defaultChecked /><label htmlFor="showTyping" className="text-sm font-medium">Show typing indicator</label></div>
                <div className="flex items-center space-x-3"><input type="checkbox" id="soundNotifications" /><label htmlFor="soundNotifications" className="text-sm font-medium">Sound notifications</label></div>
              </div>
            </TabsContent>
          </Tabs>
          <div className="flex justify-end space-x-2 mt-6 pt-6 border-t">
            <Button variant="outline">Reset to Default</Button>
            <Button variant="primary" onClick={() => createEmbedCode.mutate({ code_name: 'Default Widget', config: { title: settings.botName, primary_color: settings.primaryColor, position: settings.position, welcome_message: settings.welcomeMessage, placeholder: 'Ask me anything...', show_avatar: true, max_messages: 50, enable_sound: true, enable_typing_indicator: true } })}>Save & Generate</Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
