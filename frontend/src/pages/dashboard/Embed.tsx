import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Copy, 
  Eye, 
  Settings, 
  Palette, 
  Upload,
  CheckCircle
} from 'lucide-react';
import toast from 'react-hot-toast';
import { api } from '@/lib/api';
import { WidgetPreview } from '@/components/common/WidgetPreview';

type EmbedCode = {
  id: string;
  code_name: string;
  embed_script: string;
  is_active: boolean;
  usage_count: number;
};

export function Embed() {
  const [copied, setCopied] = useState(false);
  const [settings, setSettings] = useState({
    primaryColor: '#3b82f6',
    secondaryColor: '#f8f9fa',
    textColor: '#111111',
    theme: 'light',
    showAvatar: true,
    avatarUrl: '',
    position: 'bottom-right',
    customCss: '',
    welcomeMessage: 'Hi! How can I help you today?',
    botName: 'CustomerCare Assistant',
    placeholder: 'Ask me anything...',
    maxMessages: 50,
    enableSound: true,
    enableTypingIndicator: true,
    enableWebSocket: true,
  });

  const [codes, setCodes] = useState<EmbedCode[]>([]);
  const [loading, setLoading] = useState(false);
  const [workspaceId, setWorkspaceId] = useState<string | null>(null);
  const [previewHtml, setPreviewHtml] = useState<string | null>(null);
  const [previewCss, setPreviewCss] = useState<string | null>(null);
  const [previewJs, setPreviewJs] = useState<string | null>(null);
  const [showWidgetPreview, setShowWidgetPreview] = useState(false);

  const fetchCodes = async () => {
    setLoading(true);
    try {
      const res = await api.get('/embed/codes');
      const list = (res.data || []).map((c: any) => ({
        id: String(c.id),
        code_name: c.code_name,
        embed_script: c.embed_script,
        is_active: c.is_active,
        usage_count: c.usage_count,
      })) as EmbedCode[];
      setCodes(list);
    } catch (e) {
      // toast handled globally
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    (async () => {
      try {
        const ws = await api.get('/workspace/settings');
        if (ws?.data?.id) setWorkspaceId(ws.data.id);
      } catch (e) {}
    })();
    fetchCodes();
  }, []);

  const selected = codes[0];
  const embedCode = selected
    ? (selected.embed_script || `<script src="${window.location.origin}/api/v1/embed/widget/${selected.id}" async></script>`)
    : `<script src="${window.location.origin}/api/v1/embed/widget/{code_id}" async></script>`;

  const copyToClipboard = () => {
    navigator.clipboard.writeText(embedCode);
    setCopied(true);
    toast.success('Embed code copied to clipboard!');
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl sm:text-3xl font-bold text-foreground">Embed Widget</h1>
        <Button variant="outline" onClick={async () => {
          if (!workspaceId) return;
          try {
            const res = await api.post('/embed/preview', {
              workspace_id: workspaceId,
              config: {
                title: settings.botName,
                welcome_message: settings.welcomeMessage,
                placeholder: settings.placeholder,
                primary_color: settings.primaryColor,
                secondary_color: settings.secondaryColor,
                text_color: settings.textColor,
                position: settings.position,
                show_avatar: settings.showAvatar,
                avatar_url: settings.avatarUrl || null,
                enable_sound: settings.enableSound,
                enable_typing_indicator: settings.enableTypingIndicator,
                enable_websocket: settings.enableWebSocket,
                theme: settings.theme,
                custom_css: settings.customCss || null,
                max_messages: settings.maxMessages,
              },
            });
            setPreviewHtml(res.data?.preview_html || null);
            setPreviewCss(res.data?.preview_css || null);
            setPreviewJs(res.data?.preview_js || null);
          } catch (e) {}
        }}>
          <Eye className="mr-2 h-4 w-4" />
          Preview Widget
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Embed Code */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Embed Code</CardTitle>
            <CardDescription>
              Copy and paste this code into your website's HTML to add the chat widget
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="relative">
              <pre className="bg-gray-900 text-green-400 p-4 rounded-lg text-sm overflow-x-auto">
                <code>{embedCode}</code>
              </pre>
              <Button 
                onClick={copyToClipboard}
                className="absolute top-2 right-2"
                size="sm"
                variant={copied ? "default" : "outline"}
              >
                {copied ? (
                  <>
                    <CheckCircle className="mr-2 h-4 w-4" />
                    Copied!
                  </>
                ) : (
                  <>
                    <Copy className="mr-2 h-4 w-4" />
                    Copy
                  </>
                )}
              </Button>
            </div>
            <div className="mt-4 p-4 bg-blue-50 rounded-lg">
              <h3 className="font-medium text-blue-800 mb-2">Installation Instructions</h3>
              <ol className="text-sm text-blue-700 space-y-1">
                <li>1. Copy the embed code above</li>
                <li>2. Paste it before the closing &lt;/body&gt; tag in your HTML</li>
                <li>3. The widget will automatically appear on your website</li>
                <li>4. Customize the appearance using the settings below</li>
              </ol>
            </div>
            <div className="mt-4">
              <div className="flex items-center justify-between mb-2">
                <div className="text-sm text-muted-foreground">Your embed codes</div>
                <Button size="sm" variant="outline" onClick={fetchCodes}>Refresh</Button>
              </div>
              <div className="space-y-2">
                {loading && <div className="text-sm">Loading...</div>}
                {!loading && codes.length === 0 && (
                  <div className="text-sm">No embed codes yet. Save changes below to generate one.</div>
                )}
                {codes.map((c) => (
                  <div key={c.id} className="flex items-center justify-between p-3 border rounded-lg">
                    <div className="text-sm">
                      <div className="font-medium">{c.code_name}</div>
                      <div className="text-muted-foreground">ID: {c.id}</div>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-muted-foreground">{c.usage_count} uses</span>
                      <Button size="sm" variant="outline" onClick={() => navigator.clipboard.writeText(`<script src=\"${window.location.origin}/api/v1/embed/widget/${c.id}\" async></script>`).then(() => toast.success('Script tag copied'))}>Copy tag</Button>
                      <Button size="sm" variant="outline" onClick={async () => {
                        try {
                          await api.post(`/embed/codes/${c.id}/regenerate`);
                          toast.success('Regenerated');
                          fetchCodes();
                        } catch (e) {}
                      }}>Regenerate</Button>
                      <Button size="sm" variant="destructive" onClick={async () => {
                        try {
                          await api.delete(`/embed/codes/${c.id}`);
                          toast.success('Deleted');
                          fetchCodes();
                        } catch (e) {}
                      }}>Delete</Button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Customization */}
      <Card>
        <CardHeader>
          <CardTitle>Widget Customization</CardTitle>
          <CardDescription>
            Customize the appearance and behavior of your chat widget
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="appearance" className="w-full">
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="appearance">
                <Palette className="mr-2 h-4 w-4" />
                Appearance
              </TabsTrigger>
              <TabsTrigger value="messages">
                <Settings className="mr-2 h-4 w-4" />
                Messages
              </TabsTrigger>
              <TabsTrigger value="behavior">
                <Settings className="mr-2 h-4 w-4" />
                Behavior
              </TabsTrigger>
            </TabsList>
            
            <TabsContent value="appearance" className="space-y-6 mt-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <label className="text-sm font-medium">Primary Color</label>
                  <div className="flex space-x-2">
                    <Input
                      type="color"
                      value={settings.primaryColor}
                      onChange={(e) => setSettings({...settings, primaryColor: e.target.value})}
                      className="w-16 h-10 p-1"
                    />
                    <Input
                      value={settings.primaryColor}
                      onChange={(e) => setSettings({...settings, primaryColor: e.target.value})}
                      placeholder="#3b82f6"
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Secondary Color</label>
                  <div className="flex space-x-2">
                    <Input type="color" value={settings.secondaryColor} onChange={(e) => setSettings({...settings, secondaryColor: e.target.value})} className="w-16 h-10 p-1" />
                    <Input value={settings.secondaryColor} onChange={(e) => setSettings({...settings, secondaryColor: e.target.value})} placeholder="#f8f9fa" />
                  </div>
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Text Color</label>
                  <div className="flex space-x-2">
                    <Input type="color" value={settings.textColor} onChange={(e) => setSettings({...settings, textColor: e.target.value})} className="w-16 h-10 p-1" />
                    <Input value={settings.textColor} onChange={(e) => setSettings({...settings, textColor: e.target.value})} placeholder="#111111" />
                  </div>
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Widget Position</label>
                  <select 
                    className="w-full p-2 border border-input bg-background text-foreground rounded-md"
                    value={settings.position}
                    onChange={(e) => setSettings({...settings, position: e.target.value})}
                  >
                    <option value="bottom-right">Bottom Right</option>
                    <option value="bottom-left">Bottom Left</option>
                    <option value="top-right">Top Right</option>
                    <option value="top-left">Top Left</option>
                  </select>
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Theme</label>
                  <select 
                    className="w-full p-2 border border-input bg-background text-foreground rounded-md"
                    value={settings.theme}
                    onChange={(e) => setSettings({...settings, theme: e.target.value})}
                  >
                    <option value="light">Light</option>
                    <option value="dark">Dark</option>
                    <option value="custom">Custom</option>
                  </select>
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Show Avatar</label>
                  <div className="flex items-center space-x-3">
                    <input type="checkbox" className="w-4 h-4" checked={settings.showAvatar} onChange={(e) => setSettings({...settings, showAvatar: e.target.checked})} />
                    <span className="text-sm text-muted-foreground">Display robot avatar in header</span>
                  </div>
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Avatar URL (optional)</label>
                  <Input value={settings.avatarUrl} onChange={(e) => setSettings({...settings, avatarUrl: e.target.value})} placeholder="https://.../avatar.png" />
                </div>
                <div className="space-y-2 md:col-span-2">
                  <label className="text-sm font-medium">Custom CSS (applied inside widget)</label>
                  <textarea
                    value={settings.customCss}
                    onChange={(e) => setSettings({...settings, customCss: e.target.value})}
                    placeholder=":root { --ccgpt-primary: #4f46e5; }"
                    className="w-full min-h-[100px] p-2 border border-input rounded-md bg-background text-foreground"
                  />
                </div>
              </div>
            </TabsContent>
            <TabsContent value="messages" className="space-y-6 mt-6">
              <div className="space-y-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">Welcome Message</label>
                  <Input
                    value={settings.welcomeMessage}
                    onChange={(e) => setSettings({...settings, welcomeMessage: e.target.value})}
                    placeholder="Hi! How can I help you today?"
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Bot Name</label>
                  <Input
                    value={settings.botName}
                    onChange={(e) => setSettings({...settings, botName: e.target.value})}
                    placeholder="CustomerCare Assistant"
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Placeholder Text</label>
                  <Input
                    value={settings.placeholder}
                    onChange={(e) => setSettings({...settings, placeholder: e.target.value})}
                    placeholder="Type your message here..."
                    className="bg-background text-foreground"
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Max Messages Stored</label>
                  <Input
                    type="number"
                    min="1"
                    max="500"
                    value={String(settings.maxMessages)}
                    onChange={(e) => setSettings({...settings, maxMessages: Number(e.target.value || 0)})}
                    className="bg-background text-foreground"
                  />
                </div>
              </div>
            </TabsContent>
            <TabsContent value="behavior" className="space-y-6 mt-6">
              <div className="space-y-4">
                <div className="flex items-center space-x-3">
                  <input type="checkbox" id="showTyping" className="w-4 h-4 text-blue-600 bg-background border-input rounded focus:ring-blue-500" checked={settings.enableTypingIndicator} onChange={(e) => setSettings({...settings, enableTypingIndicator: e.target.checked})} />
                  <label htmlFor="showTyping" className="text-sm font-medium">
                    Show typing indicator
                  </label>
                </div>
                <div className="flex items-center space-x-3">
                  <input type="checkbox" id="soundNotifications" className="w-4 h-4 text-blue-600 bg-background border-input rounded focus:ring-blue-500" checked={settings.enableSound} onChange={(e) => setSettings({...settings, enableSound: e.target.checked})} />
                  <label htmlFor="soundNotifications" className="text-sm font-medium">
                    Sound notifications
                  </label>
                </div>
                <div className="flex items-center space-x-3">
                  <input type="checkbox" id="wsToggle" className="w-4 h-4 text-blue-600 bg-background border-input rounded focus:ring-blue-500" checked={settings.enableWebSocket} onChange={(e) => setSettings({...settings, enableWebSocket: e.target.checked})} />
                  <label htmlFor="wsToggle" className="text-sm font-medium">
                    Use WebSocket (enable streaming and faster responses)
                  </label>
                </div>
              </div>
            </TabsContent>
          </Tabs>
          <div className="flex justify-end space-x-2 mt-6 pt-6 border-t">
            <Button variant="outline" onClick={() => setSettings({
              primaryColor: '#3b82f6',
              secondaryColor: '#f8f9fa',
              textColor: '#111111',
              theme: 'light',
              showAvatar: true,
              avatarUrl: '',
              position: 'bottom-right',
              customCss: '',
              welcomeMessage: 'Hi! How can I help you today?',
              botName: 'CustomerCare Assistant',
              placeholder: 'Ask me anything...',
              maxMessages: 50,
              enableSound: true,
              enableTypingIndicator: true,
              enableWebSocket: true,
            })}>Reset to Default</Button>
            <Button
              disabled={!workspaceId}
              variant="primary"
              onClick={async () => {
                if (!workspaceId) {
                  toast.error('Workspace not loaded yet');
                  return;
                }
                try {
                  await api.post('/embed/generate', {
                    workspace_id: workspaceId,
                    code_name: `Widget ${new Date().toISOString().slice(0, 10)}`,
                    config: {
                      title: settings.botName,
                      welcome_message: settings.welcomeMessage,
                      placeholder: settings.placeholder,
                      primary_color: settings.primaryColor,
                      secondary_color: settings.secondaryColor,
                      text_color: settings.textColor,
                      position: settings.position,
                      show_avatar: settings.showAvatar,
                      avatar_url: settings.avatarUrl || null,
                      enable_sound: settings.enableSound,
                      enable_typing_indicator: settings.enableTypingIndicator,
                      enable_websocket: settings.enableWebSocket,
                      theme: settings.theme,
                      custom_css: settings.customCss || null,
                      max_messages: settings.maxMessages,
                    },
                  });
                  toast.success('Embed code created');
                  fetchCodes();
                } catch (e) {
                  // handled by interceptor
                }
              }}
            >
              Generate Embed Code
            </Button>
            <Button
              disabled={!selected}
              variant="outline"
              onClick={async () => {
                if (!selected) return;
                try {
                  await api.put(`/embed/codes/${selected.id}`, {
                    widget_config: {
                      title: settings.botName,
                      welcome_message: settings.welcomeMessage,
                      placeholder: settings.placeholder,
                      primary_color: settings.primaryColor,
                      secondary_color: settings.secondaryColor,
                      text_color: settings.textColor,
                      position: settings.position,
                      show_avatar: settings.showAvatar,
                      avatar_url: settings.avatarUrl || null,
                      enable_sound: settings.enableSound,
                      enable_typing_indicator: settings.enableTypingIndicator,
                      enable_websocket: settings.enableWebSocket,
                      theme: settings.theme,
                      custom_css: settings.customCss || null,
                      max_messages: settings.maxMessages,
                    },
                  });
                  toast.success('Settings saved');
                  fetchCodes();
                } catch (e) {}
              }}
            >
              Save Settings
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Widget Preview */}
      <Card>
        <CardHeader>
          <CardTitle>Widget Preview</CardTitle>
          <CardDescription>
            This is how your chat widget will appear on your website
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-2 mb-4">
            <Button
              variant="outline"
              onClick={() => setShowWidgetPreview(true)}
            >
              <Eye className="mr-2 h-4 w-4" />
              Preview Widget
            </Button>
            <Button
              variant="outline"
              disabled={!workspaceId}
              onClick={async () => {
                if (!workspaceId) return;
                try {
                  const res = await api.post('/embed/preview', {
                    workspace_id: workspaceId,
                    config: {
                      title: settings.botName,
                      welcome_message: settings.welcomeMessage,
                      placeholder: settings.placeholder,
                      primary_color: settings.primaryColor,
                      secondary_color: settings.secondaryColor,
                      text_color: settings.textColor,
                      position: settings.position,
                      show_avatar: settings.showAvatar,
                      avatar_url: settings.avatarUrl || null,
                      enable_sound: settings.enableSound,
                      enable_typing_indicator: settings.enableTypingIndicator,
                      enable_websocket: settings.enableWebSocket,
                      theme: settings.theme,
                      custom_css: settings.customCss || null,
                      max_messages: settings.maxMessages,
                    },
                  });
                  setPreviewHtml(res.data?.preview_html || null);
                  setPreviewCss(res.data?.preview_css || null);
                  setPreviewJs(res.data?.preview_js || null);
                } catch (e) {}
              }}
            >
              Refresh Preview
            </Button>
          </div>
          {previewHtml ? (
            <div className="relative border rounded-lg overflow-hidden">
              <iframe
                title="Widget Preview"
                style={{ width: '100%', height: 520, border: '0', background: '#fff' }}
                srcDoc={`<!DOCTYPE html><html><head><meta charset=\"utf-8\" />${previewCss ? `<style>${previewCss}</style>` : ''}</head><body>${previewHtml}${previewJs ? `<script>${previewJs}</script>` : ''}</body></html>`}
              />
            </div>
          ) : (
            <div className="relative bg-gray-100 rounded-lg p-8 min-h-[300px] overflow-hidden">
              {/* Mock website content */}
              <div className="text-center text-gray-500 mt-20">
                <h3 className="text-lg font-medium mb-2">Your Website Content</h3>
                <p className="text-muted-foreground">Click Refresh Preview to load a live preview.</p>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Widget Preview Modal */}
      <WidgetPreview
        isOpen={showWidgetPreview}
        onClose={() => setShowWidgetPreview(false)}
        config={{
          title: settings.botName,
          welcome_message: settings.welcomeMessage,
          placeholder: settings.placeholder,
          primary_color: settings.primaryColor,
          secondary_color: settings.secondaryColor,
          text_color: settings.textColor,
          position: settings.position,
          show_avatar: settings.showAvatar,
          avatar_url: settings.avatarUrl || undefined,
          enable_sound: settings.enableSound,
          enable_typing_indicator: settings.enableTypingIndicator,
          enable_websocket: settings.enableWebSocket,
          theme: settings.theme,
          custom_css: settings.customCss || undefined,
          max_messages: settings.maxMessages,
        }}
      />
    </div>
  );
}