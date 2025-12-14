import React, { useState } from 'react';
import { Send, Loader2, Plus, X, FileCode } from 'lucide-react';
import { runCodeHealthAgent } from '../../services/api';

export default function CodeHealthForm({ onResponse, isLoading, setIsLoading }) {
  const [prNumber, setPrNumber] = useState('');
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [author, setAuthor] = useState('');
  const [files, setFiles] = useState([]);
  const [newFile, setNewFile] = useState('');
  const [labels, setLabels] = useState('');
  const [jiraRef, setJiraRef] = useState('');
  const [showAdvanced, setShowAdvanced] = useState(false);

  const addFile = () => {
    if (newFile.trim() && !files.includes(newFile.trim())) {
      setFiles([...files, newFile.trim()]);
      setNewFile('');
    }
  };

  const removeFile = (file) => {
    setFiles(files.filter(f => f !== file));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!title.trim()) return;

    setIsLoading(true);
    
    const prInput = {
      pr_number: parseInt(prNumber) || Math.floor(Math.random() * 1000),
      title: title.trim(),
      description: description.trim(),
      author: author.trim() || 'Developer',
      author_github: '',
      files_changed: files,
      labels: labels.split(',').map(l => l.trim()).filter(Boolean),
      lines_added: 100,
      lines_removed: 20,
      jira_ref: jiraRef.trim(),
      comments: []
    };

    try {
      const result = await runCodeHealthAgent(prInput);
      
      // Format response
      const formattedResponse = formatCodeHealthResponse(result);
      onResponse(`PR: ${title}`, formattedResponse, 'codehealth');
      
      // Reset form
      setPrNumber('');
      setTitle('');
      setDescription('');
      setFiles([]);
      setLabels('');
      setJiraRef('');
    } catch (error) {
      onResponse(`PR: ${title}`, `Error: ${error.message || 'Failed to analyze PR'}`, 'codehealth');
    } finally {
      setIsLoading(false);
    }
  };

  const formatCodeHealthResponse = (result) => {
    let response = `## PR Analysis: ${result.pr_title}\n\n`;
    response += `**Risk Level:** ${result.risk_level.toUpperCase()}\n\n`;
    response += `**Summary:** ${result.summary}\n\n`;

    if (result.checklist?.length > 0) {
      response += `### Review Checklist\n`;
      result.checklist.forEach(item => {
        const priority = item.priority === 'high' ? '🔴' : item.priority === 'medium' ? '🟡' : '🟢';
        response += `- ${priority} **[${item.category}]** ${item.item}\n`;
      });
    }

    return response;
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-3" data-testid="codehealth-form">
      {/* Main Input Row */}
      <div className="flex gap-2">
        <input
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="PR Title (e.g., feat: add payment retry mechanism)"
          disabled={isLoading}
          data-testid="pr-title-input"
          className="w-[70%] h-11 px-4 rounded-xl border border-slate-200 bg-slate-50 focus:bg-white focus:border-blue-400 focus:ring-2 focus:ring-blue-100 outline-none transition-all text-sm"
        />
        <button
          type="submit"
          disabled={isLoading || !title.trim()}
          data-testid="submit-codehealth-btn"
          className="h-11 px-5 bg-blue-600 text-white rounded-xl font-medium text-sm hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
        >
          {isLoading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Analyzing...</span>
            </>
          ) : (
            <>
              <Send className="w-4 h-4" />
              <span>Analyze</span>
            </>
          )}
        </button>
      </div>

      {/* Toggle Advanced */}
      <button
        type="button"
        onClick={() => setShowAdvanced(!showAdvanced)}
        className="text-xs text-blue-600 hover:text-blue-700 font-medium"
      >
        {showAdvanced ? 'Hide' : 'Show'} advanced options
      </button>

      {/* Advanced Options */}
      {showAdvanced && (
        <div className="space-y-3 p-4 bg-slate-50 rounded-xl border border-slate-200">
          <div className="grid grid-cols-3 gap-3">
            <input
              type="number"
              value={prNumber}
              onChange={(e) => setPrNumber(e.target.value)}
              placeholder="PR #"
              className="h-9 px-3 rounded-lg border border-slate-200 text-sm"
            />
            <input
              type="text"
              value={author}
              onChange={(e) => setAuthor(e.target.value)}
              placeholder="Author"
              className="h-9 px-3 rounded-lg border border-slate-200 text-sm"
            />
            <input
              type="text"
              value={jiraRef}
              onChange={(e) => setJiraRef(e.target.value)}
              placeholder="Jira (e.g., ENG-123)"
              className="h-9 px-3 rounded-lg border border-slate-200 text-sm"
            />
          </div>

          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="PR Description..."
            rows={2}
            className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm resize-none"
          />

          {/* Files Changed */}
          <div>
            <label className="text-xs text-slate-500 font-medium mb-1 block">Files Changed</label>
            <div className="flex gap-2 mb-2">
              <input
                type="text"
                value={newFile}
                onChange={(e) => setNewFile(e.target.value)}
                placeholder="src/path/to/file.py"
                onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addFile())}
                className="flex-1 h-8 px-3 rounded-lg border border-slate-200 text-sm"
              />
              <button
                type="button"
                onClick={addFile}
                className="h-8 px-3 bg-slate-200 rounded-lg hover:bg-slate-300 transition-colors"
              >
                <Plus className="w-4 h-4" />
              </button>
            </div>
            {files.length > 0 && (
              <div className="flex flex-wrap gap-1">
                {files.map((file) => (
                  <span key={file} className="inline-flex items-center gap-1 px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs">
                    <FileCode className="w-3 h-3" />
                    {file}
                    <button type="button" onClick={() => removeFile(file)} className="hover:text-blue-900">
                      <X className="w-3 h-3" />
                    </button>
                  </span>
                ))}
              </div>
            )}
          </div>

          <input
            type="text"
            value={labels}
            onChange={(e) => setLabels(e.target.value)}
            placeholder="Labels (comma-separated, e.g., feature, payment)"
            className="w-full h-9 px-3 rounded-lg border border-slate-200 text-sm"
          />
        </div>
      )}
    </form>
  );
}
