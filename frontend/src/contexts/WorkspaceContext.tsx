import React, { createContext, useContext, useState, useEffect, useMemo, useCallback } from 'react';
import { api } from '@/lib/api';
import toast from 'react-hot-toast';

interface WorkspaceContextType {
  workspaceId: string | null;
  isLoading: boolean;
  error: string | null;
  refreshWorkspace: () => Promise<void>;
}

const WorkspaceContext = createContext<WorkspaceContextType | undefined>(undefined);

export function WorkspaceProvider({ children }: { children: React.ReactNode }) {
  const [workspaceId, setWorkspaceId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchWorkspaceId = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await api.get('/auth/me');
      if (res.data?.workspace_id) {
        setWorkspaceId(String(res.data.workspace_id));
      } else if (res.data?.id) {
        // Fallback: use user ID as workspace ID
        setWorkspaceId(String(res.data.id));
      } else {
        setError("Could not determine workspace ID.");
        toast.error("Failed to load workspace information.");
      }
    } catch (err) {
      console.error("Failed to fetch workspace ID:", err);
      setError("Failed to load workspace information.");
      toast.error("Failed to load workspace information.");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchWorkspaceId();
  }, [fetchWorkspaceId]);

  const refreshWorkspace = useCallback(async () => {
    await fetchWorkspaceId();
  }, [fetchWorkspaceId]);

  const value = useMemo(() => ({
    workspaceId,
    isLoading,
    error,
    refreshWorkspace,
  }), [workspaceId, isLoading, error, refreshWorkspace]);

  return (
    <WorkspaceContext.Provider value={value}>
      {children}
    </WorkspaceContext.Provider>
  );
}

export function useWorkspace() {
  const context = useContext(WorkspaceContext);
  if (context === undefined) {
    throw new Error('useWorkspace must be used within a WorkspaceProvider');
  }
  return context;
}