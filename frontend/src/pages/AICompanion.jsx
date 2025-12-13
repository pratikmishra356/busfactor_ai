import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { Bot, User, Settings, Loader2, Briefcase, Code, Users, ChevronDown, CheckCircle, AlertCircle } from 'lucide-react';
import SearchInput from '../components/SearchInput';
import { SourceBadge } from '../components/EntityComponents';
import { getRoleTask } from '../services/api';

const ROLES = [
  { 
    id: 'engineer', 
    label: 'Engineer', 
    icon: Code,
    description: 'Technical details, PRs, debugging',
    color: 'text-info'
  },
  { 
    id: 'product_manager', 
    label: 'Product Manager', 
    icon: Briefcase,
    description: 'Feature progress, customer impact',
    color: 'text-success'
  },
  { 
    id: 'engineering_manager', 
    label: 'Engineering Manager', 
    icon: Users,
    description: 'Team health, incidents, process',
    color: 'text-primary'
  },
];

export default function AICompanion() {
  const [query, setQuery] = useState('');
  const [selectedRole, setSelectedRole] = useState('engineer');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [showRoleDropdown, setShowRoleDropdown] = useState(false);

  const handleSearch = async (searchQuery) => {
    setLoading(true);
    setError(null);
    
    try {
      const data = await getRoleTask(selectedRole, searchQuery);
      setResult(data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to generate response. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const currentRole = ROLES.find(r => r.id === selectedRole);

  return (
    <div className="p-8 max-w-5xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-12 h-12 bg-primary/20 rounded-sm flex items-center justify-center">
            <Bot className="w-6 h-6 text-primary" />
          </div>
          <div>
            <h1 className="font-heading font-bold text-3xl tracking-tight">AI Companion</h1>
            <p className="text-text-muted">Your role-based intelligent assistant</p>
          </div>
        </div>
      </div>

      {/* Role Selector */}
      <div className="mb-6">
        <label className="text-xs uppercase tracking-widest text-text-muted mb-2 block">Select Your Role</label>
        <div className="relative">
          <button
            onClick={() => setShowRoleDropdown(!showRoleDropdown)}
            data-testid="role-selector"
            className="w-full md:w-80 flex items-center justify-between gap-3 p-4 bg-surface border border-border rounded-sm hover:border-primary transition-colors"
          >
            <div className="flex items-center gap-3">
              {currentRole && (
                <>
                  <currentRole.icon className={`w-5 h-5 ${currentRole.color}`} />
                  <div className="text-left">
                    <p className="font-medium text-white">{currentRole.label}</p>
                    <p className="text-xs text-text-muted">{currentRole.description}</p>
                  </div>
                </>
              )}
            </div>
            <ChevronDown className={`w-5 h-5 text-text-muted transition-transform ${showRoleDropdown ? 'rotate-180' : ''}`} />
          </button>
          
          {showRoleDropdown && (
            <div className="absolute top-full left-0 w-full md:w-80 mt-1 bg-surface border border-border rounded-sm z-10 shadow-lg">
              {ROLES.map((role) => (
                <button
                  key={role.id}
                  onClick={() => {
                    setSelectedRole(role.id);
                    setShowRoleDropdown(false);
                  }}
                  data-testid={`role-option-${role.id}`}
                  className={`w-full flex items-center gap-3 p-4 hover:bg-border/30 transition-colors ${selectedRole === role.id ? 'bg-primary/10' : ''}`}
                >
                  <role.icon className={`w-5 h-5 ${role.color}`} />
                  <div className="text-left">
                    <p className="font-medium text-white">{role.label}</p>
                    <p className="text-xs text-text-muted">{role.description}</p>
                  </div>
                  {selectedRole === role.id && (
                    <CheckCircle className="w-4 h-4 text-primary ml-auto" />
                  )}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Search */}
      <div className="mb-8">
        <SearchInput
          value={query}
          onChange={setQuery}
          onSubmit={handleSearch}
          loading={loading}
          placeholder={`Ask as ${currentRole?.label}... e.g., 'database performance issues'`}
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
        <div className="space-y-6" data-testid="ai-results">
          {/* Response Header */}
          <div className="flex items-center gap-3 pb-4 border-b border-border">
            <div className={`w-10 h-10 rounded-sm flex items-center justify-center bg-primary/20`}>
              <Bot className="w-5 h-5 text-primary" />
            </div>
            <div>
              <p className="font-heading font-bold text-white">AI Response</p>
              <p className="text-xs text-text-muted">Tailored for {currentRole?.label}</p>
            </div>
          </div>

          {/* Main Response */}
          <div className="bg-surface border border-border rounded-sm p-6" data-testid="ai-response">
            <div className="markdown-content text-text-muted leading-relaxed">
              <ReactMarkdown>{result.response}</ReactMarkdown>
            </div>
          </div>

          {/* Priority Items */}
          {result.priority_items && result.priority_items.length > 0 && result.priority_items[0] !== 'No critical items identified' && (
            <div className="bg-error/5 border border-error/30 rounded-sm p-4">
              <h4 className="font-heading font-bold text-error flex items-center gap-2 mb-3">
                <AlertCircle className="w-5 h-5" />
                Priority Items
              </h4>
              <ul className="space-y-2">
                {result.priority_items.map((item, idx) => (
                  <li key={idx} className="text-sm text-text-muted flex items-start gap-2">
                    <span className="text-error">•</span>
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Relevant Entities */}
          {result.relevant_entities && result.relevant_entities.length > 0 && (
            <div className="bg-surface border border-border rounded-sm p-4">
              <h4 className="font-heading font-bold text-white mb-3">Relevant Entities</h4>
              <div className="flex flex-wrap gap-2">
                {result.relevant_entities.map((entity, idx) => (
                  <div key={idx} className="flex items-center gap-2 px-3 py-2 bg-background rounded-sm border border-border">
                    <SourceBadge source={entity.source} />
                    <span className="text-sm text-text-muted truncate max-w-[200px]">{entity.title}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Empty State */}
      {!loading && !result && !error && (
        <div className="text-center py-16">
          <Bot className="w-16 h-16 text-border mx-auto mb-4" />
          <h3 className="font-heading text-xl text-text-muted mb-2">Your AI Companion Awaits</h3>
          <p className="text-text-muted text-sm max-w-md mx-auto mb-6">
            Select your role and ask any question about your organization's context. 
            Get tailored insights based on your perspective.
          </p>
          <div className="flex flex-wrap justify-center gap-2">
            {['what happened with payments', 'team incidents this month', 'database performance', 'security updates'].map((suggestion) => (
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
          <div className="relative">
            <Loader2 className="w-12 h-12 text-primary animate-spin mb-4" />
          </div>
          <p className="text-text-muted">Thinking as {currentRole?.label}...</p>
        </div>
      )}
    </div>
  );
}
