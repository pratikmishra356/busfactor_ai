import React from 'react';
import { Link } from 'react-router-dom';
import { Database, AlertTriangle, Users, ArrowRight, Sparkles, Activity } from 'lucide-react';

const useCases = [
  {
    id: 'knowledge',
    title: 'Knowledge Base',
    description: 'Search and explore organizational context from Slack, Jira, GitHub, Docs, and Meetings.',
    icon: Database,
    path: '/knowledge',
    color: 'primary',
    features: ['Semantic Search', 'Weekly Summaries', 'Multi-source Context']
  },
  {
    id: 'incident',
    title: 'Incident Analysis',
    description: 'Generate comprehensive RCA reports with timeline, root cause, and recommendations.',
    icon: AlertTriangle,
    path: '/incident',
    color: 'error',
    features: ['RCA Reports', 'Timeline View', 'Related Tickets & PRs']
  },
  {
    id: 'companion',
    title: 'AI Companion',
    description: 'Get role-specific insights and action items for Engineers, PMs, and EMs.',
    icon: Users,
    path: '/companion',
    color: 'info',
    features: ['Role-based Views', 'Priority Items', 'Action Items']
  }
];

function UseCaseCard({ useCase }) {
  const Icon = useCase.icon;
  
  return (
    <Link
      to={useCase.path}
      data-testid={`usecase-card-${useCase.id}`}
      className="
        group bg-surface border border-border rounded-sm p-6
        hover:border-primary/50 transition-all duration-300
        flex flex-col h-full
      "
    >
      <div className="flex items-start justify-between mb-4">
        <div className={`w-12 h-12 rounded-sm flex items-center justify-center bg-${useCase.color}/20`}>
          <Icon className={`w-6 h-6 text-${useCase.color}`} />
        </div>
        <ArrowRight className="w-5 h-5 text-text-muted group-hover:text-primary group-hover:translate-x-1 transition-all" />
      </div>
      
      <h3 className="font-heading font-bold text-xl mb-2 text-white group-hover:text-primary transition-colors">
        {useCase.title}
      </h3>
      
      <p className="text-text-muted text-sm mb-4 flex-1">
        {useCase.description}
      </p>
      
      <div className="flex flex-wrap gap-2">
        {useCase.features.map((feature, idx) => (
          <span key={idx} className="text-xs bg-border/50 text-text-muted px-2 py-1 rounded-sm">
            {feature}
          </span>
        ))}
      </div>
    </Link>
  );
}

function StatCard({ label, value, icon: Icon }) {
  return (
    <div className="bg-surface border border-border rounded-sm p-4">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-sm bg-primary/20 flex items-center justify-center">
          <Icon className="w-5 h-5 text-primary" />
        </div>
        <div>
          <p className="text-2xl font-heading font-bold text-white">{value}</p>
          <p className="text-xs text-text-muted uppercase tracking-widest">{label}</p>
        </div>
      </div>
    </div>
  );
}

export default function Dashboard() {
  return (
    <div className="p-8 max-w-7xl mx-auto">
      {/* Hero Section */}
      <div className="mb-12">
        <div className="flex items-center gap-2 mb-4">
          <Sparkles className="w-5 h-5 text-primary" />
          <span className="text-xs uppercase tracking-widest text-primary font-semibold">Context Intelligence Platform</span>
        </div>
        <h1 className="font-heading font-black text-4xl md:text-5xl mb-4 tracking-tight">
          Your Organization's<br />
          <span className="text-primary">Knowledge Hub</span>
        </h1>
        <p className="text-text-muted text-lg max-w-2xl">
          Unified intelligence from Slack, Jira, GitHub, Documentation, and Meetings. 
          Search, analyze incidents, and get role-specific insights powered by AI.
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-12">
        <StatCard label="Entities Indexed" value="148" icon={Database} />
        <StatCard label="Connections" value="212" icon={Activity} />
        <StatCard label="Weekly Summaries" value="9" icon={Sparkles} />
        <StatCard label="Data Sources" value="5" icon={Users} />
      </div>

      {/* Use Cases */}
      <div className="mb-8">
        <h2 className="font-heading font-bold text-2xl mb-6 text-white">Get Started</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {useCases.map((useCase) => (
            <UseCaseCard key={useCase.id} useCase={useCase} />
          ))}
        </div>
      </div>

      {/* Quick Tips */}
      <div className="bg-surface border border-border rounded-sm p-6">
        <h3 className="font-heading font-bold text-lg mb-4 text-white">Quick Tips</h3>
        <ul className="space-y-2 text-text-muted text-sm">
          <li className="flex items-start gap-2">
            <span className="text-primary">•</span>
            Use natural language queries like "payment gateway issues" or "database performance problems"
          </li>
          <li className="flex items-start gap-2">
            <span className="text-primary">•</span>
            Incident Analysis generates RCA reports with related tickets, PRs, and timeline
          </li>
          <li className="flex items-start gap-2">
            <span className="text-primary">•</span>
            AI Companion provides role-specific insights for Engineers, PMs, and Engineering Managers
          </li>
        </ul>
      </div>
    </div>
  );
}
