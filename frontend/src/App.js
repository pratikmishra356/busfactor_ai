import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navigation from './components/Navigation';
import MainLayout from './components/MainLayout';
import DynamicAgentBuilder from './components/DynamicAgentBuilder';
import LandingPage from './components/LandingPage';
import './App.css';

function App() {
  return (
    <Router>
      <div className="h-screen w-screen overflow-hidden flex flex-col">
        <Navigation />
        <div className="flex-1 overflow-hidden">
          <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/agents" element={<MainLayout />} />
            <Route path="/agent-builder" element={<DynamicAgentBuilder />} />
          </Routes>
        </div>
      </div>
    </Router>
  );
}

export default App;
