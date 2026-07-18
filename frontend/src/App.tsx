import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import Chat from './pages/Chat';
import Corpus from './pages/Corpus';
import Landing from './pages/Landing';
import Auth from './pages/Auth';
import Analytics from './pages/Analytics';
import Profile from './pages/Profile';
import Verification from './pages/Verification';
import Admin from './pages/Admin';
import { useChatStore } from './store/chatStore';
import { useEffect } from 'react';

// Protected route wrapper
const ProtectedRoute = ({ children, requireApproved = true }: { children: React.ReactNode, requireApproved?: boolean }) => {
  const { user } = useChatStore();
  
  if (!user) {
    return <Navigate to="/auth" replace />;
  }
  
  if (requireApproved && user.status !== 'approved') {
    return <Navigate to="/verification" replace />;
  }
  
  return <>{children}</>;
};

function App() {
  const { isDarkMode } = useChatStore();

  useEffect(() => {
    if (isDarkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [isDarkMode]);

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/auth" element={<Auth />} />

        <Route 
          path="/verification" 
          element={
            <ProtectedRoute requireApproved={false}>
              <Verification />
            </ProtectedRoute>
          } 
        />

        <Route path="/admin" element={<Admin />} />
        
        <Route 
          path="/dashboard" 
          element={
            <ProtectedRoute requireApproved={false}>
              <Dashboard />
            </ProtectedRoute>
          } 
        />
        
        <Route 
          path="/chat" 
          element={
            <ProtectedRoute>
              <Chat />
            </ProtectedRoute>
          } 
        />
        
        <Route 
          path="/corpus" 
          element={
            <ProtectedRoute requireApproved={false}>
              <Corpus />
            </ProtectedRoute>
          } 
        />

        <Route 
          path="/analytics" 
          element={
            <ProtectedRoute requireApproved={false}>
              <Analytics />
            </ProtectedRoute>
          } 
        />
        
        <Route 
          path="/profile" 
          element={
            <ProtectedRoute requireApproved={false}>
              <Profile />
            </ProtectedRoute>
          } 
        />

        {/* Fallback */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
