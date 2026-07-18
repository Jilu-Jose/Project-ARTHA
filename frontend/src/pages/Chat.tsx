import { useState, useRef, useEffect } from 'react';
import Layout from '../components/ui/Layout';
import { Send, Paperclip, ExternalLink, FileText, Scissors, Search as SearchIcon, BookOpen, Loader2, Square, User as UserIcon } from 'lucide-react';
import { useChatStore } from '../store/chatStore';
import { askQuestionStream } from '../api/artha';

export default function Chat() {
  const [input, setInput] = useState('');
  
  const { 
    messages, 
    isStreaming, 
    currentConversationId,
    domainFilters,
    addUserMessage,
    setStreamingState,
    appendStreamingContent,
    finalizeStreamingMessage,
    handleStreamingError,
    fetchConversations
  } = useChatStore();

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const citationsRef = useRef<any[]>([]);
  const abortControllerRef = useRef<AbortController | null>(null);

  // Scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isStreaming]);

  // Find the citations from the latest assistant message that has them
  const activeCitations = [...messages].reverse().find(m => m.citations && m.citations.length > 0)?.citations || [];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isStreaming) return;

    const question = input.trim();
    addUserMessage(question);
    setInput('');
    citationsRef.current = [];

    abortControllerRef.current = new AbortController();

    await askQuestionStream(
      question,
      domainFilters,
      currentConversationId,
      (convId) => {
        setStreamingState(true, convId);
      },
      (chunk) => {
        appendStreamingContent(chunk);
      },
      (citations) => {
        citationsRef.current = citations;
      },
      (messageId) => {
        finalizeStreamingMessage(citationsRef.current, messageId);
        abortControllerRef.current = null;
      },
      (error) => {
        handleStreamingError(error);
        abortControllerRef.current = null;
      },
      abortControllerRef.current.signal
    );
  };

  const handleStop = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
      setStreamingState(false, currentConversationId || '');
    }
  };

  return (
    <Layout>
      <div className="flex flex-col lg:flex-row h-[calc(100vh-120px)] gap-6 animate-in fade-in duration-500">
        
        {/* Main Chat Area */}
        <div className="flex-1 flex flex-col bg-card border border-border rounded-2xl shadow-sm overflow-hidden relative">
          
          {/* Header */}
          <div className="px-6 py-4 border-b border-border flex justify-between items-center bg-secondary/50">
            <div>
              <h2 className="text-lg font-semibold text-brand-red mb-0.5">
                {currentConversationId ? 'Active Research' : 'New Legal Research'}
              </h2>
              <p className="text-xs text-muted-foreground">Vectorless RAG Engine</p>
            </div>
            {isStreaming && (
              <div className="px-3 py-1 bg-blue-50 text-blue-700 text-[10px] font-semibold rounded-full border border-blue-100 flex items-center gap-2">
                <Loader2 className="w-3 h-3 animate-spin" />
                Processing
              </div>
            )}
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-6 space-y-8">
            {messages.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-muted-foreground text-center p-4">
                <div className="w-16 h-16 bg-red-50 text-brand-red rounded-full flex items-center justify-center mb-4">
                  <SearchIcon className="w-8 h-8" />
                </div>
                <h3 className="text-lg font-serif font-bold text-foreground mb-2">What legal issue can I help you research?</h3>
                <p className="text-sm max-w-md">
                  Ask a question based on Indian Corporate Law, GST, FEMA, or SEBI regulations. 
                  ARTHA will extract and cite the exact provisions.
                </p>
              </div>
            ) : (
              messages.map((msg) => (
                <div key={msg.id} className={`flex gap-4 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  
                  {msg.role === 'assistant' && (
                    <div className="w-8 h-8 rounded-lg bg-red-50 border border-red-100 flex items-center justify-center shrink-0 mt-1">
                       <div className="text-[10px] font-bold text-brand-red">AI</div>
                    </div>
                  )}
                  
                  <div className={`max-w-[85%] ${msg.role === 'user' ? 'bg-secondary' : 'bg-transparent'} rounded-2xl p-4 text-sm text-foreground leading-relaxed shadow-sm border border-transparent whitespace-pre-wrap ${msg.role === 'user' ? 'border-gray-200' : ''}`}
                       dangerouslySetInnerHTML={{ __html: msg.content }}
                  />

                  {msg.role === 'user' && (
                    <div className="w-8 h-8 rounded-full bg-secondary overflow-hidden shrink-0 mt-1 shadow-sm flex items-center justify-center">
                      <UserIcon className="w-5 h-5 text-muted-foreground opacity-50" />
                    </div>
                  )}

                </div>
              ))
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <div className="p-4 bg-card border-t border-border">
            <form onSubmit={handleSubmit} className="relative flex items-center bg-secondary border border-border rounded-full shadow-sm p-1">
              <button type="button" className="p-2 text-muted-foreground hover:text-foreground transition-colors rounded-full hover:bg-secondary ml-1">
                <Paperclip className="w-4 h-4" />
              </button>
              <input 
                type="text" 
                value={input}
                onChange={(e) => setInput(e.target.value)}
                disabled={isStreaming}
                placeholder="Ask a legal question or request a draft..."
                className="flex-1 bg-transparent border-none py-2 px-3 text-sm text-foreground focus:outline-none placeholder:text-muted-foreground disabled:opacity-50"
              />
              {isStreaming ? (
                <button type="button" onClick={handleStop} className="p-1.5 mr-1 text-white bg-red-500 hover:bg-red-600 rounded-full transition-colors flex items-center justify-center gap-1.5 px-3">
                  <Square className="w-3 h-3 fill-current" />
                  <span className="text-xs font-semibold">Stop</span>
                </button>
              ) : (
                <button type="submit" disabled={!input.trim()} className="p-2 mr-1 text-brand-red hover:bg-red-50 rounded-full transition-colors disabled:opacity-50 disabled:cursor-not-allowed">
                  <Send className="w-4 h-4" />
                </button>
              )}
            </form>
          </div>

        </div>

        {/* Right Sidebar Area */}
        <div className="w-full lg:w-[320px] flex flex-col gap-6 shrink-0">
          
          {/* Citation Reference */}
          <div className="bg-card border border-border rounded-2xl shadow-sm overflow-hidden flex flex-col flex-1">
            <div className="p-4 border-b border-border bg-secondary/50 flex items-center gap-2">
              <BookOpen className="w-4 h-4 text-brand-red" />
              <h3 className="font-semibold text-sm text-foreground">Citation Reference</h3>
            </div>
            <div className="p-4 space-y-4 overflow-y-auto">
              
              {activeCitations.length === 0 ? (
                <div className="text-xs text-muted-foreground text-center py-10">
                  No citations active. Ask a question to see statutory references here.
                </div>
              ) : (
                activeCitations.map((cit, idx) => (
                  <div key={idx} className="bg-secondary border border-border rounded-xl p-4">
                    <div className="flex justify-between items-center mb-2">
                      <h4 className="text-[10px] font-bold text-blue-800 tracking-wider uppercase">{cit.act_name} §{cit.section}</h4>
                      <ExternalLink className="w-3 h-3 text-muted-foreground cursor-pointer hover:text-foreground" />
                    </div>
                    <p className="text-xs text-muted-foreground leading-relaxed italic">
                      "{cit.chunk_text}..."
                    </p>
                  </div>
                ))
              )}

            </div>
          </div>

          {/* Quick Actions */}
          <div className="bg-card border border-border rounded-2xl shadow-sm overflow-hidden">
            <div className="p-4 border-b border-border bg-secondary/50 flex items-center gap-2">
              <Zap className="w-4 h-4 text-brand-red" />
              <h3 className="font-semibold text-sm text-foreground">Quick Actions</h3>
            </div>
            <div className="p-2 space-y-1">
              <button 
                onClick={() => setInput('Draft a legal memo regarding: ')}
                className="w-full flex items-center justify-between p-3 text-sm text-foreground hover:bg-secondary rounded-lg transition-colors group"
              >
                <span className="font-medium text-xs">Draft Memo</span>
                <FileText className="w-4 h-4 text-muted-foreground group-hover:text-brand-red transition-colors" />
              </button>
              <button 
                onClick={() => setInput('Extract the key clauses and compliance requirements for: ')}
                className="w-full flex items-center justify-between p-3 text-sm text-foreground hover:bg-secondary rounded-lg transition-colors group"
              >
                <span className="font-medium text-xs">Extract Key Clauses</span>
                <Scissors className="w-4 h-4 text-muted-foreground group-hover:text-brand-red transition-colors" />
              </button>
              <button 
                onClick={() => setInput('Find legal precedents and similar cases for: ')}
                className="w-full flex items-center justify-between p-3 text-sm text-foreground hover:bg-secondary rounded-lg transition-colors group"
              >
                <span className="font-medium text-xs">Find Similar Precedent</span>
                <SearchIcon className="w-4 h-4 text-muted-foreground group-hover:text-brand-red transition-colors" />
              </button>
            </div>
          </div>

        </div>

      </div>
    </Layout>
  );
}

function Zap(props: any) {
  return (
    <svg {...props} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon>
    </svg>
  );
}
