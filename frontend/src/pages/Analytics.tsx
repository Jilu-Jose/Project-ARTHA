import { useState, useEffect } from 'react';
import Layout from '../components/ui/Layout';
import { BarChart3, MessageSquare, BookOpen, FileText, Loader2 } from 'lucide-react';
import { getAnalytics } from '../api/artha';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const dummyChartData = [
  { name: 'Mon', queries: 40 },
  { name: 'Tue', queries: 30 },
  { name: 'Wed', queries: 55 },
  { name: 'Thu', queries: 45 },
  { name: 'Fri', queries: 70 },
  { name: 'Sat', queries: 65 },
  { name: 'Sun', queries: 85 },
];

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
        
        {/* Chart Section */}
        {!loading && !error && (
          <div className="mt-8 bg-card border border-border rounded-2xl p-6 shadow-sm">
            <h3 className="text-xl font-serif text-foreground mb-6">Weekly Queries Overview</h3>
            <div className="h-[350px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={dummyChartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorQueries" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#B91C1C" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#B91C1C" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="currentColor" className="text-border opacity-50" />
                  <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fill: '#6B7280', fontSize: 12 }} dy={10} />
                  <YAxis axisLine={false} tickLine={false} tick={{ fill: '#6B7280', fontSize: 12 }} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: 'var(--card)', borderColor: 'var(--border)', borderRadius: '8px', color: 'var(--foreground)' }}
                    itemStyle={{ color: '#B91C1C' }}
                  />
                  <Area type="monotone" dataKey="queries" stroke="#B91C1C" strokeWidth={3} fillOpacity={1} fill="url(#colorQueries)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
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
