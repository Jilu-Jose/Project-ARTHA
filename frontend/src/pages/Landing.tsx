import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { Scale, ShieldCheck, Zap, ArrowRight, BookOpen, Search, FileText } from 'lucide-react';
import { useChatStore } from '../store/chatStore';

export default function Landing() {
  const navigate = useNavigate();
  const { user } = useChatStore();

  const handleStart = () => {
    if (user) {
      navigate('/dashboard');
    } else {
      navigate('/auth');
    }
  };

  const handleViewCorpus = () => {
    navigate('/corpus');
  };

  return (
    <div className="min-h-screen bg-brand-bg flex flex-col items-center justify-center relative overflow-x-hidden font-sans">
      
      {/* Background Decorative Elements */}
      <div className="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] rounded-full bg-brand-red/5 blur-[120px] pointer-events-none" />
      <div className="absolute bottom-[-20%] right-[-10%] w-[60%] h-[60%] rounded-full bg-blue-500/5 blur-[120px] pointer-events-none" />

      {/* Navbar */}
      <header className="absolute top-0 w-full px-8 py-6 flex justify-between items-center z-20 max-w-7xl mx-auto left-0 right-0">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-white shadow-sm border border-border rounded flex items-center justify-center">
            <span className="font-serif text-brand-red font-bold text-xl">A</span>
          </div>
          <span className="font-serif font-bold text-2xl tracking-wide text-foreground">ARTHA</span>
        </div>
        <nav className="flex items-center gap-8 hidden md:flex">
          <a href="#features" className="text-sm font-medium text-muted-foreground hover:text-brand-red transition-colors">Features</a>
          <a href="#how-it-works" className="text-sm font-medium text-muted-foreground hover:text-brand-red transition-colors">How it Works</a>
          <button 
            onClick={handleStart}
            className="px-6 py-2.5 bg-brand-red text-white rounded-lg text-sm font-medium hover:bg-brand-red-dark transition-colors shadow-md"
          >
            {user ? 'Enter Workspace' : 'Sign In'}
          </button>
        </nav>
      </header>

      {/* Hero Section */}
      <main className="w-full max-w-6xl px-6 pt-32 pb-20 flex flex-col items-center text-center z-10 mt-10">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: "easeOut" }}
          className="flex flex-col items-center"
        >
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-red-50 text-brand-red border border-red-100 text-xs font-semibold tracking-wide mb-8 shadow-sm">
            <span className="w-2 h-2 rounded-full bg-brand-red animate-pulse" />
            Vectorless RAG Architecture
          </div>
          <h1 className="text-5xl md:text-7xl font-serif font-bold leading-tight mb-6 max-w-4xl mx-auto text-foreground">
            Legal Intelligence for <br/>
            <span className="text-brand-red">
              Indian Startup Founders
            </span>
          </h1>
          <p className="text-lg md:text-xl text-muted-foreground max-w-2xl mx-auto mb-10 text-balance">
            Navigate complex Indian regulations with absolute precision. Get cited answers from the Companies Act, GST, FEMA, and SEBI—grounded exclusively in authoritative statutes.
          </p>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center w-full sm:w-auto">
            <button 
              onClick={handleStart}
              className="group flex items-center justify-center gap-2 px-8 py-4 bg-brand-red text-white rounded-xl text-lg font-medium hover:bg-brand-red-dark transition-all shadow-lg w-full sm:w-auto"
            >
              Start Querying
              <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </button>
            <button 
              onClick={handleViewCorpus}
              className="px-8 py-4 bg-white border border-border text-foreground rounded-xl text-lg font-medium hover:bg-gray-50 transition-all shadow-sm w-full sm:w-auto"
            >
              View Corpus
            </button>
          </div>
        </motion.div>

        {/* Feature Grid */}
        <motion.div 
          id="features"
          className="grid md:grid-cols-3 gap-8 mt-32 w-full text-left"
          initial={{ opacity: 0, y: 40 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.8, ease: "easeOut" }}
        >
          <FeatureCard 
            icon={<ShieldCheck className="w-6 h-6 text-brand-red" />}
            title="Zero Hallucinations"
            description="Built on a strict extraction protocol. If the answer isn't in the legal texts, ARTHA won't guess."
          />
          <FeatureCard 
            icon={<Scale className="w-6 h-6 text-brand-red" />}
            title="Deep Citation Grounding"
            description="Every claim is mapped to the exact section and act. Click to read the original legal prose."
          />
          <FeatureCard 
            icon={<Zap className="w-6 h-6 text-brand-red" />}
            title="Vectorless RAG"
            description="Powered by BM25 sparse retrieval and 256K long-context LLMs for superior precision over semantic embeddings."
          />
        </motion.div>
      </main>

      {/* How it Works Section */}
      <section id="how-it-works" className="w-full bg-white border-y border-border py-24 relative z-10">
        <div className="max-w-6xl mx-auto px-6">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-serif font-bold text-foreground mb-4">How ARTHA Works</h2>
            <p className="text-muted-foreground max-w-2xl mx-auto">A transparent, reliable legal research workflow designed to eliminate AI hallucination and provide verifiable legal advice.</p>
          </div>

          <div className="grid md:grid-cols-3 gap-12 relative">
            {/* Connecting line for desktop */}
            <div className="hidden md:block absolute top-12 left-[16%] right-[16%] h-[2px] bg-red-100 z-0"></div>
            
            <StepCard 
              step="1"
              icon={<Search className="w-6 h-6 text-brand-red" />}
              title="Query Interpretation"
              description="You ask a complex legal question. Our system restructures it to find the precise legal terms required for search."
            />
            <StepCard 
              step="2"
              icon={<BookOpen className="w-6 h-6 text-brand-red" />}
              title="Statutory Retrieval"
              description="Using exact-match keyword algorithms (BM25), we retrieve the relevant sections from the raw Acts and Statutes."
            />
            <StepCard 
              step="3"
              icon={<FileText className="w-6 h-6 text-brand-red" />}
              title="Cited Generation"
              description="A long-context LLM analyzes the retrieved texts and generates an answer, strictly citing the original documents."
            />
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="w-full bg-brand-bg py-12 border-t border-border mt-auto z-10">
        <div className="max-w-6xl mx-auto px-6 flex flex-col md:flex-row justify-between items-center gap-6">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-white shadow-sm border border-border rounded flex items-center justify-center">
              <span className="font-serif text-brand-red font-bold text-lg">A</span>
            </div>
            <span className="font-serif font-bold text-xl tracking-wide text-foreground">ARTHA</span>
          </div>
          <p className="text-sm text-muted-foreground text-center md:text-left">
            Disclaimer: ARTHA provides legal intelligence based on public statutes, not legal advice. Always consult a qualified professional.
          </p>
          <div className="flex gap-4">
             <a href="#" className="text-sm text-muted-foreground hover:text-brand-red">Privacy Policy</a>
             <a href="#" className="text-sm text-muted-foreground hover:text-brand-red">Terms of Service</a>
          </div>
        </div>
      </footer>
    </div>
  );
}

