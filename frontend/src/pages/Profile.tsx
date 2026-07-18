import Layout from '../components/ui/Layout';
import { useChatStore } from '../store/chatStore';
import { User as UserIcon, Mail, CreditCard, LogOut } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export default function Profile() {
  const { user, logout } = useChatStore();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/auth');
  };

  return (
    <Layout>
      <div className="flex flex-col h-full animate-in fade-in duration-500 pb-10">
        
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-serif text-foreground mb-2">Profile & Settings</h1>
          <p className="text-muted-foreground text-sm">
            Manage your account and preferences.
          </p>
        </div>

        <div className="max-w-3xl space-y-6">
          
          {/* Profile Card */}
          <div className="bg-card border border-border rounded-2xl shadow-sm overflow-hidden relative">
             <div className="h-32 bg-gradient-to-r from-red-50 to-brand-red-light/30 border-b border-border"></div>
             <div className="px-8 pb-8 relative">
                {/* Avatar */}
                <div className="absolute -top-12 w-24 h-24 bg-card rounded-full p-1 border border-border shadow-sm">
                  <div className="w-full h-full bg-secondary rounded-full flex items-center justify-center overflow-hidden">
                    <UserIcon className="w-12 h-12 text-muted-foreground opacity-50" />
                  </div>
                </div>

                <div className="pt-16">
                  <h2 className="text-xl font-serif font-bold text-foreground mb-1">
                    {user?.email ? user.email.split('@')[0] : 'User'}
                  </h2>
                  <p className="text-sm text-muted-foreground flex items-center gap-2">
                    <Mail className="w-4 h-4" />
                    {user?.email || 'user@example.com'}
                  </p>

                  <div className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="p-4 bg-secondary border border-border rounded-xl">
                      <div className="flex items-center gap-2 mb-2 text-brand-red font-semibold text-sm">
                        <CreditCard className="w-4 h-4" />
                        Subscription Plan
                      </div>
                      <p className="text-foreground capitalize font-medium">
                        {user?.plan || 'Free'} Plan
                      </p>
                    </div>

                    <div className="p-4 bg-secondary border border-border rounded-xl">
                       <div className="flex items-center gap-2 mb-2 text-brand-red font-semibold text-sm">
                        <UserIcon className="w-4 h-4" />
                        Account ID
                      </div>
                      <p className="text-muted-foreground text-xs font-mono break-all">
                        {user?.id || 'Unknown ID'}
                      </p>
                    </div>
                  </div>
                </div>
             </div>
          </div>

          {/* Actions */}
          <div className="bg-card border border-border rounded-2xl shadow-sm p-6">
            <h3 className="text-lg font-serif font-bold text-foreground mb-4">Account Actions</h3>
            <div className="space-y-3">
               <button className="w-full flex justify-between items-center px-4 py-3 bg-secondary hover:bg-secondary border border-border rounded-xl transition-colors">
                  <span className="text-sm font-medium text-foreground">Change Password</span>
                  <span className="text-xs text-muted-foreground">Update &gt;</span>
               </button>
               <button 
                  onClick={handleLogout}
                  className="w-full flex justify-between items-center px-4 py-3 bg-red-50 hover:bg-red-100 border border-red-100 rounded-xl transition-colors text-brand-red"
               >
                  <span className="text-sm font-medium flex items-center gap-2">
                    <LogOut className="w-4 h-4" />
                    Log Out
                  </span>
               </button>
            </div>
          </div>

        </div>
      </div>
    </Layout>
  );
}
