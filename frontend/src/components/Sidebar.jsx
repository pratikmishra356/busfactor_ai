import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Brain, Database, AlertTriangle, Users, ChevronRight } from 'lucide-react';

const navItems = [
  { path: '/', label: 'Dashboard', icon: Brain },
  { path: '/knowledge', label: 'Knowledge Base', icon: Database },
  { path: '/incident', label: 'Incident Analysis', icon: AlertTriangle },
  { path: '/companion', label: 'AI Companion', icon: Users },
];

export default function Sidebar() {
  const location = useLocation();

  return (
    <aside className="fixed left-0 top-0 h-screen w-64 bg-surface border-r border-border flex flex-col z-50">
      {/* Logo */}
      <div className="p-6 border-b border-border">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-primary rounded-sm flex items-center justify-center">
            <Brain className="w-6 h-6 text-black" />
          </div>
          <div>
            <h1 className="font-heading font-bold text-lg tracking-tight">Context AI</h1>
            <p className="text-xs text-text-muted uppercase tracking-widest">Intelligence</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4">
        <ul className="space-y-1">
          {navItems.map((item) => {
            const isActive = location.pathname === item.path;
            const Icon = item.icon;
            
            return (
              <li key={item.path}>
                <Link
                  to={item.path}
                  data-testid={`nav-${item.label.toLowerCase().replace(' ', '-')}`}
                  className={`
                    flex items-center gap-3 px-4 py-3 rounded-sm transition-fast
                    ${isActive 
                      ? 'bg-primary text-black font-semibold' 
                      : 'text-text-muted hover:text-white hover:bg-border/50'
                    }
                  `}
                >
                  <Icon className="w-5 h-5" strokeWidth={1.5} />
                  <span className="flex-1">{item.label}</span>
                  {isActive && <ChevronRight className="w-4 h-4" />}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-border">
        <div className="text-xs text-text-muted">
          <p className="uppercase tracking-widest mb-1">Powered by</p>
          <p className="text-white font-medium">Emergent AI</p>
        </div>
      </div>
    </aside>
  );
}
