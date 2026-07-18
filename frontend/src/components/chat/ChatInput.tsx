import { useState, useRef, useEffect } from 'react';
import { Send, Sparkles, Filter, X } from 'lucide-react';
import { cn } from '../../lib/utils';
import { useChatStore } from '../../store/chatStore';

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
}

const DOMAINS = [
  { id: 'companies_act', label: 'Companies Act' },
  { id: 'gst', label: 'GST' },
  { id: 'fema', label: 'FEMA' },
  { id: 'sebi', label: 'SEBI' },
  { id: 'startup_india', label: 'Startup India' }
];

export default function ChatInput({ onSend, disabled }: ChatInputProps) {
  const [input, setInput] = useState('');
  const [showFilters, setShowFilters] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  
  const { domainFilters, toggleDomainFilter } = useChatStore();

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  }, [input]);

  const handleSubmit = () => {
    if (input.trim() && !disabled) {
      onSend(input.trim());
      setInput('');
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="relative w-full max-w-4xl mx-auto">
      
      {/* Domain Filters Panel */}
      {showFilters && (
        <div className="absolute bottom-[calc(100%+12px)] left-0 bg-popover border border-border p-3 rounded-lg shadow-lg z-20 w-[300px] animate-in slide-in-from-bottom-2 fade-in duration-200">
          <div className="flex justify-between items-center mb-3">
            <span className="text-sm font-semibold">Filter by Domain</span>
            <button onClick={() => setShowFilters(false)} className="text-muted-foreground hover:text-foreground">
              <X className="w-4 h-4" />
            </button>
          </div>
          <div className="flex flex-wrap gap-2">
            {DOMAINS.map(domain => {
              const isActive = domainFilters.includes(domain.id);
              return (
                <button
                  key={domain.id}
                  onClick={() => toggleDomainFilter(domain.id)}
                  className={cn(
                    "text-xs px-2.5 py-1.5 rounded-full border transition-colors",
                    isActive 
                      ? "bg-brand-navy border-brand-navy text-white dark:bg-brand-gold dark:border-brand-gold dark:text-brand-navy"
                      : "bg-transparent border-border text-muted-foreground hover:border-brand-navy/50"
                  )}
                >
                  {domain.label}
                </button>
              );
            })}
          </div>
          {domainFilters.length > 0 && (
            <div className="mt-3 pt-3 border-t border-border flex justify-end">
              <button 
                onClick={() => DOMAINS.forEach(d => { if(domainFilters.includes(d.id)) toggleDomainFilter(d.id) })}
                className="text-xs text-muted-foreground hover:text-destructive transition-colors"
              >
                Clear all
              </button>
            </div>
          )}
        </div>
      )}

      {/* Main Input Area */}
      <div className="relative glass-panel rounded-2xl shadow-sm focus-within:shadow-md focus-within:border-brand-gold/50 transition-all flex flex-col bg-white dark:bg-dark-surface border border-border">
        
        <textarea
          ref={textareaRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask a legal or compliance question..."
          className="w-full max-h-[200px] bg-transparent resize-none outline-none py-4 px-5 text-[15px] text-foreground placeholder:text-muted-foreground/70"
          rows={1}
          disabled={disabled}
        />
        
        <div className="flex justify-between items-center px-4 pb-3 pt-1">
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowFilters(!showFilters)}
              className={cn(
                "p-1.5 rounded-md text-xs font-medium flex items-center gap-1.5 transition-colors",
                domainFilters.length > 0 
                  ? "text-brand-navy bg-brand-gold/20 dark:text-brand-gold" 
                  : "text-muted-foreground hover:bg-muted"
              )}
              title="Filter by legal domain"
            >
              <Filter className="w-3.5 h-3.5" />
              {domainFilters.length > 0 ? `${domainFilters.length} domains` : 'All Domains'}
            </button>
            <div className="flex items-center gap-1 text-xs text-muted-foreground/60 px-2">
              <Sparkles className="w-3 h-3 text-brand-gold" />
              Kimi K2.6
            </div>
          </div>
          
          <button
            onClick={handleSubmit}
            disabled={!input.trim() || disabled}
            className="p-2 rounded-full bg-brand-navy text-white disabled:bg-muted disabled:text-muted-foreground hover:bg-brand-navy-light transition-colors dark:bg-brand-gold dark:text-brand-navy dark:disabled:bg-muted dark:hover:bg-brand-gold-light"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>

      </div>
      <div className="text-center mt-3 text-xs text-muted-foreground">
        ARTHA can make mistakes. Always consult a qualified legal professional for critical decisions.
      </div>
    </div>
  );
}
