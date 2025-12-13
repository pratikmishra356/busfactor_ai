import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Search, AlertTriangle, Bot, LayoutDashboard } from 'lucide-react';

const NAV_ITEMS = [
  { path: '/', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/knowledge', label: 'Knowledge Base', icon: Search },
  { path: '/incident', label: 'Incident Analysis', icon: AlertTriangle },
  { path: '/companion', label: 'AI Companion', icon: Bot },
];

export default function Layout({ children }) {
  const location = useLocation();

  return (
    <div className="min-h-screen bg-background text-white">
      {/* Navigation */}
      <nav className="border-b border-border bg-surface/50 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6">
          <div className="flex items-center justify-between h-16">
            {/* Logo */}
            <Link to="/" className="flex items-center gap-2" data-testid="nav-logo">
              <div className="w-8 h-8 bg-primary rounded-sm flex items-center justify-center">
                <span className="font-heading font-black text-black text-sm">CI</span>
              </div>
              <span className="font-heading font-bold text-lg hidden md:block">Context Intelligence</span>
            </Link>

            {/* Nav Links */}
            <div className="flex items-center gap-1">
              {NAV_ITEMS.map((item) => {
                const isActive = location.pathname === item.path;
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    data-testid={`nav-${item.label.toLowerCase().replace(/ /g, '-')}`}
                    className={`
                      flex items-center gap-2 px-4 py-2 rounded-sm text-sm font-medium transition-colors
                      ${isActive 
                        ? 'bg-primary text-black' 
                        : 'text-text-muted hover:text-white hover:bg-border/30'
                      }
                    `}
                  >
                    <item.icon className="w-4 h-4" />
                    <span className="hidden md:inline">{item.label}</span>
                  </Link>
                );
              })}
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main>
        {children}
      </main>

      {/* Footer */}
      <footer className="border-t border-border py-6 mt-12">
        <div className="max-w-7xl mx-auto px-6">
          <p className="text-xs text-text-muted text-center">
            Context Intelligence Platform • Powered by Vector Search & AI
          </p>
        </div>
      </footer>
    </div>
  );
}
