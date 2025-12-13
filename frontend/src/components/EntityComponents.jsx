import React from 'react';
import { MessageSquare, AlertTriangle, GitBranch, FileText, Users, Clock } from 'lucide-react';

const SOURCE_CONFIG = {
  slack: { icon: MessageSquare, color: 'bg-purple-500/20 text-purple-400', label: 'Slack' },
  jira: { icon: AlertTriangle, color: 'bg-blue-500/20 text-blue-400', label: 'Jira' },
  github: { icon: GitBranch, color: 'bg-green-500/20 text-green-400', label: 'GitHub' },
  docs: { icon: FileText, color: 'bg-yellow-500/20 text-yellow-400', label: 'Docs' },
  meetings: { icon: Users, color: 'bg-pink-500/20 text-pink-400', label: 'Meetings' },
};

export function SourceBadge({ source }) {
  const config = SOURCE_CONFIG[source] || SOURCE_CONFIG.docs;
  const Icon = config.icon;
  
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-sm text-xs font-medium ${config.color}`} data-testid={`source-badge-${source}`}>
      <Icon className="w-3 h-3" />
      {config.label}
    </span>
  );
}

export function EntityCard({ entity }) {
  return (
    <div className="bg-surface border border-border rounded-sm p-4 hover:border-primary/30 transition-colors" data-testid={`entity-card-${entity.entity_id || entity.id}`}>
      <div className="flex items-start justify-between gap-3 mb-2">
        <SourceBadge source={entity.source} />
        {entity.timestamp && (
          <span className="text-xs text-text-muted flex items-center gap-1">
            <Clock className="w-3 h-3" />
            {entity.timestamp.split('T')[0]}
          </span>
        )}
      </div>
      <h4 className="font-medium text-white text-sm mb-1 line-clamp-2">
        {entity.title}
      </h4>
      {entity.preview && (
        <p className="text-xs text-text-muted line-clamp-2">
          {entity.preview}
        </p>
      )}
    </div>
  );
}

export function SummaryCard({ summary, onClick }) {
  return (
    <div 
      className="bg-surface border border-border rounded-sm p-4 hover:border-primary/30 transition-colors cursor-pointer"
      onClick={onClick}
      data-testid={`summary-card-${summary.week_key}`}
    >
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs uppercase tracking-widest text-primary font-bold">{summary.week_key}</span>
        <span className="text-xs text-text-muted">{summary.entity_count} entities</span>
      </div>
      <p className="text-sm text-text-muted line-clamp-3 leading-relaxed mb-3">
        {summary.summary_text}
      </p>
      <div className="flex flex-wrap gap-1">
        {summary.sources?.map((source) => (
          <SourceBadge key={source} source={source} />
        ))}
      </div>
    </div>
  );
}

export function TimelineEvent({ event }) {
  const config = SOURCE_CONFIG[event.source] || SOURCE_CONFIG.docs;
  const Icon = config.icon;
  
  return (
    <div className="flex gap-4 pb-4 border-l-2 border-border pl-4 ml-2 relative" data-testid={`timeline-event-${event.entity_id}`}>
      <div className={`absolute -left-[11px] top-0 w-5 h-5 rounded-full ${config.color} flex items-center justify-center`}>
        <Icon className="w-3 h-3" />
      </div>
      <div className="flex-1">
        <div className="flex items-center gap-2 mb-1">
          <span className="text-xs text-text-muted font-mono">{event.timestamp?.split('T')[0]}</span>
          <SourceBadge source={event.source} />
        </div>
        <p className="text-sm text-white">{event.title}</p>
      </div>
    </div>
  );
}

export function WeekBadge({ week }) {
  return (
    <span className="inline-flex items-center px-2 py-1 bg-primary/20 text-primary text-xs font-mono rounded-sm">
      {week}
    </span>
  );
}
