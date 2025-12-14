import React, { useState } from 'react';
import { Send, Loader2, AlertTriangle } from 'lucide-react';
import { runOnCallAgent } from '../../services/api';

const ALERT_EXAMPLES = [
  'PaymentService timeout - 500 errors increasing',
  'Database connection pool exhausted',
  'Memory leak in authentication service',
];

export default function OnCallForm({ onResponse, isLoading, setIsLoading }) {
  const [alertText, setAlertText] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!alertText.trim()) return;

    setIsLoading(true);
    
    try {
      const result = await runOnCallAgent({
        alert_text: alertText
      });
      
      const formattedResponse = formatOnCallResponse(result);
      onResponse(alertText, formattedResponse, 'oncall');
      
      // Reset form
      setAlertText('');
    } catch (error) {
      onResponse(alertText, `Error: ${error.message || 'Failed to analyze alert'}`, 'oncall');
    } finally {
      setIsLoading(false);
    }
  };

  const formatOnCallResponse = (result) => {
    const severityEmoji = {
      critical: '🔴',
      high: '🟠',
      medium: '🟡',
      low: '🟢'
    };
    
    let response = `## ${severityEmoji[result.severity] || '🟡'} Incident Analysis - ${result.severity.toUpperCase()} Severity\n\n`;
    response += `${result.alert_summary}\n\n`;
    
    // Suspect Files - show first
    if (result.suspect_files?.length > 0) {
      response += `### 🎯 Suspect Files\n`;
      result.suspect_files.slice(0, 5).forEach(file => {
        const confidenceEmoji = file.confidence === 'high' ? '🔴' : file.confidence === 'medium' ? '🟡' : '🟢';
        response += `${confidenceEmoji} **\`${file.file_path}\`** [${file.confidence}]\n`;
        response += `${file.reason}\n`;
        if (file.related_pr) {
          response += `*From PR #${file.related_pr}: ${file.pr_title}*\n`;
        }
        response += '\n';
      });
    }
    
    // Root Cause Analysis - cleaned up
    if (result.root_cause_analysis) {
      response += `---\n\n`;
      response += `${result.root_cause_analysis}\n\n`;
    }
    
    // Related PRs - only if there are some
    if (result.related_prs?.length > 0) {
      response += `### 📋 Directly Related PRs\n`;
      result.related_prs.slice(0, 3).forEach(pr => {
        response += `- **PR #${pr.pr_number}**: ${pr.title} (by ${pr.author})\n`;
        if (pr.overlapping_files?.length > 0) {
          response += `  *Modified: ${pr.overlapping_files.slice(0, 2).join(', ')}*\n`;
        }
      });
      response += '\n';
    }
    
    // Similar Incidents
    if (result.similar_incidents?.length > 0) {
      response += `### 📚 Similar Past Incidents\n`;
      result.similar_incidents.slice(0, 2).forEach(incident => {
        response += `- ${incident}\n`;
      });
    }

    return response;
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-3 overflow-visible" data-testid="oncall-form">
      {/* Main Input Row */}
      <div className="flex gap-2 overflow-visible">
        <textarea
          value={alertText}
          onChange={(e) => setAlertText(e.target.value)}
          placeholder="Paste alert/incident details here... (e.g., error messages, stack traces, metrics)"
          disabled={isLoading}
          data-testid="alert-input"
          rows={2}
          className="w-[70%] px-4 py-3 rounded-xl border border-slate-200 bg-slate-50 focus:bg-white focus:border-red-400 focus:ring-2 focus:ring-red-100 outline-none transition-all text-sm resize-none"
        />
        
        <button
          type="submit"
          disabled={isLoading || !alertText.trim()}
          data-testid="submit-oncall-btn"
          className="h-11 px-5 bg-red-600 text-white rounded-xl font-medium text-sm hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2 self-start"
        >
          {isLoading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Analyzing...</span>
            </>
          ) : (
            <>
              <AlertTriangle className="w-4 h-4" />
              <span>Analyze</span>
            </>
          )}
        </button>
      </div>

      {/* Alert Examples */}
      <div className="flex items-center gap-2">
        <span className="text-xs text-slate-400">Try:</span>
        <div className="flex gap-2 overflow-x-auto hide-scrollbar">
          {ALERT_EXAMPLES.map((example, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => setAlertText(example)}
              disabled={isLoading}
              className="px-3 py-1.5 text-xs bg-red-50 hover:bg-red-100 text-red-600 rounded-full whitespace-nowrap transition-colors"
            >
              {example}
            </button>
          ))}
        </div>
      </div>
    </form>
  );
}
