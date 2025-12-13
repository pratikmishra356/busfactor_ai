import React from 'react';
import { MessageSquare, FileText, GitPullRequest, Ticket, Video } from 'lucide-react';

const sourceConfig = {
  slack: { icon: MessageSquare, color: 'purple', label: 'Slack' },
  jira: { icon: Ticket, color: 'blue', label: 'Jira' },
  github: { icon: GitPullRequest, color: 'green', label: 'GitHub' },
  docs: { icon: FileText, color: 'yellow', label: 'Docs' },
  meetings: { icon: Video, color: 'pink', label: 'Meetings' },
};

export function SourceBadge({ source }) {
  const config = sourceConfig[source] || { icon: FileText, color: 'gray', label: source };
  const Icon = config.icon;

  return (
    <span className={`badge badge-${source}`} data-testid={`source-badge-${source}`}>
      <Icon className="w-3 h-3 mr-1" />
      {config.label}
    </span>
  );
}

export function SourceBadgeList({ sources }) {
  if (!sources || sources.length === 0) return null;
  
  return (
    <div className="flex flex-wrap gap-2">
      {sources.map((source, index) => (
        <SourceBadge key={index} source={source} />
      ))}
    </div>
  );
}

export function EntityCard({ entity, onClick }) {
  const sourceConf = sourceConfig[entity.source] || sourceConfig.docs;
  const Icon = sourceConf.icon;

  return (
    <div 
      className="bg-surface border border-border rounded-sm p-4 card-hover cursor-pointer"
      onClick={onClick}
      data-testid={`entity-card-${entity.entity_id || entity.id}`}
    >
      <div className="flex items-start gap-3">
        <div className={`w-8 h-8 rounded-sm flex items-center justify-center bg-${sourceConf.color}-500/20`}>
          <Icon className={`w-4 h-4 text-${sourceConf.color}-400`} />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <SourceBadge source={entity.source} />
            {entity.type && (
              <span className="text-xs text-text-muted">{entity.type}</span>
            )}
          </div>
          <h4 className="font-medium text-white truncate">{entity.title}</h4>
          {entity.preview && (
            <p className="text-sm text-text-muted mt-1 line-clamp-2">{entity.preview}</p>
          )}
        </div>
      </div>
    </div>
  );
}

export function TimelineEvent({ event }) {
  const sourceConf = sourceConfig[event.source] || sourceConfig.docs;
  const Icon = sourceConf.icon;
  
  const formatDate = (timestamp) => {
    if (!timestamp) return '';
    try {
      return new Date(timestamp).toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return timestamp;
    }
  };

  return (
    <div className="flex gap-4" data-testid="timeline-event">
      <div className="flex flex-col items-center">
        <div className={`w-8 h-8 rounded-full flex items-center justify-center bg-${sourceConf.color}-500/20 border-2 border-${sourceConf.color}-500/50`}>
          <Icon className={`w-4 h-4 text-${sourceConf.color}-400`} />
        </div>
        <div className="w-px flex-1 bg-border mt-2" />
      </div>
      <div className="flex-1 pb-6">
        <p className="text-xs text-text-muted mb-1">{formatDate(event.timestamp)}</p>
        <p className="text-white font-medium">{event.title}</p>
        <SourceBadge source={event.source} />
      </div>
    </div>
  );
}

export default { SourceBadge, SourceBadgeList, EntityCard, TimelineEvent };
