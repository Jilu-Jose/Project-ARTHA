import { useEffect, useState } from 'react';
import Layout from '../components/ui/Layout';
import { MessageSquare, BookOpen, FileText, BarChart3, Loader2, ArrowRight } from 'lucide-react';
import { getAnalytics } from '../api/artha';
import { useNavigate } from 'react-router-dom';
import { useChatStore } from '../store/chatStore';

interface AnalyticsData {
  total_conversations: number;
  total_messages: number;
  total_citations: number;
  documents_indexed: number;
}

export default function Dashboard() {
  const navigate = useNavigate();
  const { user, conversations, fetchConversations, isLoadingConversations } = useChatStore();
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [loadingAnalytics, setLoadingAnalytics] = useState(true);

  useEffect(() => {
    fetchConversations();
    getAnalytics()
      .then(setAnalytics)
      .catch(console.error)
      .finally(() => setLoadingAnalytics(false));
  }, [fetchConversations]);

  const recentConversations = conversations.slice(0, 5);

  return (
    <Layout>
      <div className="flex flex-col h-full animate-in fade-in duration-500 pb-10">

        {/* Welcome Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-serif text-foreground mb-1">
            Welcome back{user?.email ? `, ${user.email.split('@')[0]}` : ''}
          </h1>
          <p className="text-sm text-muted-foreground">Here's your ARTHA activity at a glance.</p>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          {loadingAnalytics ? (
            Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="bg-card border border-border rounded-2xl p-6 flex items-center justify-center h-32">
                <Loader2 className="w-5 h-5 text-brand-red animate-spin" />
              </div>
            ))
          ) : (
            <>
              <StatCard
                label="Conversations"
                value={analytics?.total_conversations ?? 0}
                icon={<MessageSquare className="w-5 h-5 text-brand-red" />}
              />
              <StatCard
                label="Messages"
                value={analytics?.total_messages ?? 0}
                icon={<FileText className="w-5 h-5 text-brand-red" />}
              />
              <StatCard
                label="Citations"
                value={analytics?.total_citations ?? 0}
                icon={<BookOpen className="w-5 h-5 text-brand-red" />}
              />
              <StatCard
                label="Docs Indexed"
                value={analytics?.documents_indexed ?? 0}
                icon={<BarChart3 className="w-5 h-5 text-brand-red" />}
              />
            </>
          )}
        </div>

        {/* Recent Conversations */}
        <div>
          <div className="flex justify-between items-end mb-4 px-1">
            <h3 className="text-xl font-serif text-foreground">Recent Conversations</h3>
            <button
              onClick={() => navigate('/chat')}
              className="text-xs font-semibold text-brand-red hover:text-brand-red/80 transition-colors flex items-center gap-1"
            >
              New Chat <ArrowRight className="w-3 h-3" />
            </button>
          </div>

          <div className="bg-card border border-border rounded-2xl shadow-sm overflow-hidden">
            {isLoadingConversations ? (
              <div className="flex items-center justify-center p-12">
                <Loader2 className="w-6 h-6 text-brand-red animate-spin" />
              </div>
            ) : recentConversations.length === 0 ? (
              <div className="flex flex-col items-center justify-center p-16 text-center">
                <MessageSquare className="w-10 h-10 text-muted-foreground/30 mb-4" />
                <p className="text-sm font-medium text-foreground mb-1">No conversations yet</p>
                <p className="text-xs text-muted-foreground mb-6">
                  Start asking legal questions to see your history here.
                </p>
                <button
                  onClick={() => navigate('/chat')}
                  className="px-4 py-2 bg-brand-red text-white text-xs font-semibold rounded-lg hover:bg-brand-red/90 transition-colors"
                >
                  Start a Conversation
                </button>
              </div>
            ) : (
              <ul className="divide-y divide-border">
                {recentConversations.map((conv) => (
                  <li
                    key={conv.id}
                    onClick={() => navigate(`/chat?conv=${conv.id}`)}
                    className="flex items-center justify-between px-6 py-4 hover:bg-secondary/40 transition-colors cursor-pointer group"
                  >
                    <div className="flex items-center gap-4 min-w-0">
                      <div className="w-8 h-8 rounded-full bg-red-50 flex items-center justify-center shrink-0">
                        <MessageSquare className="w-4 h-4 text-brand-red" />
                      </div>
                      <div className="min-w-0">
                        <p className="text-sm font-medium text-foreground truncate">{conv.title}</p>
                        <p className="text-xs text-muted-foreground">
                          {conv.message_count} message{conv.message_count !== 1 ? 's' : ''} · {new Date(conv.updated_at).toLocaleDateString()}
                        </p>
                      </div>
                    </div>
                    <ArrowRight className="w-4 h-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity shrink-0" />
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>

      </div>
    </Layout>
  );
}

function StatCard({ label, value, icon }: { label: string; value: number; icon: React.ReactNode }) {
  return (
    <div className="bg-card border border-border rounded-2xl p-6 shadow-sm flex flex-col gap-3">
      <div className="w-9 h-9 bg-red-50 rounded-full flex items-center justify-center">
        {icon}
      </div>
      <div>
        <p className="text-2xl font-bold text-foreground">{value.toLocaleString()}</p>
        <p className="text-xs text-muted-foreground font-medium mt-0.5">{label}</p>
      </div>
    </div>
  );
}