function FeatureCard({ icon, title, description }: { icon: React.ReactNode, title: string, description: string }) {
  return (
    <div className="p-8 rounded-2xl bg-white shadow-sm border border-border hover:shadow-md transition-all group relative overflow-hidden h-full">
      <div className="w-12 h-12 rounded-xl bg-red-50 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform border border-red-100">
        {icon}
      </div>
      <h3 className="text-xl font-bold font-serif mb-3 text-foreground">{title}</h3>
      <p className="text-muted-foreground text-sm leading-relaxed">{description}</p>
    </div>
  );
}

function StepCard({ step, icon, title, description }: { step: string, icon: React.ReactNode, title: string, description: string }) {
  return (
    <div className="flex flex-col items-center text-center relative z-10">
      <div className="w-24 h-24 rounded-full bg-white border border-red-100 shadow-md flex items-center justify-center mb-6 relative">
        <div className="absolute -top-2 -right-2 w-8 h-8 rounded-full bg-brand-red text-white flex items-center justify-center font-bold text-sm border-2 border-white">
          {step}
        </div>
        <div className="bg-red-50 p-4 rounded-full">
          {icon}
        </div>
      </div>
      <h3 className="text-xl font-bold font-serif mb-3 text-foreground">{title}</h3>
      <p className="text-muted-foreground text-sm leading-relaxed max-w-[280px]">{description}</p>
    </div>
  );
}

