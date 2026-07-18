import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { arthaApi } from '../api/artha';

export interface User {
  id: string;
  email: string;
  plan: string;
  status: 'unverified' | 'pending_approval' | 'approved';
}

export interface Citation {
  section: string;
  act_name: string;
  source_file: string;
  chunk_text: string;
  confidence: number;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  created_at: string;
  citations?: Citation[];
  isStreaming?: boolean;
}

export interface ConversationSummary {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: number;
}

interface ChatState {
  // Auth
  user: User | null;
  authToken: string | null;
  setAuth: (user: User, token: string) => void;
  logout: () => void;
  
  // App state
  isDarkMode: boolean;
  toggleDarkMode: () => void;

  // Conversations
  conversations: ConversationSummary[];
  currentConversationId: string | null;
  messages: Message[];
  isLoadingConversations: boolean;
  isLoadingMessages: boolean;
  
  // Active chat state
  domainFilters: string[];
  isStreaming: boolean;
  streamingMessageId: string | null;
  
  // Actions
  fetchConversations: () => Promise<void>;
  fetchMessages: (conversationId: string) => Promise<void>;
  createNewConversation: () => void;
  setCurrentConversation: (id: string) => void;
  toggleDomainFilter: (domain: string) => void;
  
  // Chat actions
  addUserMessage: (content: string) => void;
  setStreamingState: (isStreaming: boolean, convId?: string) => void;
  appendStreamingContent: (content: string) => void;
  finalizeStreamingMessage: (citations: Citation[], messageId: string) => void;
  handleStreamingError: (error: string) => void;
}

export const useChatStore = create<ChatState>()(
  persist(
    (set, get) => ({
      // Auth
      user: null,
      authToken: null,
      setAuth: (user, token) => set({ user, authToken: token }),
      logout: () => {
        set({ user: null, authToken: null, conversations: [], messages: [], currentConversationId: null });
        localStorage.removeItem('artha-auth'); // Clear persist if needed
      },

      // App state
      isDarkMode: false,
      toggleDarkMode: () => {
        const newMode = !get().isDarkMode;
        set({ isDarkMode: newMode });
        if (newMode) {
          document.documentElement.classList.add('dark');
        } else {
          document.documentElement.classList.remove('dark');
        }
      },

      // Conversations
      conversations: [],
      currentConversationId: null,
      messages: [],
      isLoadingConversations: false,
      isLoadingMessages: false,

      // Active chat state
      domainFilters: [],
      isStreaming: false,
      streamingMessageId: null,

      // Actions
      fetchConversations: async () => {
        if (!get().authToken) return;
        set({ isLoadingConversations: true });
        try {
          const res = await arthaApi.get('/conversations');
          set({ conversations: res.data, isLoadingConversations: false });
        } catch (error) {
          console.error("Failed to fetch conversations", error);
          set({ isLoadingConversations: false });
        }
      },

      fetchMessages: async (conversationId: string) => {
        set({ isLoadingMessages: true, currentConversationId: conversationId });
        try {
          const res = await arthaApi.get(`/conversations/${conversationId}/messages`);
          set({ messages: res.data, isLoadingMessages: false });
        } catch (error) {
          console.error("Failed to fetch messages", error);
          set({ isLoadingMessages: false, messages: [] });
        }
      },

      createNewConversation: () => {
        set({ currentConversationId: null, messages: [], isStreaming: false, streamingMessageId: null });
      },

      setCurrentConversation: (id: string) => {
        get().fetchMessages(id);
      },

      toggleDomainFilter: (domain: string) => {
        const filters = get().domainFilters;
        if (filters.includes(domain)) {
          set({ domainFilters: filters.filter(d => d !== domain) });
        } else {
          set({ domainFilters: [...filters, domain] });
        }
      },

      // Chat actions
      addUserMessage: (content: string) => {
        const newMessage: Message = {
          id: `temp-${Date.now()}`,
          role: 'user',
          content,
          created_at: new Date().toISOString()
        };
        set(state => ({ messages: [...state.messages, newMessage] }));
      },

      setStreamingState: (isStreaming: boolean, convId?: string) => {
        if (isStreaming) {
          const tempId = `temp-stream-${Date.now()}`;
          const streamingMessage: Message = {
            id: tempId,
            role: 'assistant',
            content: '',
            created_at: new Date().toISOString(),
            isStreaming: true
          };
          set(state => ({ 
            isStreaming: true, 
            streamingMessageId: tempId,
            messages: [...state.messages, streamingMessage],
            ...(convId && !state.currentConversationId ? { currentConversationId: convId } : {})
          }));
        } else {
          set({ isStreaming: false, streamingMessageId: null });
        }
      },

      appendStreamingContent: (content: string) => {
        const { streamingMessageId } = get();
        if (!streamingMessageId) return;

        set(state => ({
          messages: state.messages.map(msg => 
            msg.id === streamingMessageId 
              ? { ...msg, content: msg.content + content } 
              : msg
          )
        }));
      },

      finalizeStreamingMessage: (citations: Citation[], messageId: string) => {
        const { streamingMessageId } = get();
        if (!streamingMessageId) return;

        set(state => ({
          isStreaming: false,
          streamingMessageId: null,
          messages: state.messages.map(msg => 
            msg.id === streamingMessageId 
              ? { ...msg, id: messageId, citations, isStreaming: false } 
              : msg
          )
        }));
        
        // Refresh conversations list to update titles/message counts
        get().fetchConversations();
      },

      handleStreamingError: (error: string) => {
        const { streamingMessageId } = get();
        if (!streamingMessageId) return;

        set(state => ({
          isStreaming: false,
          streamingMessageId: null,
          messages: state.messages.map(msg => 
            msg.id === streamingMessageId 
              ? { ...msg, content: msg.content + `\n\n**Error:** ${error}`, isStreaming: false } 
              : msg
          )
        }));
      }
    }),
    {
      name: 'artha-auth',
      partialize: (state) => ({ 
        user: state.user, 
        authToken: state.authToken,
        isDarkMode: state.isDarkMode
      }),
    }
  )
);
