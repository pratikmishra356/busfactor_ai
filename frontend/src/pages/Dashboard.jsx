import React from 'react';
import { Link } from 'react-router-dom';
import { Search, AlertTriangle, Bot, ArrowRight, Database, MessageSquare, GitBranch, FileText, Users } from 'lucide-react';

const USE_CASES = [
  {
    id: 'knowledge',
    title: 'Knowledge Base',
    description: 'Search and explore organizational context from all your data sources.',
    icon: Search,
    color: 'bg-info/20 text-info',
    path: '/knowledge',
    features: ['Vector search', 'Multi-source', 'Weekly summaries'],
  },
  {
    id: 'incident',
    title: 'Analyse Incident',
    description: 'Generate comprehensive RCA reports with timeline and recommendations.',
    icon: AlertTriangle,
    color: 'bg-error/20 text-error',
    path: '/incident',
    features: ['RCA reports', 'Timeline view', 'Related items'],
  },
  {
    id: 'companion',
    title: 'AI Companion',
    description: 'Your role-based intelligent assistant for contextual insights.',
    icon: Bot,
    color: 'bg-primary/20 text-primary',
    path: '/companion',
    features: ['Engineer', 'Product Manager', 'Eng Manager'],
  },
];

const STATS = [
  { label: 'Data Sources', value: '5', icon: Database },
  { label: 'Entities Indexed', value: '148', icon: FileText },
  { label: 'Connections', value: '212', icon: GitBranch },
  { label: 'Weekly Summaries', value: '9', icon: MessageSquare },
];

export default function Dashboard() {
  return (
    <div className="p-8 max-w-7xl mx-auto">
      {/* Hero Section */}
      <div className="mb-12">
        <h1 className="font-heading font-black text-5xl md:text-6xl tracking-tight mb-4">
          Context <span className="text-primary">Intelligence</span>
        </h1>
        <p className="text-text-muted text-lg max-w-2xl leading-relaxed">
          Unified intelligence across Slack, Jira, GitHub, Docs, and Meetings. 
          Search, analyze, and get AI-powered insights from your organization's knowledge.
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-12">
        {STATS.map((stat) => (
          <div key={stat.label} className="bg-surface border border-border rounded-sm p-4" data-testid={`stat-${stat.label.toLowerCase().replace(/ /g, '-')}`}>
            <div className="flex items-center gap-3">
              <stat.icon className="w-5 h-5 text-primary" />
              <div>
                <p className="text-2xl font-heading font-bold text-white">{stat.value}</p>
                <p className="text-xs text-text-muted uppercase tracking-widest">{stat.label}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Use Cases Grid */}
      <div className="mb-8">
        <h2 className="text-xs uppercase tracking-widest text-text-muted mb-4">Use Cases</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {USE_CASES.map((useCase) => (
            <Link
              key={useCase.id}
              to={useCase.path}
              data-testid={`usecase-${useCase.id}`}
              className="group bg-surface border border-border rounded-sm p-6 hover:border-primary/50 transition-all duration-300"
            >
              <div className={`w-14 h-14 ${useCase.color} rounded-sm flex items-center justify-center mb-4`}>
                <useCase.icon className="w-7 h-7" />
              </div>
              <h3 className="font-heading font-bold text-xl text-white mb-2 group-hover:text-primary transition-colors">
                {useCase.title}
              </h3>
              <p className="text-text-muted text-sm mb-4 leading-relaxed">
                {useCase.description}
              </p>
              <div className="flex flex-wrap gap-2 mb-4">
                {useCase.features.map((feature) => (
                  <span key={feature} className="text-xs px-2 py-1 bg-background border border-border rounded-sm text-text-muted">
                    {feature}
                  </span>
                ))}
              </div>
              <div className="flex items-center gap-2 text-primary text-sm font-medium opacity-0 group-hover:opacity-100 transition-opacity">
                Open <ArrowRight className="w-4 h-4" />
              </div>
            </Link>
          ))}
        </div>
      </div>

      {/* Data Sources */}
      <div className="bg-surface border border-border rounded-sm p-6">
        <h2 className="text-xs uppercase tracking-widest text-text-muted mb-4">Connected Sources</h2>
        <div className="flex flex-wrap gap-4">
          {[
            { name: 'Slack', icon: MessageSquare, count: 67 },
            { name: 'Jira', icon: AlertTriangle, count: 36 },
            { name: 'GitHub', icon: GitBranch, count: 17 },
            { name: 'Docs', icon: FileText, count: 14 },
            { name: 'Meetings', icon: Users, count: 14 },
          ].map((source) => (
            <div key={source.name} className="flex items-center gap-3 px-4 py-3 bg-background border border-border rounded-sm" data-testid={`source-${source.name.toLowerCase()}`}>
              <source.icon className="w-5 h-5 text-primary" />
              <div>
                <p className="font-medium text-white text-sm">{source.name}</p>
                <p className="text-xs text-text-muted">{source.count} entities</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
