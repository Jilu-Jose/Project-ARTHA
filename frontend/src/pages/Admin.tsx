import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Loader2, CheckCircle2, User, Building, Clock } from 'lucide-react';
import { useChatStore } from '../store/chatStore';
import { adminLogin, arthaApi, getPendingRequests, approveRequest } from '../api/artha';
import Layout from '../components/ui/Layout';

export default function Admin() {
  const { setAuth, user } = useChatStore();
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  
  const [requests, setRequests] = useState<any[]>([]);
  const [isApproving, setIsApproving] = useState<string | null>(null);

  useEffect(() => {
    const performLoginAndFetch = async () => {
      try {
        // Authenticate silently
        const tokenRes = await adminLogin();
        const token = tokenRes.access_token;
        
        // Fetch profile with new token
        const profileRes = await arthaApi.get('/auth/me', {
          headers: {
            Authorization: `Bearer ${token}`
          }
        });
        
        // Update store
        setAuth(profileRes.data, token);
        
        // Now fetch pending requests
        const pending = await getPendingRequests();
        setRequests(pending);
        
        setIsLoading(false);
      } catch (err: any) {
        console.error('Admin login failed', err);
        setError(err.response?.data?.detail || 'Failed to authenticate as Admin');
        setIsLoading(false);
      }
    };

    performLoginAndFetch();
  }, [setAuth]);

  const handleApprove = async (userId: string) => {
    setIsApproving(userId);
    try {
      await approveRequest(userId);
      // Remove from list
      setRequests((prev) => prev.filter((r) => r.id !== userId));
    } catch (err) {
      console.error('Failed to approve', err);
      alert('Failed to approve request.');
    } finally {
      setIsApproving(null);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background flex flex-col items-center justify-center">
        <Loader2 className="w-8 h-8 text-brand-red animate-spin mb-4" />
        <p className="text-muted-foreground font-medium">Entering Admin Dashboard...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-background flex flex-col items-center justify-center px-4">
        <div className="bg-card p-8 rounded-2xl shadow-sm border border-border max-w-md w-full text-center">
          <h2 className="text-xl font-bold text-brand-red mb-2">Access Denied</h2>
          <p className="text-muted-foreground mb-6">{error}</p>
          <button 
            onClick={() => navigate('/')}
            className="px-4 py-2 bg-brand-red text-white rounded-lg hover:bg-brand-red/90 transition-colors"
          >
            Return Home
          </button>
        </div>
      </div>
    );
  }

  return (
    <Layout>
      <div className="flex flex-col h-full animate-in fade-in duration-500 pb-10">
        
        <div className="mb-8">
          <h1 className="text-2xl font-serif text-foreground mb-2">Admin Dashboard</h1>
          <p className="text-sm text-muted-foreground">Manage user access requests and platform administration.</p>
        </div>

        <div className="bg-card border border-border rounded-2xl shadow-sm overflow-hidden">
          <div className="p-6 border-b border-border bg-secondary/50">
            <h2 className="text-lg font-medium text-foreground">Pending Verification Requests</h2>
          </div>
          
          <div className="overflow-x-auto">
            {requests.length === 0 ? (
              <div className="p-12 text-center text-muted-foreground flex flex-col items-center">
                <CheckCircle2 className="w-10 h-10 mb-3 text-brand-red/50" />
                <p>No pending requests at this time.</p>
              </div>
            ) : (
              <table className="w-full text-left text-sm">
                <thead className="bg-secondary text-muted-foreground">
                  <tr>
                    <th className="px-6 py-4 font-medium">Email</th>
                    <th className="px-6 py-4 font-medium">Institution</th>
                    <th className="px-6 py-4 font-medium">Role</th>
                    <th className="px-6 py-4 font-medium">Requested</th>
                    <th className="px-6 py-4 font-medium text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {requests.map((req) => (
                    <tr key={req.id} className="hover:bg-secondary/30 transition-colors">
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2 text-foreground font-medium">
                          <User className="w-4 h-4 text-muted-foreground" />
                          {req.email}
                        </div>
                      </td>
                      <td className="px-6 py-4 text-muted-foreground">
                        <div className="flex items-center gap-2">
                          <Building className="w-4 h-4" />
                          {req.institution || 'N/A'}
                        </div>
                      </td>
                      <td className="px-6 py-4 text-muted-foreground">
                        <span className="inline-flex px-2 py-1 bg-secondary rounded-md text-xs border border-border">
                          {req.role || 'N/A'}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-muted-foreground">
                        <div className="flex items-center gap-2">
                          <Clock className="w-4 h-4" />
                          {new Date(req.created_at).toLocaleDateString()}
                        </div>
                      </td>
                      <td className="px-6 py-4 text-right">
                        <button
                          onClick={() => handleApprove(req.id)}
                          disabled={isApproving === req.id}
                          className="inline-flex items-center justify-center px-4 py-2 bg-brand-red text-white text-xs font-medium rounded-lg hover:bg-brand-red/90 transition-colors disabled:opacity-50"
                        >
                          {isApproving === req.id ? (
                            <Loader2 className="w-4 h-4 animate-spin" />
                          ) : (
                            'Approve Access'
                          )}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      </div>
    </Layout>
  );
}
