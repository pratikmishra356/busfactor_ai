import React, { useState } from 'react';
import { Code2, Users, Bell, FileText, Zap } from 'lucide-react';
import Header from './Header';
import AgentTabs from './AgentTabs';
import ChatPanel from './ChatPanel';
import BuilderPanel from './BuilderPanel';
import CompletedTasks from './CompletedTasks';

const AGENTS = [
  { id: 'codehealth', name: 'CodeHealth', icon: Code2, color: 'accent-codehealth', enabled: true },
  { id: 'employee', name: 'Employee', icon: Users, color: 'accent-employee', enabled: true },
  { id: 'oncall', name: 'OnCall', icon: Bell, color: 'accent-oncall', enabled: false },
  { id: 'document', name: 'Document', icon: FileText, color: 'accent-document', enabled: false },
];

export default function MainLayout() {
  const [activeAgent, setActiveAgent] = useState('codehealth');
  const [completedTasks, setCompletedTasks] = useState([]);
  const [chatMessages, setChatMessages] = useState([]);

  const addCompletedTask = (task) => {
    setCompletedTasks(prev => [task, ...prev].slice(0, 10));
  };

  const addChatMessage = (message) => {
    setChatMessages(prev => [...prev, message]);
  };

  const clearChat = () => {
    setChatMessages([]);
  };

  const currentAgent = AGENTS.find(a => a.id === activeAgent);

  return (
    <div className="h-screen w-screen overflow-hidden bg-white flex flex-col">
      {/* Header */}
      <Header />

      {/* Agent Tabs */}
      <AgentTabs 
        agents={AGENTS} 
        activeAgent={activeAgent} 
        onAgentChange={setActiveAgent} 
      />

      {/* Main Content - Split Screen */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top Panel - Chat + Tasks */}
        <div className="h-[55%] flex flex-col border-b border-slate-200 bg-white">
          <ChatPanel 
            agent={currentAgent}
            messages={chatMessages}
            addMessage={addChatMessage}
            addCompletedTask={addCompletedTask}
            clearChat={clearChat}
          />
          
          {/* Completed Tasks */}
          <CompletedTasks tasks={completedTasks} />
        </div>

        {/* Resizer */}
        <div className="h-1 bg-slate-100 hover:bg-blue-200 cursor-row-resize transition-colors flex items-center justify-center">
          <div className="w-12 h-1 bg-slate-300 rounded-full" />
        </div>

        {/* Bottom Panel - Builder */}
        <div className="flex-1 bg-slate-50 builder-grid overflow-hidden">
          <BuilderPanel agent={currentAgent} />
        </div>
      </div>
    </div>
  );
}
