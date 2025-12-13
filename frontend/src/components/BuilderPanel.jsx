import React from 'react';
import { Blocks, ArrowRight, Webhook, Database, GitBranch, Plug } from 'lucide-react';

const INTEGRATION_BLOCKS = [
  { id: 'webhook', name: 'Webhook Trigger', icon: Webhook, color: 'bg-blue-500' },
  { id: 'github', name: 'GitHub Events', icon: GitBranch, color: 'bg-slate-800' },
  { id: 'database', name: 'Query Context DB', icon: Database, color: 'bg-emerald-500' },
  { id: 'api', name: 'External API', icon: Plug, color: 'bg-violet-500' },
];

export default function BuilderPanel({ agent }) {
  return (
    <div className="h-full flex flex-col overflow-hidden p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-white border border-slate-200 shadow-sm flex items-center justify-center">
            <Blocks className="w-5 h-5 text-slate-600" />
          </div>
          <div>
            <h2 className="font-heading font-semibold text-slate-900">Integration Builder</h2>
            <p className="text-xs text-slate-500">Self-build and deploy custom agent workflows</p>
          </div>
        </div>
        <button
          disabled
          className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg shadow-sm opacity-50 cursor-not-allowed flex items-center gap-2"
          data-testid="deploy-agent-btn"
        >
          Deploy Agent
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>

      {/* Canvas */}
      <div className="flex-1 bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="h-full flex">
          {/* Sidebar - Available Blocks */}
          <div className="w-56 border-r border-slate-200 p-4 bg-slate-50/50">
            <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">Available Blocks</h3>
            <div className="space-y-2">
              {INTEGRATION_BLOCKS.map((block) => (
                <div
                  key={block.id}
                  className="flex items-center gap-3 p-3 bg-white rounded-lg border border-slate-200 cursor-grab hover:border-blue-300 hover:shadow-sm transition-all"
                  draggable
                  data-testid={`block-${block.id}`}
                >
                  <div className={`w-8 h-8 ${block.color} rounded-lg flex items-center justify-center`}>
                    <block.icon className="w-4 h-4 text-white" />
                  </div>
                  <span className="text-sm font-medium text-slate-700">{block.name}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Main Canvas */}
          <div className="flex-1 p-6 bg-[radial-gradient(#e2e8f0_1px,transparent_1px)] [background-size:20px_20px]">
            <div className="h-full flex flex-col items-center justify-center text-center">
              {/* Sample Flow Preview */}
              <div className="flex items-center gap-4 mb-8">
                <div className="w-24 h-16 bg-white rounded-lg border-2 border-dashed border-slate-300 flex items-center justify-center">
                  <span className="text-xs text-slate-400">Trigger</span>
                </div>
                <ArrowRight className="w-5 h-5 text-slate-300" />
                <div className="w-24 h-16 bg-white rounded-lg border-2 border-dashed border-slate-300 flex items-center justify-center">
                  <span className="text-xs text-slate-400">Agent</span>
                </div>
                <ArrowRight className="w-5 h-5 text-slate-300" />
                <div className="w-24 h-16 bg-white rounded-lg border-2 border-dashed border-slate-300 flex items-center justify-center">
                  <span className="text-xs text-slate-400">Action</span>
                </div>
              </div>

              <div className="max-w-sm">
                <h3 className="font-heading font-semibold text-slate-900 mb-2">
                  Build Custom {agent?.name} Workflows
                </h3>
                <p className="text-sm text-slate-500 mb-4">
                  Drag blocks from the sidebar to create automated workflows. Connect triggers to agents and define actions.
                </p>
                <div className="flex items-center justify-center gap-2 text-xs text-slate-400">
                  <span className="px-2 py-1 bg-amber-100 text-amber-700 rounded-full">Coming Soon</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
