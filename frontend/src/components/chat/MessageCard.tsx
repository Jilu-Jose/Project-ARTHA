import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Bot, User as UserIcon, BookOpen, AlertTriangle } from 'lucide-react';
import type { Message, Citation } from '../../store/chatStore';
import { cn } from '../../lib/utils';
import { useState } from 'react';

interface MessageCardProps {
  message: Message;
}

export default function MessageCard({ message }: MessageCardProps) {
  const isUser = message.role === 'user';
  const [expandedCitation, setExpandedCitation] = useState<number | null>(null);

  if (isUser) {
    return (
      <div className="w-full flex justify-end mb-8 px-4">
        <div className="max-w-[80%] md:max-w-[70%]">
          <div className="bg-brand-navy text-white dark:bg-brand-gold dark:text-brand-navy px-5 py-4 rounded-2xl rounded-tr-sm shadow-sm text-[15px] leading-relaxed">
            {message.content}
          </div>
        </div>
      </div>
    );
  }

  // Assistant Message
  return (
    <div className="w-full flex justify-start mb-10 px-4">
      <div className="max-w-[90%] md:max-w-[85%] flex gap-4">
        <div className="w-8 h-8 rounded-full bg-brand-gold flex items-center justify-center shrink-0 mt-1">
          <Bot className="w-4 h-4 text-brand-navy" />
        </div>
        
        <div className="flex-1 min-w-0">
          <div className="text-foreground text-[15px] leading-relaxed markdown-prose">
            <ReactMarkdown 
              remarkPlugins={[remarkGfm]}
              components={{
                p: ({node, ...props}) => <p className="mb-4 last:mb-0" {...props} />,
                ul: ({node, ...props}) => <ul className="list-disc pl-6 mb-4 space-y-1 marker:text-brand-gold" {...props} />,
                ol: ({node, ...props}) => <ol className="list-decimal pl-6 mb-4 space-y-1 marker:text-brand-gold" {...props} />,
                h1: ({node, ...props}) => <h1 className="text-2xl font-bold font-serif mb-4 mt-6 text-brand-navy dark:text-brand-gold" {...props} />,
                h2: ({node, ...props}) => <h2 className="text-xl font-bold font-serif mb-3 mt-5 text-brand-navy dark:text-brand-gold" {...props} />,
                h3: ({node, ...props}) => <h3 className="text-lg font-bold font-serif mb-2 mt-4" {...props} />,
                strong: ({node, ...props}) => <strong className="font-semibold text-brand-navy dark:text-brand-gold" {...props} />,
                hr: ({node, ...props}) => <hr className="my-6 border-border" {...props} />,
                blockquote: ({node, ...props}) => (
                  <blockquote className="border-l-4 border-brand-gold pl-4 italic text-muted-foreground my-4" {...props} />
                ),
                a: ({node, ...props}) => (
                  <a className="text-brand-navy dark:text-brand-gold underline decoration-brand-gold/30 underline-offset-4 hover:decoration-brand-gold transition-colors" {...props} />
                )
              }}
            >
              {message.content}
            </ReactMarkdown>
            
            {message.isStreaming && (
              <span className="inline-block w-2 h-4 ml-1 bg-brand-gold animate-pulse align-middle" />
            )}
          </div>

          {/* Citations Block */}
          {message.citations && message.citations.length > 0 && (
            <div className="mt-6 border border-border rounded-xl bg-card overflow-hidden">
              <div className="px-4 py-3 bg-muted/30 border-b border-border flex items-center gap-2">
                <BookOpen className="w-4 h-4 text-brand-gold" />
                <h4 className="text-sm font-semibold font-serif m-0">Grounded Citations</h4>
              </div>
              <div className="divide-y divide-border">
                {message.citations.map((cit, idx) => (
                  <div key={idx} className="flex flex-col">
                    <button 
                      onClick={() => setExpandedCitation(expandedCitation === idx ? null : idx)}
                      className="px-4 py-3 text-left hover:bg-muted/50 transition-colors flex justify-between items-center group"
                    >
                      <div className="flex flex-col gap-1">
                        <span className="text-sm font-semibold text-brand-navy dark:text-brand-gold group-hover:underline decoration-brand-gold/50 underline-offset-2">
                          {cit.section}
                        </span>
                        <span className="text-xs text-muted-foreground">{cit.act_name}</span>
                      </div>
                      <div className="text-xs font-mono text-muted-foreground/60">
                        {cit.source_file}
                      </div>
                    </button>
                    
                    {/* Expandable chunk text */}
                    {expandedCitation === idx && (
                      <div className="px-4 py-3 bg-muted/10 border-t border-border/50 animate-in slide-in-from-top-1">
                        <div className="text-xs font-mono text-muted-foreground leading-relaxed whitespace-pre-wrap gold-accent">
                          {cit.chunk_text}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

        </div>
      </div>
    </div>
  );
}
