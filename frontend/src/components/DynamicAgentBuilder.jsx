import React, { useState, useEffect } from 'react';
import { Bot, Plus, Sparkles, MessageSquare, AlertCircle, CheckCircle, Loader2, Trash2 } from 'lucide-react';
import { createDynamicAgent, listDynamicAgents, executeDynamicAgent } from '../services/api';

export default function DynamicAgentBuilder() {
  const [agents, setAgents] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  
  // Create Agent Form State
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newAgent, setNewAgent] = useState({
    name: '',
    role: '',
    prompt: ''
  });
  
  // Chat State
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [chatMessages, setChatMessages] = useState([]);
  const [currentQuery, setCurrentQuery] = useState('');
  const [executing, setExecuting] = useState(false);

  useEffect(() => {
    loadAgents();
  }, []);

  const loadAgents = async () => {
    try {
      setLoading(true);
      const data = await listDynamicAgents();
      setAgents(data);
    } catch (err) {
      setError('Failed to load agents');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateAgent = async (e) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    
    try {
      setLoading(true);
      await createDynamicAgent(newAgent);
      setSuccess(`Agent "${newAgent.name}" created successfully!`);
      setNewAgent({ name: '', role: '', prompt: '' });
      setShowCreateForm(false);
      await loadAgents();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create agent');
    } finally {
      setLoading(false);
    }
  };

  const handleExecuteAgent = async (e) => {
    e.preventDefault();
    if (!currentQuery.trim() || !selectedAgent) return;
    
    const userMessage = { type: 'user', content: currentQuery };
    setChatMessages(prev => [...prev, userMessage]);
    setCurrentQuery('');
    setExecuting(true);
    
    try {
      const response = await executeDynamicAgent(selectedAgent.name, userMessage.content);
      const agentMessage = {
        type: 'agent',
        content: response.response,
        contextFetched: response.context_fetched,
        executionTime: response.execution_time
      };
      setChatMessages(prev => [...prev, agentMessage]);
    } catch (err) {
      const errorMessage = {
        type: 'error',
        content: err.response?.data?.detail || 'Failed to execute agent'
      };
      setChatMessages(prev => [...prev, errorMessage]);
    } finally {
      setExecuting(false);
    }
  };

  const handleSelectAgent = (agent) => {
    setSelectedAgent(agent);
    setChatMessages([]);
  };

  return (
    <div className="h-screen w-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 flex flex-col overflow-hidden">
      {/* Header */}
      <div className="bg-white border-b border-slate-200 px-6 py-4 shadow-sm">
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center shadow-lg">
                <Bot className="w-5 h-5 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-slate-900">Dynamic Agent Builder</h1>
                <p className="text-sm text-slate-600">Build and deploy your agent on top of your knowledge base</p>
              </div>
            </div>
          </div>
          <button
            onClick={() => setShowCreateForm(!showCreateForm)}
            className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-lg hover:from-blue-600 hover:to-purple-700 transition-all shadow-md hover:shadow-lg"
          >
            <Plus className="w-4 h-4" />
            Create Agent
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Sidebar - Agent List */}
        <div className="w-80 bg-white border-r border-slate-200 flex flex-col">
          <div className="p-4 border-b border-slate-200">
            <h2 className="text-lg font-semibold text-slate-900 flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-purple-500" />
              Your Agents ({agents.length})
            </h2>
          </div>
          
          <div className="flex-1 overflow-y-auto">
            {loading && agents.length === 0 ? (
              <div className="flex items-center justify-center h-32">
                <Loader2 className="w-6 h-6 animate-spin text-blue-500" />
              </div>
            ) : agents.length === 0 ? (
              <div className="p-6 text-center text-slate-500">
                <Bot className="w-12 h-12 mx-auto mb-3 text-slate-300" />
                <p className="text-sm">No agents yet.</p>
                <p className="text-xs mt-1">Create your first agent to get started!</p>
              </div>
            ) : (
              <div className="p-3 space-y-2">
                {agents.map((agent) => (
                  <button
                    key={agent.name}
                    onClick={() => handleSelectAgent(agent)}
                    className={`w-full text-left p-3 rounded-lg border transition-all ${
                      selectedAgent?.name === agent.name
                        ? 'bg-gradient-to-r from-blue-50 to-purple-50 border-blue-300 shadow-sm'
                        : 'bg-white border-slate-200 hover:border-blue-200 hover:bg-slate-50'
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                        selectedAgent?.name === agent.name
                          ? 'bg-gradient-to-br from-blue-500 to-purple-600'
                          : 'bg-slate-100'
                      }`}>
                        <Bot className={`w-5 h-5 ${
                          selectedAgent?.name === agent.name ? 'text-white' : 'text-slate-600'
                        }`} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <h3 className="font-semibold text-slate-900 truncate">{agent.name}</h3>
                        <p className="text-xs text-slate-600 truncate">{agent.role}</p>
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Right Content Area */}
        <div className="flex-1 flex flex-col bg-slate-50">
          {/* Create Agent Form */}
          {showCreateForm && (
            <div className="bg-white border-b border-slate-200 p-6 shadow-sm">
              <form onSubmit={handleCreateAgent} className="space-y-4">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-slate-900">Create New Agent</h3>
                  <button
                    type="button"
                    onClick={() => setShowCreateForm(false)}
                    className="text-slate-400 hover:text-slate-600"
                  >
                    ✕
                  </button>
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">Agent Name*</label>
                    <input
                      type="text"
                      value={newAgent.name}
                      onChange={(e) => setNewAgent({ ...newAgent, name: e.target.value })}
                      placeholder="e.g., payment-specialist"
                      required
                      className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-slate-900"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">Role*</label>
                    <input
                      type="text"
                      value={newAgent.role}
                      onChange={(e) => setNewAgent({ ...newAgent, role: e.target.value })}
                      placeholder="e.g., Payment Systems Expert"
                      required
                      className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-slate-900"
                    />
                  </div>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">System Prompt*</label>
                  <textarea
                    value={newAgent.prompt}
                    onChange={(e) => setNewAgent({ ...newAgent, prompt: e.target.value })}
                    placeholder="You are an expert in... Provide specific guidance based on the organizational context from PRs, docs, and incidents."
                    required
                    rows={3}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-slate-900"
                  />
                </div>
                
                <button
                  type="submit"
                  disabled={loading}
                  className="px-4 py-2 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-lg hover:from-blue-600 hover:to-purple-700 transition-all shadow-md disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                >
                  {loading ? (
                    <><Loader2 className="w-4 h-4 animate-spin" /> Creating...</>
                  ) : (
                    <><Plus className="w-4 h-4" /> Create Agent</>
                  )}
                </button>
              </form>
            </div>
          )}

          {/* Alerts */}
          {(error || success) && (
            <div className="mx-6 mt-4">
              {error && (
                <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700">
                  <AlertCircle className="w-5 h-5" />
                  <span className="text-sm">{error}</span>
                  <button onClick={() => setError(null)} className="ml-auto text-red-400 hover:text-red-600">✕</button>
                </div>
              )}
              {success && (
                <div className="flex items-center gap-2 p-3 bg-green-50 border border-green-200 rounded-lg text-green-700">
                  <CheckCircle className="w-5 h-5" />
                  <span className="text-sm">{success}</span>
                  <button onClick={() => setSuccess(null)} className="ml-auto text-green-400 hover:text-green-600">✕</button>
                </div>
              )}
            </div>
          )}

          {/* Chat Area */}
          {selectedAgent ? (
            <div className="flex-1 flex flex-col m-6 bg-white rounded-xl shadow-lg overflow-hidden border border-slate-200">
              {/* Chat Header */}
              <div className="bg-gradient-to-r from-blue-500 to-purple-600 text-white p-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-white/20 backdrop-blur flex items-center justify-center">
                    <Bot className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="font-semibold">{selectedAgent.name}</h3>
                    <p className="text-xs text-blue-100">{selectedAgent.role}</p>
                  </div>
                </div>
              </div>

              {/* Messages */}
              <div className="flex-1 overflow-y-auto p-6 space-y-4">
                {chatMessages.length === 0 ? (
                  <div className="flex flex-col items-center justify-center h-full text-slate-400">
                    <MessageSquare className="w-16 h-16 mb-4" />
                    <p className="text-lg font-medium">Start a conversation</p>
                    <p className="text-sm">Ask anything about your organization's knowledge base</p>
                  </div>
                ) : (
                  chatMessages.map((msg, idx) => (
                    <div key={idx} className={`flex ${msg.type === 'user' ? 'justify-end' : 'justify-start'}`}>
                      <div className={`max-w-3xl rounded-lg px-4 py-3 ${
                        msg.type === 'user' 
                          ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white'
                          : msg.type === 'error'
                          ? 'bg-red-50 text-red-700 border border-red-200'
                          : 'bg-slate-100 text-slate-900'
                      }`}>
                        {msg.type === 'agent' && (
                          <div className="flex items-center gap-2 text-xs text-slate-500 mb-2">
                            <Bot className="w-4 h-4" />
                            <span>Context: {msg.contextFetched} items • {msg.executionTime?.toFixed(1)}s</span>
                          </div>
                        )}
                        <div className="whitespace-pre-wrap">{msg.content}</div>
                      </div>
                    </div>
                  ))
                )}
                {executing && (
                  <div className="flex justify-start">
                    <div className="bg-slate-100 rounded-lg px-4 py-3 flex items-center gap-2">
                      <Loader2 className="w-4 h-4 animate-spin text-blue-500" />
                      <span className="text-slate-600">Agent is thinking...</span>
                    </div>
                  </div>
                )}
              </div>

              {/* Input */}
              <form onSubmit={handleExecuteAgent} className="border-t border-slate-200 p-4 bg-slate-50">
                <div className="flex gap-3">
                  <input
                    type="text"
                    value={currentQuery}
                    onChange={(e) => setCurrentQuery(e.target.value)}
                    placeholder="Ask me anything about your knowledge base..."
                    disabled={executing}
                    className="flex-1 px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:opacity-50 text-slate-900"
                  />
                  <button
                    type="submit"
                    disabled={executing || !currentQuery.trim()}
                    className="px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-lg hover:from-blue-600 hover:to-purple-700 transition-all shadow-md disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {executing ? <Loader2 className="w-5 h-5 animate-spin" /> : 'Send'}
                  </button>
                </div>
              </form>
            </div>
          ) : (
            <div className="flex-1 flex items-center justify-center text-slate-400">
              <div className="text-center">
                <Bot className="w-20 h-20 mx-auto mb-4 text-slate-300" />
                <p className="text-lg font-medium">Select an agent to start</p>
                <p className="text-sm mt-1">Choose from your agents or create a new one</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
