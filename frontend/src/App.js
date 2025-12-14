import React from 'react';
import { BrowserRouter as Router, Routes, Route, useLocation } from 'react-router-dom';
import Navigation from './components/Navigation';
import MainLayout from './components/MainLayout';
import DynamicAgentBuilder from './components/DynamicAgentBuilder';
import LandingPage from './components/LandingPage';
import AuthCallback from './components/AuthCallback';
import { AuthProvider } from './context/AuthContext';
import { Toaster } from '@/components/ui/toaster';
import './App.css';

function AppRouter() {
  const location = useLocation();

  // CRITICAL: Handle session_id during render to avoid race conditions
  if (location.hash?.includes('session_id=')) {
    return <AuthCallback />;
  }

  return (
    <div className="h-screen w-screen overflow-hidden flex flex-col">
      <Navigation />
      <div className="flex-1 overflow-hidden">
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/agents" element={<MainLayout />} />
          <Route path="/agent-builder" element={<DynamicAgentBuilder />} />
        </Routes>
      </div>
      <Toaster />
    </div>
  );
}

function App() {
  return (
    <AuthProvider>
      <Router>
        <AppRouter />
      </Router>
    </AuthProvider>
  );
}

export default App;
