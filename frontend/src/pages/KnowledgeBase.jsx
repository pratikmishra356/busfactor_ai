import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { Database, Loader2, FileText, Calendar, Users, ChevronDown, ChevronUp } from 'lucide-react';
import SearchInput from '../components/SearchInput';
import { SourceBadgeList, EntityCard } from '../components/EntityComponents';
import { getContext } from '../services/api';

export default function KnowledgeBase() {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [expandedSummaries, setExpandedSummaries] = useState({});

  const handleSearch = async (searchQuery) => {
    setLoading(true);
    setError(null);
    
    try {
      const data = await getContext(searchQuery, 3);
      setResult(data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to fetch context. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const toggleSummary = (weekKey) => {
    setExpandedSummaries(prev => ({
      ...prev,
      [weekKey]: !prev[weekKey]
    }));
  };

  return (
    <div className="p-8 max-w-6xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-12 h-12 bg-primary/20 rounded-sm flex items-center justify-center">
            <Database className="w-6 h-6 text-primary" />
          </div>
          <div>
            <h1 className="font-heading font-bold text-3xl tracking-tight">Knowledge Base</h1>
            <p className="text-text-muted">Search organizational context across all sources</p>
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
          placeholder="Ask anything... e.g., 'payment gateway issues' or 'database performance'"
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
        <div className="space-y-6" data-testid="knowledge-results">
          {/* Context Header */}
          <div className="bg-surface border border-border rounded-sm p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-heading font-bold text-xl text-white">Context Results</h2>
              <div className="flex items-center gap-4 text-sm text-text-muted">
                <span className="flex items-center gap-1">
                  <FileText className="w-4 h-4" />
                  {result.entity_count} entities
                </span>
                <span className="flex items-center gap-1">
                  <Calendar className="w-4 h-4" />
                  {result.weeks_covered?.length || 0} weeks
                </span>
              </div>
            </div>
            
            {/* Sources */}
            <div className="mb-4">
              <p className="text-xs uppercase tracking-widest text-text-muted mb-2">Sources Used</p>
              <SourceBadgeList sources={result.sources_used} />
            </div>
          </div>

          {/* Main Context */}
          <div className="bg-surface border border-border rounded-sm p-6">
            <h3 className="font-heading font-bold text-lg mb-4 text-primary">AI-Generated Context</h3>
            <div className="markdown-content text-text-muted leading-relaxed">
              <ReactMarkdown>{result.context}</ReactMarkdown>
            </div>
          </div>

          {/* Weeks Covered */}
          {result.weeks_covered && result.weeks_covered.length > 0 && (
            <div className="bg-surface border border-border rounded-sm p-6">
              <h3 className="font-heading font-bold text-lg mb-4 text-white">Weeks Analyzed</h3>
              <div className="flex flex-wrap gap-2">
                {result.weeks_covered.map((week, idx) => (
                  <span 
                    key={idx} 
                    className="px-3 py-1 bg-primary/20 text-primary rounded-sm text-sm font-medium"
                  >
                    {week}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Empty State */}
      {!loading && !result && !error && (
        <div className="text-center py-16">
          <Database className="w-16 h-16 text-border mx-auto mb-4" />
          <h3 className="font-heading text-xl text-text-muted mb-2">Search the Knowledge Base</h3>
          <p className="text-text-muted text-sm max-w-md mx-auto">
            Enter a natural language query to search across Slack, Jira, GitHub, Docs, and Meetings.
          </p>
          <div className="mt-6 flex flex-wrap justify-center gap-2">
            {['payment issues', 'database performance', 'security vulnerabilities', 'API refactoring'].map((suggestion) => (
              <button
                key={suggestion}
                onClick={() => {
                  setQuery(suggestion);
                  handleSearch(suggestion);
                }}
                data-testid={`suggestion-${suggestion.replace(' ', '-')}`}
                className="px-3 py-1 bg-surface border border-border rounded-sm text-sm text-text-muted hover:border-primary hover:text-primary transition-colors"
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
          <Loader2 className="w-12 h-12 text-primary animate-spin mb-4" />
          <p className="text-text-muted">Generating context...</p>
        </div>
      )}
    </div>
  );
}
