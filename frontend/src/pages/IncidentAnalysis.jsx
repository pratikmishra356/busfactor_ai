import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { AlertTriangle, Loader2, FileText, GitPullRequest, Clock, CheckCircle, AlertCircle } from 'lucide-react';
import SearchInput from '../components/SearchInput';
import { SourceBadge, TimelineEvent } from '../components/EntityComponents';
import { getIncidentReport } from '../services/api';

export default function IncidentAnalysis() {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('report');

  const handleSearch = async (searchQuery) => {
    setLoading(true);
    setError(null);
    
    try {
      const data = await getIncidentReport(searchQuery);
      setResult(data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to generate incident report. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const tabs = [
    { id: 'report', label: 'RCA Report', icon: FileText },
    { id: 'timeline', label: 'Timeline', icon: Clock },
    { id: 'related', label: 'Related Items', icon: GitPullRequest },
  ];

  return (
    <div className="p-8 max-w-6xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-12 h-12 bg-error/20 rounded-sm flex items-center justify-center">
            <AlertTriangle className="w-6 h-6 text-error" />
          </div>
          <div>
            <h1 className="font-heading font-bold text-3xl tracking-tight">Incident Analysis</h1>
            <p className="text-text-muted">Generate RCA reports with timeline and recommendations</p>
          </div>
        </div>
      </div>

      {/* Search */}
      <div className="mb-8">
        <SearchInput
          value={query}
          onChange={setQuery}
          onSubmit={handleSearch}
          loading={loading}
          placeholder="Describe the incident... e.g., 'payment outage' or 'email notification failure'"
        />
      </div>

      {/* Error */}
      {error && (
        <div className="bg-error/10 border border-error/30 rounded-sm p-4 mb-6" data-testid="error-message">
          <p className="text-error">{error}</p>
        </div>
      )}

      {/* Results */}
      {result && (
        <div className="space-y-6" data-testid="incident-results">
          {/* Quick Stats */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-surface border border-border rounded-sm p-4">
              <div className="flex items-center gap-3">
                <AlertCircle className="w-8 h-8 text-error" />
                <div>
                  <p className="text-2xl font-heading font-bold text-white">{result.related_tickets?.length || 0}</p>
                  <p className="text-xs text-text-muted uppercase tracking-widest">Related Tickets</p>
                </div>
              </div>
            </div>
            <div className="bg-surface border border-border rounded-sm p-4">
              <div className="flex items-center gap-3">
                <GitPullRequest className="w-8 h-8 text-success" />
                <div>
                  <p className="text-2xl font-heading font-bold text-white">{result.related_prs?.length || 0}</p>
                  <p className="text-xs text-text-muted uppercase tracking-widest">Related PRs</p>
                </div>
              </div>
            </div>
            <div className="bg-surface border border-border rounded-sm p-4">
              <div className="flex items-center gap-3">
                <Clock className="w-8 h-8 text-info" />
                <div>
                  <p className="text-2xl font-heading font-bold text-white">{result.timeline?.length || 0}</p>
                  <p className="text-xs text-text-muted uppercase tracking-widest">Timeline Events</p>
                </div>
              </div>
            </div>
          </div>

          {/* Tabs */}
          <div className="bg-surface border border-border rounded-sm overflow-hidden">
            <div className="flex border-b border-border">
              {tabs.map((tab) => {
                const Icon = tab.icon;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    data-testid={`tab-${tab.id}`}
                    className={`
                      flex items-center gap-2 px-6 py-4 text-sm font-medium transition-colors
                      ${activeTab === tab.id 
                        ? 'bg-primary text-black border-b-2 border-primary' 
                        : 'text-text-muted hover:text-white hover:bg-border/30'
                      }
                    `}
                  >
                    <Icon className="w-4 h-4" />
                    {tab.label}
                  </button>
                );
              })}
            </div>

            <div className="p-6">
              {/* RCA Report Tab */}
              {activeTab === 'report' && (
                <div className="markdown-content text-text-muted leading-relaxed" data-testid="rca-report">
                  <ReactMarkdown>{result.report}</ReactMarkdown>
                </div>
              )}

              {/* Timeline Tab */}
              {activeTab === 'timeline' && (
                <div data-testid="timeline-view">
                  {result.timeline && result.timeline.length > 0 ? (
                    <div className="space-y-0">
                      {result.timeline.map((event, idx) => (
                        <TimelineEvent key={idx} event={event} />
                      ))}
                    </div>
                  ) : (
                    <p className="text-text-muted text-center py-8">No timeline events available</p>
                  )}
                </div>
              )}

              {/* Related Items Tab */}
              {activeTab === 'related' && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6" data-testid="related-items">
                  {/* Related Tickets */}
                  <div>
                    <h4 className="font-heading font-bold text-lg mb-4 text-white flex items-center gap-2">
                      <AlertCircle className="w-5 h-5 text-error" />
                      Jira Tickets
                    </h4>
                    {result.related_tickets && result.related_tickets.length > 0 ? (
                      <ul className="space-y-2">
                        {result.related_tickets.map((ticket, idx) => (
                          <li key={idx} className="flex items-center gap-2 p-3 bg-background rounded-sm border border-border">
                            <SourceBadge source="jira" />
                            <span className="font-mono text-sm text-white">{ticket}</span>
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <p className="text-text-muted text-sm">No related tickets found</p>
                    )}
                  </div>

                  {/* Related PRs */}
                  <div>
                    <h4 className="font-heading font-bold text-lg mb-4 text-white flex items-center gap-2">
                      <GitPullRequest className="w-5 h-5 text-success" />
                      Pull Requests
                    </h4>
                    {result.related_prs && result.related_prs.length > 0 ? (
                      <ul className="space-y-2">
                        {result.related_prs.map((pr, idx) => (
                          <li key={idx} className="flex items-center gap-2 p-3 bg-background rounded-sm border border-border">
                            <SourceBadge source="github" />
                            <span className="font-mono text-sm text-white">{pr}</span>
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <p className="text-text-muted text-sm">No related PRs found</p>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Empty State */}
      {!loading && !result && !error && (
        <div className="text-center py-16">
          <AlertTriangle className="w-16 h-16 text-border mx-auto mb-4" />
          <h3 className="font-heading text-xl text-text-muted mb-2">Analyze an Incident</h3>
          <p className="text-text-muted text-sm max-w-md mx-auto">
            Enter an incident description to generate a comprehensive RCA report with timeline and recommendations.
          </p>
          <div className="mt-6 flex flex-wrap justify-center gap-2">
            {['payment outage', 'email notification failure', 'database connection issues', 'security vulnerability'].map((suggestion) => (
              <button
                key={suggestion}
                onClick={() => {
                  setQuery(suggestion);
                  handleSearch(suggestion);
                }}
                data-testid={`suggestion-${suggestion.replace(/ /g, '-')}`}
                className="px-3 py-1 bg-surface border border-border rounded-sm text-sm text-text-muted hover:border-error hover:text-error transition-colors"
              >
                {suggestion}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="flex flex-col items-center justify-center py-16" data-testid="loading-state">
          <Loader2 className="w-12 h-12 text-error animate-spin mb-4" />
          <p className="text-text-muted">Generating incident report...</p>
        </div>
      )}
    </div>
  );
}
