'use client';

import React, { createContext, useContext, useCallback, useState } from 'react';

// =============================================================================
// Types
// =============================================================================

interface PlatformConnection {
  id: string;
  platform: 'youtube' | 'tiktok' | 'instagram';
  username: string;
  channel_name?: string;
  profile_image_url?: string;
  status: 'active' | 'expired' | 'error';
  connected_at: string;
}

interface PlatformStatus {
  connected: boolean;
  count: number;
  active: number;
}

interface PlatformState {
  youtube: PlatformConnection[];
  tiktok: PlatformConnection[];
  instagram: PlatformConnection[];
  status: {
    youtube: PlatformStatus;
    tiktok: PlatformStatus;
    instagram: PlatformStatus;
  };
  isLoading: boolean;
  error: string | null;
}

interface PlatformContextType extends PlatformState {
  fetchConnections: () => Promise<void>;
  connectPlatform: (platform: 'youtube' | 'tiktok' | 'instagram') => Promise<void>;
  disconnectPlatform: (platform: string, connectionId: string) => Promise<void>;
  refreshToken: (platform: string, connectionId: string) => Promise<void>;
  clearError: () => void;
}

// =============================================================================
// Constants
// =============================================================================

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// =============================================================================
// Context
// =============================================================================

const PlatformContext = createContext<PlatformContextType | undefined>(undefined);

// =============================================================================
// Helper
// =============================================================================

function getAccessToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('reelflow_access_token');
}

async function apiRequest<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const token = getAccessToken();
  
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...options.headers,
  };
  
  if (token) {
    (headers as Record<string, string>)['Authorization'] = `Bearer ${token}`;
  }
  
  let response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });
  
  // Handle 401 - try to refresh token
  if (response.status === 401) {
    const refreshToken = localStorage.getItem('reelflow_refresh_token');
    
    if (refreshToken) {
      try {
        // Attempt to refresh the access token
        const refreshResponse = await fetch(`${API_BASE_URL}/api/auth/refresh`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ refresh_token: refreshToken }),
        });
        
        if (refreshResponse.ok) {
          const tokens = await refreshResponse.json();
          localStorage.setItem('reelflow_access_token', tokens.access_token);
          localStorage.setItem('reelflow_refresh_token', tokens.refresh_token);
          
          // Retry the original request with new token
          (headers as Record<string, string>)['Authorization'] = `Bearer ${tokens.access_token}`;
          response = await fetch(`${API_BASE_URL}${endpoint}`, {
            ...options,
            headers,
          });
        } else {
          // Refresh failed, redirect to login
          localStorage.removeItem('reelflow_access_token');
          localStorage.removeItem('reelflow_refresh_token');
          window.location.href = '/login?expired=true';
          throw new Error('Session expired. Please log in again.');
        }
      } catch (refreshError) {
        // Refresh failed, redirect to login
        localStorage.removeItem('reelflow_access_token');
        localStorage.removeItem('reelflow_refresh_token');
        window.location.href = '/login?expired=true';
        throw new Error('Session expired. Please log in again.');
      }
    } else {
      // No refresh token, redirect to login
      localStorage.removeItem('reelflow_access_token');
      window.location.href = '/login';
      throw new Error('Session expired. Please log in again.');
    }
  }
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Request failed' }));
    throw new Error(error.detail || 'Request failed');
  }
  
  return response.json();
}

// =============================================================================
// Provider
// =============================================================================

export function PlatformProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<PlatformState>({
    youtube: [],
    tiktok: [],
    instagram: [],
    status: {
      youtube: { connected: false, count: 0, active: 0 },
      tiktok: { connected: false, count: 0, active: 0 },
      instagram: { connected: false, count: 0, active: 0 },
    },
    isLoading: false,
    error: null,
  });

  const fetchConnections = useCallback(async () => {
    setState(prev => ({ ...prev, isLoading: true, error: null }));
    
    try {
      const [connections, status] = await Promise.all([
        apiRequest<{
          youtube: PlatformConnection[];
          tiktok: PlatformConnection[];
          instagram: PlatformConnection[];
        }>('/api/platforms/connections'),
        apiRequest<{
          youtube: PlatformStatus;
          tiktok: PlatformStatus;
          instagram: PlatformStatus;
        }>('/api/platforms/status'),
      ]);
      
      setState({
        youtube: connections.youtube,
        tiktok: connections.tiktok,
        instagram: connections.instagram,
        status,
        isLoading: false,
        error: null,
      });
    } catch (error) {
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: error instanceof Error ? error.message : 'Failed to fetch connections',
      }));
    }
  }, []);

  const connectPlatform = useCallback(async (platform: 'youtube' | 'tiktok' | 'instagram') => {
    setState(prev => ({ ...prev, isLoading: true, error: null }));
    
    try {
      const response = await apiRequest<{ auth_url: string }>(
        `/api/oauth/${platform}/connect`
      );
      
      // Redirect to OAuth provider
      window.location.href = response.auth_url;
    } catch (error) {
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: error instanceof Error ? error.message : 'Failed to connect platform',
      }));
      throw error;
    }
  }, []);

  const disconnectPlatform = useCallback(async (platform: string, connectionId: string) => {
    setState(prev => ({ ...prev, isLoading: true, error: null }));
    
    try {
      await apiRequest(`/api/platforms/disconnect/${platform}/${connectionId}`, {
        method: 'DELETE',
      });
      
      // Refresh connections
      await fetchConnections();
    } catch (error) {
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: error instanceof Error ? error.message : 'Failed to disconnect platform',
      }));
      throw error;
    }
  }, [fetchConnections]);

  const refreshToken = useCallback(async (platform: string, connectionId: string) => {
    setState(prev => ({ ...prev, isLoading: true, error: null }));
    
    try {
      await apiRequest(`/api/platforms/refresh/${platform}/${connectionId}`, {
        method: 'POST',
      });
      
      // Refresh connections
      await fetchConnections();
    } catch (error) {
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: error instanceof Error ? error.message : 'Failed to refresh token',
      }));
      throw error;
    }
  }, [fetchConnections]);

  const clearError = useCallback(() => {
    setState(prev => ({ ...prev, error: null }));
  }, []);

  const value: PlatformContextType = {
    ...state,
    fetchConnections,
    connectPlatform,
    disconnectPlatform,
    refreshToken,
    clearError,
  };

  return (
    <PlatformContext.Provider value={value}>
      {children}
    </PlatformContext.Provider>
  );
}

// =============================================================================
// Hook
// =============================================================================

export function usePlatforms() {
  const context = useContext(PlatformContext);
  
  if (context === undefined) {
    throw new Error('usePlatforms must be used within a PlatformProvider');
  }
  
  return context;
}
