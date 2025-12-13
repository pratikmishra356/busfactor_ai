import React from 'react';
import { CheckCircle2, Code2, Users, Bell, FileText } from 'lucide-react';

const AGENT_ICONS = {
  codehealth: Code2,
  employee: Users,
  oncall: Bell,
  document: FileText,
};

const AGENT_COLORS = {
  codehealth: 'text-sky-500 bg-sky-50',
  employee: 'text-violet-500 bg-violet-50',
  oncall: 'text-red-500 bg-red-50',
  document: 'text-emerald-500 bg-emerald-50',
};

export default function CompletedTasks({ tasks, activeTaskId, onTaskClick }) {
  if (tasks.length === 0) {
    return (
      <div className="h-16 border-t border-slate-100 px-4 flex items-center bg-slate-50/50">
        <span className="text-xs text-slate-400 uppercase tracking-wider font-medium">Completed Tasks</span>
        <span className="ml-3 text-xs text-slate-400">No tasks yet</span>
      </div>
    );
  }

  return (
    <div className="h-20 border-t border-slate-100 px-4 py-2 bg-slate-50/50" data-testid="completed-tasks">
      <div className="flex items-center gap-2 mb-2">
        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
        <span className="text-xs text-slate-500 uppercase tracking-wider font-medium">Completed Tasks</span>
        <span className="text-xs text-slate-400">({tasks.length})</span>
      </div>
      <div className="flex gap-2 overflow-x-auto hide-scrollbar">
        {tasks.map((task) => {
          const Icon = AGENT_ICONS[task.agent] || Code2;
          const colorClass = AGENT_COLORS[task.agent] || 'text-slate-500 bg-slate-50';
          const isActive = activeTaskId === task.id;
          
          return (
            <button
              key={task.id}
              onClick={() => onTaskClick(task)}
              className={`task-tab flex items-center gap-1.5 flex-shrink-0 transition-all cursor-pointer ${
                isActive ? 'ring-2 ring-blue-400 bg-blue-50' : 'hover:bg-slate-100'
              }`}
              data-testid={`task-${task.id}`}
              title={task.title}
            >
              <Icon className={`w-3 h-3 ${isActive ? 'text-blue-600' : colorClass.split(' ')[0]}`} />
              <span className={`truncate ${isActive ? 'text-blue-600 font-medium' : ''}`}>{task.title}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
