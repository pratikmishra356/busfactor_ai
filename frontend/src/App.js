import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import KnowledgeBase from './pages/KnowledgeBase';
import IncidentAnalysis from './pages/IncidentAnalysis';
import AICompanion from './pages/AICompanion';
import './App.css';

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/knowledge" element={<KnowledgeBase />} />
          <Route path="/incident" element={<IncidentAnalysis />} />
          <Route path="/companion" element={<AICompanion />} />
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;
