import React from 'react';

export default function AgentTabs({ agents, activeAgent, onAgentChange }) {
  return (
    <div className="h-12 border-b border-slate-200 bg-slate-50/50 flex items-center px-6 gap-1" data-testid="agent-tabs">
      {agents.map((agent) => {
        const Icon = agent.icon;
        const isActive = activeAgent === agent.id;
        const isDisabled = !agent.enabled;
        
        return (
          <button
            key={agent.id}
            onClick={() => agent.enabled && onAgentChange(agent.id)}
            disabled={isDisabled}
            data-testid={`agent-tab-${agent.id}`}
            className={`
              flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all
              ${isActive 
                ? 'bg-white text-slate-900 shadow-sm border border-slate-200' 
                : isDisabled
                  ? 'text-slate-400 cursor-not-allowed'
                  : 'text-slate-600 hover:bg-white/50 hover:text-slate-900'
              }
            `}
          >
            <Icon className={`w-4 h-4 ${isActive ? agent.color : ''}`} />
            <span>{agent.name}</span>
            {isDisabled && (
              <span className="text-[10px] bg-slate-200 text-slate-500 px-1.5 py-0.5 rounded-full">Soon</span>
            )}
          </button>
        );
      })}
    </div>
  );
}
