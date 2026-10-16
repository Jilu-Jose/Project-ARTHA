import { useState, useEffect } from 'react';
import Layout from '../components/ui/Layout';
import { BarChart3, MessageSquare, BookOpen, FileText, Loader2 } from 'lucide-react';
import { getAnalytics } from '../api/artha';

interface AnalyticsData {
  total_conversations: number;
  total_messages: number;
  total_citations: number;
  documents_indexed: number;
}

export default function Analytics() {
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    async function fetchAnalytics() {
      try {
        const result = await getAnalytics();
        setData(result);
      } catch (err) {
        setError('Failed to load analytics data.');
      } finally {
        setLoading(false);
      }
    }
    fetchAnalytics();
  }, []);

  return (
    <Layout>
      <div className="flex flex-col h-full animate-in fade-in duration-500 overflow-y-auto pb-10">
        
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-serif text-foreground mb-2">Analytics Dashboard</h1>
          <p className="text-muted-foreground text-sm">
            Insights and reports on your platform usage.
          </p>
        </div>

        {loading ? (
          <div className="flex-1 flex items-center justify-center">
            <Loader2 className="w-8 h-8 text-brand-red animate-spin" />
          </div>
        ) : error ? (
          <div className="flex-1 flex items-center justify-center text-brand-red">
            {error}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            
            <StatCard 
              title="Total Conversations" 
              value={data?.total_conversations || 0} 
              icon={<MessageSquare className="w-6 h-6 text-brand-red" />} 
            />
            
            <StatCard 
              title="Total Messages" 
              value={data?.total_messages || 0} 
              icon={<FileText className="w-6 h-6 text-brand-red" />} 
            />
            
            <StatCard 
              title="Citations Extracted" 
              value={data?.total_citations || 0} 
              icon={<BookOpen className="w-6 h-6 text-brand-red" />} 
            />
            
            <StatCard 
              title="Knowledge Base Docs" 
              value={data?.documents_indexed || 0} 
              icon={<BarChart3 className="w-6 h-6 text-brand-red" />} 
            />
            
          </div>
        )}
      </div>
    </Layout>
  );
}

function StatCard({ title, value, icon }: { title: string, value: number, icon: React.ReactNode }) {
  return (
    <div className="bg-card rounded-2xl border border-border shadow-sm p-6 flex flex-col items-center justify-center text-center">
      <div className="w-12 h-12 bg-red-50 rounded-full flex items-center justify-center mb-4">
        {icon}
      </div>
      <h3 className="text-3xl font-bold text-foreground mb-1">{value}</h3>
      <p className="text-xs text-muted-foreground uppercase tracking-wider font-semibold">{title}</p>
    </div>
  );
}
