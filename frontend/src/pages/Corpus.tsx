import { useState, useEffect } from 'react';
import Layout from '../components/ui/Layout';
import { Bookmark, Calendar, List, Search as SearchIcon, Filter, FileText, MessageSquare, ChevronDown, ChevronUp, Loader2 } from 'lucide-react';
import { arthaApi } from '../api/artha';

interface CorpusDocument {
  id: string;
  name: string;
  domain: string;
  description: string;
  total_chunks: number;
}

export default function Corpus() {
  const [activeTab, setActiveTab] = useState('All');
  const [acts, setActs] = useState<CorpusDocument[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeActId, setActiveActId] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    arthaApi.get('/corpus')
      .then(res => {
        setActs(res.data);
        if (res.data.length > 0) {
          setActiveActId(res.data[0].id);
        }
      })
      .catch(err => console.error('Failed to fetch corpus:', err))
      .finally(() => setLoading(false));
  }, []);

  const filteredActs = activeTab === 'All' 
    ? acts 
    : acts.filter(act => act.domain.toLowerCase() === activeTab.toLowerCase());

  const activeAct = acts.find(a => a.id === activeActId);

  return (
    <Layout>
      <div className="flex flex-col lg:flex-row h-[calc(100vh-120px)] gap-8 animate-in fade-in duration-500 pb-8">
        
        {/* Left Panel: Statutory Library */}
        <div className="w-full lg:w-[350px] shrink-0 flex flex-col h-full">
          
          <h2 className="text-sm font-bold text-foreground tracking-wider mb-4 uppercase">Statutory Library</h2>
          
          {/* Tabs */}
          <div className="flex gap-2 mb-6 overflow-x-auto pb-2 shrink-0">
            {['All', 'Corporate', 'Tax', 'Finance'].map(tab => (
              <button 
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-3 py-1.5 rounded-full text-xs font-medium transition-colors shrink-0 ${activeTab === tab ? 'bg-red-50 text-brand-red border border-red-100' : 'bg-secondary text-muted-foreground hover:bg-secondary'}`}
              >
                {tab}
              </button>
            ))}
          </div>

          {/* List */}
          <div className="flex-1 overflow-y-auto space-y-4 pr-2">
            {loading ? (
              <div className="flex items-center justify-center p-10">
                <Loader2 className="w-6 h-6 text-brand-red animate-spin" />
              </div>
            ) : filteredActs.length === 0 ? (
              <div className="text-center text-sm text-muted-foreground p-10">
                No documents found for this category.
              </div>
            ) : (
              filteredActs.map(act => (
                <div 
                  key={act.id} 
                  onClick={() => setActiveActId(act.id)}
                  className={`bg-card rounded-xl p-5 border transition-all cursor-pointer relative overflow-hidden ${
                    activeActId === act.id 
                      ? 'border-brand-red shadow-sm ring-1 ring-brand-red/20' 
                      : 'border-border hover:bg-secondary hover:shadow-sm'
                  }`}
                >
                  {activeActId === act.id && <div className="absolute left-0 top-0 bottom-0 w-1 bg-brand-red"></div>}
                  
                  <div className="flex justify-between items-start mb-2">
                    <span className="text-[10px] font-bold text-brand-red bg-red-50 px-2 py-0.5 rounded border border-red-100 uppercase">
                      {act.domain}
                    </span>
                    <Bookmark className={`w-3.5 h-3.5 ${activeActId === act.id ? 'text-brand-red' : 'text-muted-foreground'}`} />
                  </div>
                  
                  <h3 className="font-semibold text-foreground text-sm mb-1">{act.name}</h3>
                  <p className="text-xs text-muted-foreground leading-relaxed mb-4 line-clamp-2">{act.description}</p>
                  
                  <div className="flex gap-4 text-[10px] text-muted-foreground font-medium">
                    <div className="flex items-center gap-1.5">
                      <List className="w-3 h-3" />
                      {act.total_chunks} Sections
                    </div>
                    <div className="flex items-center gap-1.5">
                      <Calendar className="w-3 h-3" />
                      Up to date
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Right Panel: Document Viewer */}
        <div className="flex-1 bg-card border border-border rounded-2xl shadow-sm flex flex-col h-full overflow-hidden relative">
          
          {/* Header */}
          <div className="px-6 py-4 border-b border-border flex justify-between items-center bg-secondary/50">
            <div className="flex items-center gap-2 text-xs font-medium text-muted-foreground">
              <span>{activeAct?.name || 'Document'}</span>
              <span>›</span>
              <span className="text-brand-red">Overview</span>
            </div>
            
            <div className="flex items-center gap-1">
              <button className="p-1.5 text-muted-foreground hover:bg-secondary rounded transition-colors">
                <Filter className="w-4 h-4" />
              </button>
              <button className="p-1.5 text-muted-foreground hover:bg-secondary rounded transition-colors">
                <FileText className="w-4 h-4" />
              </button>
              <div className="w-[1px] h-4 bg-secondary mx-1"></div>
              <button className="p-1.5 text-brand-red hover:bg-red-50 rounded transition-colors">
                <MessageSquare className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Document Content */}
          <div className="flex-1 overflow-y-auto p-10 pb-20">
            <div className="max-w-3xl mx-auto">
              <h1 className="text-3xl font-serif font-bold text-center mb-6 text-foreground">
                {activeAct?.name || 'Select a document'}
              </h1>
              
              <div className="space-y-8">
                {activeAct ? (
                  <div className="bg-secondary p-6 rounded-xl border border-border">
                    <h4 className="text-base font-bold text-foreground mb-3 font-serif">About this act</h4>
                    <p className="text-sm text-foreground leading-relaxed mb-4">
                      {activeAct.description}
                    </p>
                    <div className="flex items-center gap-4 text-xs text-muted-foreground">
                      <span className="font-semibold px-2 py-1 bg-card border border-border rounded">Domain: {activeAct.domain}</span>
                      <span className="font-semibold px-2 py-1 bg-card border border-border rounded">Indexed Chunks: {activeAct.total_chunks}</span>
                    </div>
                  </div>
                ) : (
                  <div className="text-center text-muted-foreground py-20">
                    <BookOpen className="w-12 h-12 mx-auto mb-4 text-secondary" />
                    <p>Select a document from the library to view details.</p>
                  </div>
                )}

                {activeAct && (
                   <div className="flex gap-4">
                   <div className="text-sm font-semibold text-muted-foreground pt-0.5">1.</div>
                   <div>
                     <h4 className="text-base font-bold text-foreground mb-3 font-serif">Structure.</h4>
                     <p className="text-sm text-foreground leading-relaxed mb-4">
                       This document has been fully indexed by the ARTHA Vectorless RAG engine. 
                       You can search for specific provisions using the Legal Research interface, 
                       and citations will automatically refer back to the exact sections contained here.
                     </p>
                   </div>
                 </div>
                )}
              </div>
            </div>
          </div>
          
          {/* Scroll Navigation Overlay */}
          <div className="absolute bottom-6 right-6 flex flex-col gap-2">
            <button className="w-10 h-10 bg-card border border-border shadow-md rounded-full flex items-center justify-center text-muted-foreground hover:text-foreground transition-colors">
              <ChevronUp className="w-5 h-5" />
            </button>
            <button className="w-10 h-10 bg-card border border-border shadow-md rounded-full flex items-center justify-center text-muted-foreground hover:text-foreground transition-colors">
              <ChevronDown className="w-5 h-5" />
            </button>
          </div>

        </div>

      </div>
    </Layout>
  );
}

function BookOpen(props: any) {
  return (
    <svg {...props} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"></path>
      <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"></path>
    </svg>
  );
}
