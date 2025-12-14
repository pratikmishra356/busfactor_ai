import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Bot, Home, Zap } from 'lucide-react';

export default function Navigation() {
  const location = useLocation();
  const isHome = location.pathname === '/';

  const isActive = (path) => location.pathname === path;

  return (
    <nav className="h-14 bg-white border-b border-slate-200 flex items-center justify-between px-6 shadow-sm">
      {/* Left - Logo */}
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center shadow-sm">
          <Zap className="w-4 h-4 text-white" />
        </div>
        <span className="font-heading font-bold text-lg text-slate-900">busfactor AI</span>
      </div>

      {/* Hide tabs on Home (Landing) */}
      {!isHome && (
        <>
          {/* Center - Navigation Links */}
          <div className="flex items-center gap-1">
            <Link
              to="/"
              className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all ${
                isActive('/')
                  ? 'bg-blue-50 text-blue-600 font-medium'
                  : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
              }`}
            >
              <Home className="w-4 h-4" />
              <span>Home</span>
            </Link>

            <Link
              to="/agents"
              className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all ${
                isActive('/agents')
                  ? 'bg-blue-50 text-blue-600 font-medium'
                  : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
              }`}
            >
              <span className="text-sm font-semibold">Agents</span>
            </Link>

            <Link
              to="/agent-builder"
              className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all ${
                isActive('/agent-builder')
                  ? 'bg-gradient-to-r from-blue-50 to-purple-50 text-purple-600 font-medium border border-purple-200'
                  : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
              }`}
            >
              <Bot className="w-4 h-4" />
              <span>Agent Builder</span>
              {isActive('/agent-builder') && (
                <span className="px-1.5 py-0.5 bg-purple-100 text-purple-700 text-xs font-semibold rounded">NEW</span>
              )}
            </Link>
          </div>

          {/* Right - Tagline */}
          <div className="hidden sm:flex items-center gap-2">
            <span className="text-sm text-slate-500">MCP + RAG for Engineering Ops</span>
          </div>
        </>
      )}

      {/* Spacer to keep logo left when home */}
      {isHome && <div className="w-8" />}
    </nav>
  );
}
