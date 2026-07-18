import axios from 'axios';
import { useChatStore } from '../store/chatStore';

const API_BASE_URL = '/api';

export const arthaApi = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add a request interceptor to inject the JWT token
arthaApi.interceptors.request.use(
  (config) => {
    const token = useChatStore.getState().authToken;
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for handling auth errors
arthaApi.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      useChatStore.getState().logout();
    }
    return Promise.reject(error);
  }
);

/**
 * Handles streaming responses from the /ask endpoint.
 * We use the native fetch API here because Axios doesn't support 
 * consuming Server-Sent Events (SSE) or streaming response bodies easily.
 */
export const askQuestionStream = async (
  question: string,
  domainFilters: string[] | null,
  conversationId: string | null,
  onStart: (convId: string) => void,
  onChunk: (text: string) => void,
  onCitations: (citations: any[]) => void,
  onEnd: (messageId: string) => void,
  onError: (error: string) => void,
  abortSignal?: AbortSignal
) => {
  try {
    const token = useChatStore.getState().authToken;
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_BASE_URL}/ask`, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        question,
        domain_filters: domainFilters?.length ? domainFilters : null,
        conversation_id: conversationId,
        stream: true,
      }),
      signal: abortSignal,
    });

    if (!response.ok) {
      let errorMsg = 'An error occurred';
      try {
        const errorData = await response.json();
        errorMsg = errorData.detail || errorMsg;
      } catch (e) {
        errorMsg = `HTTP Error ${response.status}`;
      }
      throw new Error(errorMsg);
    }

    const reader = response.body?.getReader();
    const decoder = new TextDecoder('utf-8');

    if (!reader) {
      throw new Error('Streaming not supported by browser');
    }

    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      
      // Process SSE lines
      const lines = buffer.split('\n\n');
      buffer = lines.pop() || ''; // Keep the incomplete line in the buffer

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const dataStr = line.slice(6);
          if (dataStr.trim() === '[DONE]') continue;
          
          try {
            const data = JSON.parse(dataStr);
            if (data.type === 'start') {
              onStart(data.conversation_id);
            } else if (data.type === 'content') {
              onChunk(data.content);
            } else if (data.type === 'citations') {
              onCitations(data.citations);
            } else if (data.type === 'end') {
              onEnd(data.message_id);
            } else if (data.type === 'error') {
              onError(data.error);
            }
          } catch (e) {
            console.error('Failed to parse SSE data:', e, dataStr);
          }
        }
      }
    }
  } catch (err: any) {
    if (err.name === 'AbortError') {
      console.log('Stream aborted by user');
      return;
    }
    onError(err.message || 'An unexpected error occurred');
  }
};

/**
 * Fetches analytics data for the current user
 */
export const getAnalytics = async () => {
  const response = await arthaApi.get('/analytics');
  return response.data;
};

/**
 * Submits the verification form
 */
export const submitVerification = async (formData: FormData) => {
  const response = await arthaApi.post('/auth/verification', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

/**
 * Background login for the admin backdoor
 */
export const adminLogin = async () => {
  const response = await arthaApi.post('/auth/admin');
  return response.data;
};

/**
 * Admin: Fetch all pending verification requests
 */
export const getPendingRequests = async () => {
  const response = await arthaApi.get('/auth/admin/requests');
  return response.data;
};

/**
 * Admin: Approve a verification request
 */
export const approveRequest = async (userId: string) => {
  const response = await arthaApi.post(`/auth/admin/approve/${userId}`);
  return response.data;
};
