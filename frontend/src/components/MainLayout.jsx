import React, { useState } from 'react';
import { Code2, Users, Bell, FileText } from 'lucide-react';
import Header from './Header';
import AgentTabs from './AgentTabs';
import ChatPanel from './ChatPanel';
import CompletedTasks from './CompletedTasks';

const AGENTS = [
  { id: 'codehealth', name: 'CodeHealth', icon: Code2, color: 'accent-codehealth', enabled: true },
  { id: 'employee', name: 'Employee', icon: Users, color: 'accent-employee', enabled: true },
  { id: 'oncall', name: 'OnCall', icon: Bell, color: 'accent-oncall', enabled: true },
  { id: 'document', name: 'Document', icon: FileText, color: 'accent-document', enabled: true },
];

export default function MainLayout() {
  const [activeAgent, setActiveAgent] = useState('codehealth');
  const [completedTasks, setCompletedTasks] = useState([]);
  const [chatMessages, setChatMessages] = useState([]);
  const [activeTaskId, setActiveTaskId] = useState(null);

  const addCompletedTask = (task) => {
    setCompletedTasks(prev => [task, ...prev].slice(0, 10));
  };

  const addChatMessage = (message) => {
    setChatMessages(prev => [...prev, message]);
  };

  const clearChat = () => {
    setChatMessages([]);
  };

  const handleAgentChange = (agentId) => {
    setActiveAgent(agentId);
    // Clear chat when switching agents
    setChatMessages([]);
    setActiveTaskId(null);
  };

  const handleTaskClick = (task) => {
    // If clicking the same task, do nothing
    if (activeTaskId === task.id) return;
    
    // Switch to the task's agent if different
    if (activeAgent !== task.agent) {
      setActiveAgent(task.agent);
    }
    
    // Load the task's conversation
    setActiveTaskId(task.id);
    setChatMessages(task.messages || []);
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
        onAgentChange={handleAgentChange} 
      />

      {/* Main Content - Full Height */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <ChatPanel 
          agent={currentAgent}
          messages={chatMessages}
          addMessage={addChatMessage}
          addCompletedTask={addCompletedTask}
          clearChat={clearChat}
          activeTaskId={activeTaskId}
        />
        
        {/* Completed Tasks */}
        <CompletedTasks 
          tasks={completedTasks} 
          activeTaskId={activeTaskId}
          onTaskClick={handleTaskClick}
        />
      </div>
    </div>
  );
}
