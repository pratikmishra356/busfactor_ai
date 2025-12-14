import React, { useState } from 'react';
import { Send, Loader2, FileText } from 'lucide-react';
import { runDocumentAgent } from '../../services/api';

const DOC_EXAMPLES = [
  'Write API documentation for payment retry system',
  'Create a setup guide for new developers',
  'Document the authentication flow',
];

export default function DocumentForm({ onResponse, isLoading, setIsLoading }) {
  const [query, setQuery] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setIsLoading(true);
    
    try {
      const result = await runDocumentAgent({ query });
      
      const formattedResponse = formatDocumentResponse(result);
      onResponse(query, formattedResponse, 'document');
      
      // Reset form
      setQuery('');
    } catch (error) {
      onResponse(query, `Error: ${error.message || 'Failed to generate document'}`, 'document');
    } finally {
      setIsLoading(false);
    }
  };

  const formatDocumentResponse = (result) => {
    // Just return the clean document content
    let response = result.document_content;
    
    // Add metadata footer
    response += `\n\n---\n\n`;
    response += `*Document Type: ${result.document_type.replace('_', ' ').toUpperCase()} • `;
    response += `${result.word_count} words • ${result.sections_count} sections*`;
    
    return response;
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-3 overflow-visible" data-testid="document-form">
      {/* Main Input Row */}
      <div className="flex gap-2 overflow-visible justify-center">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="What document would you like me to write? (e.g., API docs, setup guide, runbook)"
          disabled={isLoading}
          data-testid="document-query-input"
          className="w-[70%] h-11 px-4 rounded-xl border border-slate-200 bg-slate-50 focus:bg-white focus:border-emerald-400 focus:ring-2 focus:ring-emerald-100 outline-none transition-all text-sm"
        />
        
        <button
          type="submit"
          disabled={isLoading || !query.trim()}
          data-testid="submit-document-btn"
          className="h-11 px-5 bg-emerald-600 text-white rounded-xl font-medium text-sm hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
        >
          {isLoading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Writing...</span>
            </>
          ) : (
            <>
              <FileText className="w-4 h-4" />
              <span>Generate</span>
            </>
          )}
        </button>
      </div>

      {/* Document Examples */}
      <div className="flex items-center gap-2">
        <span className="text-xs text-slate-400">Try:</span>
        <div className="flex gap-2 overflow-x-auto hide-scrollbar">
          {DOC_EXAMPLES.map((example, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => setQuery(example)}
              disabled={isLoading}
              className="px-3 py-1.5 text-xs bg-emerald-50 hover:bg-emerald-100 text-emerald-600 rounded-full whitespace-nowrap transition-colors"
            >
              {example}
            </button>
          ))}
        </div>
      </div>
    </form>
  );
}
