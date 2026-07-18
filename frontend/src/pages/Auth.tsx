import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Mail, Lock, ArrowRight, Loader2 } from 'lucide-react';
import { useChatStore } from '../store/chatStore';
import { arthaApi } from '../api/artha';

export default function Auth() {
  const [isSignIn, setIsSignIn] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  
  const navigate = useNavigate();
  const { setAuth } = useChatStore();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const endpoint = isSignIn ? '/auth/login' : '/auth/register';
      const res = await arthaApi.post(endpoint, { email, password });
      
      const token = res.data.access_token;
      
      // Temporarily set auth so the interceptor uses the token for the next request
      setAuth({ id: '', email: '', plan: '' }, token);
      
      // Fetch user profile
      const meRes = await arthaApi.get('/auth/me');
      setAuth(meRes.data, token);
      
      navigate('/dashboard');
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      if (typeof detail === 'string') {
        setError(detail);
      } else if (Array.isArray(detail)) {
        setError(detail.map((d: any) => d.msg).join(', '));
      } else {
        setError('An unexpected error occurred. Please try again.');
      }
      // Revert the temporary auth state on failure
      setAuth(null as any, null as any); 
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-brand-bg flex items-center justify-center relative overflow-hidden font-sans">
      {/* Decorative blurs */}
      <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] rounded-full bg-brand-red/5 blur-[100px] pointer-events-none" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] rounded-full bg-secondary/5 blur-[100px] pointer-events-none" />

      <div className="w-full max-w-md bg-card p-8 rounded-2xl shadow-sm border border-border relative z-10 animate-in fade-in slide-in-from-bottom-4 duration-500">
        
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-2xl font-serif font-bold tracking-wide">
            <span className="text-brand-red">ARTHA</span>
            <br />
            <span className="text-foreground text-lg">Intelligence</span>
          </h1>
        </div>

        {/* Tabs */}
        <div className="flex bg-secondary p-1 rounded-lg mb-8 border border-border">
          <button 
            type="button"
            onClick={() => setIsSignIn(true)}
            className={`flex-1 py-2 text-sm font-medium rounded-md transition-all ${isSignIn ? 'bg-card shadow-sm text-foreground' : 'text-muted-foreground hover:text-foreground'}`}
          >
            Sign In
          </button>
          <button 
            type="button"
            onClick={() => setIsSignIn(false)}
            className={`flex-1 py-2 text-sm font-medium rounded-md transition-all ${!isSignIn ? 'bg-card shadow-sm text-foreground' : 'text-muted-foreground hover:text-foreground'}`}
          >
            Create Account
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-5">
          {error && (
            <div className="p-3 bg-red-50 text-brand-red text-xs rounded-lg border border-red-100 font-medium">
              {error}
            </div>
          )}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-foreground">Professional Email</label>
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <input 
                type="email" 
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@firm.com" 
                className="w-full bg-secondary border border-border rounded-lg py-2.5 pl-10 pr-4 text-sm text-foreground placeholder:text-muted-foreground/60 focus:outline-none focus:ring-1 focus:ring-brand-red/50 focus:border-brand-red transition-all"
                disabled={loading}
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <div className="flex justify-between items-center">
              <label className="text-xs font-semibold text-foreground">Password</label>
            </div>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <input 
                type="password" 
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••" 
                className="w-full bg-secondary border border-border rounded-lg py-2.5 pl-10 pr-4 text-sm text-foreground placeholder:text-muted-foreground/60 focus:outline-none focus:ring-1 focus:ring-brand-red/50 focus:border-brand-red transition-all"
                disabled={loading}
              />
            </div>
          </div>

          <button 
            type="submit"
            disabled={loading}
            className="w-full mt-2 py-3 bg-card border border-border rounded-lg text-brand-red font-semibold text-sm flex items-center justify-center gap-2 hover:bg-secondary hover:border-brand-red/30 transition-all group shadow-sm disabled:opacity-70 disabled:cursor-not-allowed"
          >
            {loading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <>
                Enter Workspace
                <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </>
            )}
          </button>
        </form>

        <div className="mt-8 text-center">
          <p className="text-[10px] text-muted-foreground">
            By continuing, you agree to our Terms and Privacy Policy.
          </p>
        </div>

      </div>
    </div>
  );
}
