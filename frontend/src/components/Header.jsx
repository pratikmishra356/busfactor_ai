import React from 'react';
import { Zap } from 'lucide-react';

export default function Header() {
  return (
    <header className="h-14 border-b border-slate-200 bg-white flex items-center justify-between px-6" data-testid="header">
      {/* Left - Logo */}
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center shadow-sm">
          <Zap className="w-4 h-4 text-white" />
        </div>
        <span className="font-heading font-bold text-lg text-slate-900">Context Intelligence</span>
      </div>

      {/* Right - Brand */}
      <div className="flex items-center gap-2" data-testid="brand-logo">
        <span className="text-sm text-slate-500">Powered by</span>
        <span className="font-heading font-bold text-blue-600">busfactor AI</span>
      </div>
    </header>
  );
}
