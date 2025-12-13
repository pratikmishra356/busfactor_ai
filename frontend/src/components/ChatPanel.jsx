import React, { useState, useRef, useEffect } from 'react';
import { Send, Loader2, Trash2, Bot, User } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import CodeHealthForm from './agents/CodeHealthForm';
import EmployeeForm from './agents/EmployeeForm';

export default function ChatPanel({ agent, messages, addMessage, addCompletedTask, clearChat }) {
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleAgentResponse = (userInput, response, taskType) => {
    // Add user message
    addMessage({
      id: Date.now(),
      type: 'user',
      content: userInput,
      timestamp: new Date().toISOString()
    });

    // Add agent response
    addMessage({
      id: Date.now() + 1,
      type: 'agent',
      agent: agent.id,
      content: response,
      timestamp: new Date().toISOString()
    });

    // Add to completed tasks
    addCompletedTask({
      id: Date.now(),
      agent: agent.id,
      type: taskType,
      title: typeof userInput === 'string' ? userInput.slice(0, 50) : `${agent.name} Task`,
      timestamp: new Date().toISOString()
    });
  };

  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      {/* Chat Header */}
      <div className="h-12 border-b border-slate-100 flex items-center justify-between px-4 bg-white">
        <div className="flex items-center gap-2">
          <agent.icon className={`w-5 h-5 ${agent.color}`} />
          <span className="font-heading font-semibold text-slate-900">{agent.name} Agent</span>
          {!agent.enabled && (
            <span className="text-xs bg-amber-100 text-amber-700 px-2 py-0.5 rounded-full">Coming Soon</span>
          )}
        </div>
        {messages.length > 0 && (
          <button
            onClick={clearChat}
            data-testid="clear-chat-btn"
            className="text-slate-400 hover:text-slate-600 p-1.5 rounded-md hover:bg-slate-100 transition-colors"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-slate-50/30" data-testid="chat-messages">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center">
            <div className={`w-16 h-16 rounded-2xl bg-slate-100 flex items-center justify-center mb-4`}>
              <agent.icon className={`w-8 h-8 ${agent.color}`} />
            </div>
            <h3 className="font-heading font-semibold text-slate-900 mb-1">
              {agent.name} Agent
            </h3>
            <p className="text-sm text-slate-500 max-w-md">
              {agent.id === 'codehealth' && 'Analyze PRs and generate review checklists based on your codebase history.'}
              {agent.id === 'employee' && 'Get role-based assistance for engineers and managers.'}
              {agent.id === 'oncall' && 'Incident response assistance coming soon.'}
              {agent.id === 'document' && 'Documentation intelligence coming soon.'}
            </p>
          </div>
        ) : (
          <>
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex ${msg.type === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                {msg.type === 'agent' && (
                  <div className={`w-7 h-7 rounded-full bg-slate-100 flex items-center justify-center mr-2 flex-shrink-0`}>
                    <Bot className="w-4 h-4 text-slate-600" />
                  </div>
                )}
                <div className={msg.type === 'user' ? 'chat-bubble-user' : 'chat-bubble-agent'}>
                  {typeof msg.content === 'string' ? (
                    <div className="markdown-content">
                      <ReactMarkdown>{msg.content}</ReactMarkdown>
                    </div>
                  ) : (
                    msg.content
                  )}
                </div>
                {msg.type === 'user' && (
                  <div className="w-7 h-7 rounded-full bg-blue-600 flex items-center justify-center ml-2 flex-shrink-0">
                    <User className="w-4 h-4 text-white" />
                  </div>
                )}
              </div>
            ))}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Input Area */}
      <div className="border-t border-slate-200 p-4 bg-white">
        {agent.id === 'codehealth' && (
          <CodeHealthForm 
            onResponse={handleAgentResponse}
            isLoading={isLoading}
            setIsLoading={setIsLoading}
          />
        )}
        {agent.id === 'employee' && (
          <EmployeeForm
            onResponse={handleAgentResponse}
            isLoading={isLoading}
            setIsLoading={setIsLoading}
          />
        )}
        {(agent.id === 'oncall' || agent.id === 'document') && (
          <div className="flex items-center justify-center py-4 text-slate-400 text-sm">
            This agent is coming soon
          </div>
        )}
      </div>
    </div>
  );
}
