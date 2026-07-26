import { useState, type ReactNode } from 'react';
import { 
  Bell, 
  Settings, 
  Search,
  BookOpen,
  LayoutDashboard,
  BarChart2,
  LogOut,
  Plus,
  HelpCircle,
  Menu,
  X,
  User,
  Moon,
  Sun,
  ChevronLeft,
  Home
} from 'lucide-react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { useChatStore } from '../../store/chatStore';
import { cn } from '../../lib/utils';

interface LayoutProps {
  children: ReactNode;
}

export default function Layout({ children }: LayoutProps) {
  const { logout, createNewConversation } = useChatStore();
  const navigate = useNavigate();
  const location = useLocation();
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

  const [isDarkMode, setIsDarkMode] = useState(() => {
    return document.documentElement.classList.contains('dark');
  });

  const toggleTheme = () => {
    if (isDarkMode) {
      document.documentElement.classList.remove('dark');
      setIsDarkMode(false);
    } else {
      document.documentElement.classList.add('dark');
      setIsDarkMode(true);
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/auth');
  };

  const handleNewResearch = () => {
    createNewConversation();
    navigate('/chat');
  };

  return (
    <div className="flex flex-col h-screen w-full bg-sidebar overflow-hidden font-sans">
      <div className="flex flex-1 overflow-hidden relative">
        
        {/* Left Sidebar */}
        <aside 
          className={cn(
            "w-[260px] h-full bg-sidebar shrink-0 z-30 flex flex-col justify-between transition-all duration-300 absolute md:relative border-r border-border shadow-sm overflow-hidden",
            isSidebarOpen ? "translate-x-0" : "-translate-x-full md:w-0 md:border-none md:-translate-x-0"
          )}
        >
          <div>
            <div className="p-6 flex items-center justify-between">
              <Link to="/" className="flex items-center gap-3">
                <div className="w-8 h-8 bg-blue-50 rounded-full flex items-center justify-center overflow-hidden">
                   <div className="text-[10px] font-bold text-brand-red">A</div>
                </div>
                {isSidebarOpen && (
                  <div>
                    <div className="font-serif font-bold text-lg text-brand-red leading-none">ARTHA</div>
                    <div className="text-[10px] text-muted-foreground mt-0.5">Legal Workspace</div>
                  </div>
                )}
              </Link>
              
              {/* Close Sidebar Toggle */}
              <button 
                onClick={() => setIsSidebarOpen(false)} 
                className="p-1 hover:bg-secondary rounded text-muted-foreground transition-colors"
                title="Collapse Sidebar"
              >
                <ChevronLeft className="w-5 h-5" />
              </button>
            </div>

            <nav className="flex flex-col mt-4 gap-1 px-4">
              <SidebarLink 
                icon={<Home className="w-4 h-4" />} 
                label="Home" 
                active={location.pathname === '/'}
                onClick={() => navigate('/')}
                isExpanded={isSidebarOpen}
              />
              <SidebarLink 
                icon={<LayoutDashboard className="w-4 h-4" />} 
                label="Dashboard" 
                active={location.pathname === '/dashboard'}
                onClick={() => navigate('/dashboard')}
                isExpanded={isSidebarOpen}
              />
              <SidebarLink 
                icon={<Search className="w-4 h-4" />} 
                label="Legal Research" 
                active={location.pathname === '/chat'}
                onClick={() => navigate('/chat')}
                isExpanded={isSidebarOpen}
              />
              <SidebarLink 
                icon={<BookOpen className="w-4 h-4" />} 
                label="Statutes" 
                active={location.pathname === '/corpus'}
                onClick={() => navigate('/corpus')}
                isExpanded={isSidebarOpen}
              />
              <SidebarLink 
                icon={<BarChart2 className="w-4 h-4" />} 
                label="Analytics" 
                active={location.pathname === '/analytics'}
                onClick={() => navigate('/analytics')}
                isExpanded={isSidebarOpen}
              />
            </nav>
          </div>

          <div className="p-4 flex flex-col gap-2 mb-4">
            <button 
              onClick={handleNewResearch}
              className={cn(
                "py-2.5 px-4 bg-card border border-border text-brand-red rounded-lg font-semibold text-sm hover:bg-secondary transition-all shadow-sm flex items-center justify-center gap-2",
                !isSidebarOpen && "px-0 justify-center"
              )}
            >
              <Plus className="w-4 h-4" />
              {isSidebarOpen && "New Research"}
            </button>
            
            <div className="flex flex-col gap-1 mt-6">
              <button 
                onClick={() => navigate('/profile')}
                className="flex items-center gap-3 px-3 py-2.5 text-sm font-medium text-sidebar-foreground hover:text-foreground transition-colors rounded-md hover:bg-secondary"
              >
                <Settings className="w-4 h-4" />
                {isSidebarOpen && <span>Settings</span>}
              </button>
              <button className="flex items-center gap-3 px-3 py-2.5 text-sm font-medium text-sidebar-foreground hover:text-foreground transition-colors rounded-md hover:bg-secondary">
                <HelpCircle className="w-4 h-4" />
                {isSidebarOpen && <span>Support</span>}
              </button>
              <button 
                onClick={handleLogout}
                className="flex items-center gap-3 px-3 py-2.5 text-sm font-medium text-sidebar-foreground hover:text-destructive transition-colors rounded-md hover:bg-secondary"
              >
                <LogOut className="w-4 h-4" />
                {isSidebarOpen && <span>Logout</span>}
              </button>
            </div>
          </div>
        </aside>

        {/* Content Area */}
        <main className="flex-1 flex flex-col min-w-0 h-full relative overflow-y-auto bg-sidebar">
          
          {/* Top Navbar */}
          <header className="h-20 w-full flex items-center px-4 md:px-8 shrink-0 z-20 justify-between gap-4">
            <div className="flex-1 flex items-center justify-start gap-4">
              {!isSidebarOpen && (
                <button 
                  onClick={() => setIsSidebarOpen(true)}
                  className="p-2 bg-card rounded-md shadow-sm border border-border text-muted-foreground hover:text-foreground transition-colors"
                  title="Open Menu"
                >
                  <Menu className="w-5 h-5" />
                </button>
              )}
              <div className="relative w-full max-w-md hidden md:block">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <input 
                  type="text" 
                  placeholder="Search..." 
                  className="w-full bg-card border border-border rounded-full py-2.5 pl-10 pr-4 text-sm text-foreground shadow-sm focus:outline-none focus:ring-1 focus:ring-brand-red/50 focus:border-brand-red transition-all"
                />
              </div>
            </div>

            <div className="flex items-center gap-3 ml-auto">
              <button 
                onClick={toggleTheme}
                className="w-10 h-10 bg-card rounded-full flex items-center justify-center text-muted-foreground hover:text-foreground border border-border shadow-sm transition-colors"
                title="Toggle Theme"
              >
                {isDarkMode ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
              </button>
              <button className="w-10 h-10 bg-card rounded-full flex items-center justify-center text-muted-foreground hover:text-foreground border border-border shadow-sm transition-colors relative">
                <Bell className="w-4 h-4" />
                <span className="absolute top-2.5 right-2.5 w-2 h-2 bg-brand-red rounded-full border border-white"></span>
              </button>
              <button 
                onClick={() => navigate('/profile')}
                className="w-10 h-10 bg-card rounded-full flex items-center justify-center text-muted-foreground hover:text-foreground border border-border shadow-sm transition-colors"
              >
                <Settings className="w-4 h-4" />
              </button>
              <div 
                onClick={() => navigate('/profile')}
                className="w-10 h-10 rounded-full bg-secondary border border-border shadow-sm overflow-hidden ml-2 flex items-center justify-center cursor-pointer p-0.5 hover:ring-2 hover:ring-brand-red/50 transition-all"
              >
                 <User className="w-5 h-5 text-muted-foreground opacity-50" />
              </div>
            </div>
          </header>

          <div className="flex-1 w-full max-w-7xl mx-auto p-4 md:p-8 pt-0">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}

function SidebarLink({ icon, label, active, onClick, isExpanded }: { icon: ReactNode, label: string, active: boolean, onClick: () => void, isExpanded: boolean }) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "flex items-center gap-3 px-3 py-2.5 text-sm font-medium transition-all rounded-lg",
        active 
          ? "bg-red-50 text-brand-red" 
          : "text-sidebar-foreground hover:bg-secondary hover:text-foreground"
      )}
      title={!isExpanded ? label : undefined}
    >
      <div className={cn(active ? "text-brand-red" : "text-muted-foreground")}>
        {icon}
      </div>
      {isExpanded && <span>{label}</span>}
    </button>
  );
}
