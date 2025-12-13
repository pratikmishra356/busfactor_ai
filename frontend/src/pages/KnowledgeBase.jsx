import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { Search, Loader2, BookOpen, Calendar, ChevronDown, ChevronUp } from 'lucide-react';
import SearchInput from '../components/SearchInput';
import { SourceBadge, SummaryCard, WeekBadge } from '../components/EntityComponents';
import { getContextResponse } from '../services/api';

export default function KnowledgeBase() {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [expandedSummary, setExpandedSummary] = useState(null);

  const handleSearch = async (searchQuery) => {
    setLoading(true);
    setError(null);
    
    try {
      const data = await getContextResponse(searchQuery, 3);
      setResult(data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to fetch context. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-8 max-w-5xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-12 h-12 bg-info/20 rounded-sm flex items-center justify-center">
            <BookOpen className="w-6 h-6 text-info" />
          </div>
          <div>
            <h1 className="font-heading font-bold text-3xl tracking-tight">Knowledge Base</h1>
            <p className="text-text-muted">Search and explore organizational context</p>
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
          placeholder="What would you like to know? e.g., 'payment gateway issues'"
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
        <div className="space-y-6" data-testid="search-results">
          {/* Meta Info */}
          <div className="flex flex-wrap items-center gap-4 pb-4 border-b border-border">
            <div className="flex items-center gap-2">
              <Calendar className="w-4 h-4 text-text-muted" />
              <span className="text-sm text-text-muted">Weeks covered:</span>
              {result.weeks_covered?.map((week) => (
                <WeekBadge key={week} week={week} />
              ))}
            </div>
            <div className="flex items-center gap-2">
              <span className="text-sm text-text-muted">Sources:</span>
              {result.sources_used?.map((source) => (
                <SourceBadge key={source} source={source} />
              ))}
            </div>
            <div className="text-sm text-text-muted">
              <span className="text-primary font-bold">{result.entity_count}</span> entities analyzed
            </div>
          </div>

          {/* Context Response */}
          <div className="bg-surface border border-border rounded-sm p-6" data-testid="context-response">
            <h3 className="font-heading font-bold text-lg mb-4 text-white flex items-center gap-2">
              <Search className="w-5 h-5 text-primary" />
              Context for "{result.query}"
            </h3>
            <div className="markdown-content text-text-muted leading-relaxed">
              <ReactMarkdown>{result.context}</ReactMarkdown>
            </div>
          </div>
        </div>
      )}

      {/* Empty State */}
      {!loading && !result && !error && (
        <div className="text-center py-16">
          <BookOpen className="w-16 h-16 text-border mx-auto mb-4" />
          <h3 className="font-heading text-xl text-text-muted mb-2">Search Your Knowledge</h3>
          <p className="text-text-muted text-sm max-w-md mx-auto">
            Ask any question about your organization. We'll search across Slack, Jira, GitHub, Docs, and Meetings to give you comprehensive context.
          </p>
          <div className="mt-6 flex flex-wrap justify-center gap-2">
            {['payment gateway', 'database performance', 'security vulnerability', 'email notifications'].map((suggestion) => (
              <button
                key={suggestion}
                onClick={() => {
                  setQuery(suggestion);
                  handleSearch(suggestion);
                }}
                data-testid={`suggestion-${suggestion.replace(/ /g, '-')}`}
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
          <p className="text-text-muted">Searching knowledge base...</p>
        </div>
      )}
    </div>
  );
}
