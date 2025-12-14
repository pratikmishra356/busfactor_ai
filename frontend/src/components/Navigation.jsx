import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Bot, Home, LogOut, Zap } from 'lucide-react';
import { useAuth } from '@/context/AuthContext';
import { Button } from '@/components/ui/button';

export default function Navigation() {
  const location = useLocation();
  const isHome = location.pathname === '/';
  const { isAuthenticated, user, team, login, logout } = useAuth();

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

      {/* Center/Right */}
      {isHome ? (
        <div className="flex items-center gap-3">
          {isAuthenticated && (
            <Link
              to="/agents"
              className="inline-flex items-center px-3 py-1.5 rounded-xl border border-slate-200 bg-white shadow-sm text-sm text-slate-700 hover:bg-slate-50 transition-colors"
              title="Open Agents"
            >
              {team?.team_name ? (
                <>
                  <span className="text-slate-500 mr-1">Team</span>
                  <span className="font-semibold text-slate-900">{team.team_name}</span>
                </>
              ) : (
                <span className="font-semibold text-slate-900">Open Agents</span>
              )}
            </Link>
          )}

          {isAuthenticated && user?.name && (
            <span className="hidden sm:inline text-sm text-slate-500">{user.name}</span>
          )}

          <Button
            variant="outline"
            className="h-9 rounded-xl"
            onClick={() => (isAuthenticated ? logout() : login())}
          >
            {isAuthenticated ? (
              <>
                <LogOut className="w-4 h-4" />
                Logout
              </>
            ) : (
              'Login'
            )}
          </Button>
        </div>
      ) : (
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

          {/* Right - User */}
          <div className="hidden sm:flex items-center gap-3">
            {team?.team_name && (
              <span className="text-sm text-slate-600">Team: <span className="font-semibold text-slate-900">{team.team_name}</span></span>
            )}
            {isAuthenticated && user?.name && (
              <span className="text-sm text-slate-500">{user.name}</span>
            )}
            {isAuthenticated ? (
              <Button
                variant="outline"
                size="sm"
                className="h-9 rounded-xl"
                onClick={() => logout()}
              >
                <LogOut className="w-4 h-4" />
                Logout
              </Button>
            ) : (
              <Button
                variant="outline"
                size="sm"
                className="h-9 rounded-xl"
                onClick={() => login()}
              >
                Login
              </Button>
            )}
          </div>
        </>
      )}
    </nav>
  );
}
