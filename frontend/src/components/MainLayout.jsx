import React, { useState } from 'react';
import { useAuth } from '@/context/AuthContext';
import { getMetricsKey, incrementAgentTask, readMetrics, setChatForAgent, setCompletedTasks as persistCompletedTasks } from '@/services/metrics';

import { Code2, Users, Bell, FileText } from 'lucide-react';
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
  const { user, team } = useAuth();
  const metricsKey = user && team?.team_id ? getMetricsKey({ userId: user.user_id, teamId: team.team_id }) : null;

  const [activeAgent, setActiveAgent] = useState('codehealth');
  const [completedTasks, setCompletedTasks] = useState([]);
  const [chatMessages, setChatMessages] = useState([]);
  const [activeTaskId, setActiveTaskId] = useState(null);

  // Persist chat + tasks across navigation (per user/team)
  React.useEffect(() => {
    if (!metricsKey) return;
    const saved = readMetrics(metricsKey);
    const savedChat = saved.chatByAgent?.[activeAgent] || [];
    const savedTasks = saved.completedTasks || [];
    setChatMessages(savedChat);
    setCompletedTasks(savedTasks);
  }, [metricsKey, activeAgent]);

  // Save current agent chat whenever it changes
  React.useEffect(() => {
    if (!metricsKey) return;
    setChatForAgent(metricsKey, activeAgent, chatMessages);
  }, [metricsKey, activeAgent, chatMessages]);

  // Save completed tasks whenever they change
  React.useEffect(() => {
    if (!metricsKey) return;
    persistCompletedTasks(metricsKey, completedTasks);
  }, [metricsKey, completedTasks]);

  const addCompletedTask = (task) => {
    setCompletedTasks(prev => [task, ...prev].slice(0, 10));

    // Metrics: count built-in agent tasks
    if (metricsKey) {
      incrementAgentTask(metricsKey, task.agent);
    }
  };

  const addChatMessage = (message) => {
    setChatMessages(prev => [...prev, message]);
  };

  const clearChat = () => {
    setChatMessages([]);
  };

  const handleAgentChange = (agentId) => {
    setActiveAgent(agentId);
    setActiveTaskId(null);
    // NOTE: chat for the agent will load from persisted storage via effect
  };

  const handleTaskClick = (task) => {
    if (activeTaskId === task.id) return;
    
    if (activeAgent !== task.agent) {
      setActiveAgent(task.agent);
    }
    
    setActiveTaskId(task.id);
    setChatMessages(task.messages || []);
  };

  const currentAgent = AGENTS.find(a => a.id === activeAgent);

  return (
    <div className="h-full w-full overflow-hidden bg-white flex flex-col">
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
