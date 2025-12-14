import React from 'react';
import { ArrowRight, Boxes, Cpu, Database, GitBranch, Layers, ShieldCheck, Sparkles, Workflow } from 'lucide-react';
import { Link } from 'react-router-dom';

const TOOL_BADGES = [
  { name: 'Slack', icon: Workflow },
  { name: 'Jira', icon: ShieldCheck },
  { name: 'Linear', icon: Layers },
  { name: 'GitHub', icon: GitBranch },
  { name: 'Bitbucket', icon: GitBranch },
  { name: 'Zoom', icon: Sparkles },
  { name: 'Google Meet', icon: Sparkles },
];

const AGENT_CARDS = [
  {
    title: 'OnCall Agent',
    description: 'Triage incidents, explain blast radius, and propose mitigations from your real operational context.',
  },
  {
    title: 'Backend Developer',
    description: 'Understand code + PR history, suggest changes, and keep decisions aligned with your architecture.',
  },
  {
    title: 'Product Manager',
    description: 'Turn engineering context into decisions: tradeoffs, timelines, and stakeholder-ready summaries.',
  },
  {
    title: 'Document Generator',
    description: 'Generate runbooks, postmortems, and onboarding docs with references to indexed sources.',
  },
];

function Section({ children, className = '' }) {
  return (
    <section className={`w-full max-w-6xl mx-auto px-6 ${className}`}>
      {children}
    </section>
  );
}

function Card({ children }) {
  return (
    <div className="bg-white border border-slate-200 rounded-2xl shadow-sm">
      {children}
    </div>
  );
}

export default function LandingPage() {
  return (
    <div className="h-full overflow-auto bg-white">
      {/* Hero */}
      <div className="relative overflow-hidden border-b border-slate-200">
        <div className="absolute inset-0 builder-grid opacity-30" />
        <div className="absolute -top-24 right-[-140px] w-[420px] h-[420px] rounded-full bg-gradient-to-br from-blue-200/60 to-violet-200/60 blur-3xl" />
        <div className="absolute -bottom-24 left-[-140px] w-[420px] h-[420px] rounded-full bg-gradient-to-tr from-sky-200/60 to-blue-200/60 blur-3xl" />

        <Section className="relative py-16 sm:py-20">
          <div className="text-center flex flex-col items-center gap-6">
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-slate-200 bg-white/70 text-xs text-slate-700 shadow-sm">
              <Cpu className="w-4 h-4 text-blue-600" />
              MCP Layer for indexed engineering context
            </div>

            <h1 className="font-heading font-bold text-4xl sm:text-5xl lg:text-6xl tracking-tight text-slate-900">
              busfactor AI
            </h1>

            <p className="max-w-3xl text-sm sm:text-base md:text-lg text-slate-600 leading-relaxed">
              Increase your team’s bus factor by turning fragmented engineering operations knowledge into a deployable,
              agent-ready context layer.
              {' '}Connect your tools, build a RAG-powered knowledge base, and ship AI agents that work the way your org works.
            </p>

            <div className="flex items-center gap-3">
              <Link
                to="/agents"
                className="inline-flex items-center gap-2 px-5 py-3 rounded-xl bg-blue-600 text-white text-sm font-semibold shadow-sm hover:bg-blue-700 transition-colors"
              >
                Open Agents
                <ArrowRight className="w-4 h-4" />
              </Link>
              <Link
                to="/agent-builder"
                className="inline-flex items-center gap-2 px-5 py-3 rounded-xl bg-white border border-slate-200 text-slate-800 text-sm font-semibold shadow-sm hover:bg-slate-50 transition-colors"
              >
                Build an Agent
                <Boxes className="w-4 h-4" />
              </Link>
            </div>
          </div>
        </Section>
      </div>

      {/* Tool connectors */}
      <Section className="py-10">
        <div className="flex flex-col gap-6">
          <div className="text-center">
            <h2 className="font-heading font-semibold text-base md:text-lg text-slate-900">Plug in the tools your team already uses</h2>
            <p className="mt-2 text-sm text-slate-600">Unify conversations, tickets, code, and meetings into a single operational context.</p>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-7 gap-3">
            {TOOL_BADGES.map((t) => {
              const Icon = t.icon;
              return (
                <div
                  key={t.name}
                  className="flex items-center justify-center gap-2 px-3 py-2 rounded-xl border border-slate-200 bg-white shadow-sm text-sm text-slate-700"
                >
                  <Icon className="w-4 h-4 text-slate-500" />
                  <span className="truncate">{t.name}</span>
                </div>
              );
            })}
          </div>
        </div>
      </Section>

      {/* How it works */}
      <Section className="py-10">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <Card>
            <div className="p-6">
              <div className="flex items-center gap-2">
                <div className="w-10 h-10 rounded-xl bg-blue-50 border border-blue-200 flex items-center justify-center">
                  <Workflow className="w-5 h-5 text-blue-600" />
                </div>
                <h3 className="font-heading font-semibold text-slate-900">1) Connect</h3>
              </div>
              <p className="mt-3 text-sm text-slate-600 leading-relaxed">
                Ingest engineering signals from chat, ticketing, repos, and meetings—without changing your workflows.
              </p>
            </div>
          </Card>

          <Card>
            <div className="p-6">
              <div className="flex items-center gap-2">
                <div className="w-10 h-10 rounded-xl bg-violet-50 border border-violet-200 flex items-center justify-center">
                  <Database className="w-5 h-5 text-violet-600" />
                </div>
                <h3 className="font-heading font-semibold text-slate-900">2) Index + RAG</h3>
              </div>
              <p className="mt-3 text-sm text-slate-600 leading-relaxed">
                Build an indexed knowledge base and retrieval layer that preserves source links, recency, and intent.
              </p>
            </div>
          </Card>

          <Card>
            <div className="p-6">
              <div className="flex items-center gap-2">
                <div className="w-10 h-10 rounded-xl bg-emerald-50 border border-emerald-200 flex items-center justify-center">
                  <Boxes className="w-5 h-5 text-emerald-600" />
                </div>
                <h3 className="font-heading font-semibold text-slate-900">3) Build agents</h3>
              </div>
              <p className="mt-3 text-sm text-slate-600 leading-relaxed">
                Deploy org-specific agents for oncall, dev, PM, and docs—powered by the same trusted context layer.
              </p>
            </div>
          </Card>
        </div>
      </Section>

      {/* MCP uniqueness */}
      <Section className="py-10">
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-4 items-stretch">
          <div className="lg:col-span-2">
            <div className="h-full rounded-2xl border border-slate-200 bg-gradient-to-br from-slate-50 to-white p-6 shadow-sm">
              <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-full bg-white border border-slate-200 text-xs text-slate-700">
                <Layers className="w-4 h-4 text-blue-600" />
                Our uniqueness
              </div>
              <h2 className="mt-4 font-heading font-semibold text-base md:text-lg text-slate-900">
                MCP layer over your indexed knowledge
              </h2>
              <p className="mt-3 text-sm text-slate-600 leading-relaxed">
                We don’t just store documents—we expose your organization’s engineering context as an MCP-compatible layer.
                Teams can build, evaluate, and deploy agents on top of the same indexed sources with consistent retrieval.
              </p>
            </div>
          </div>

          <div className="lg:col-span-3">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {AGENT_CARDS.map((c) => (
                <Card key={c.title}>
                  <div className="p-6">
                    <h3 className="font-heading font-semibold text-slate-900">{c.title}</h3>
                    <p className="mt-2 text-sm text-slate-600 leading-relaxed">{c.description}</p>
                  </div>
                </Card>
              ))}
            </div>
          </div>
        </div>
      </Section>

      {/* Benefits + CTA */}
      <Section className="py-12">
        <div className="rounded-2xl border border-slate-200 bg-white shadow-sm p-6 sm:p-8">
          <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6">
            <div>
              <h2 className="font-heading font-semibold text-base md:text-lg text-slate-900">Make engineering operations faster and safer</h2>
              <p className="mt-2 text-sm text-slate-600 leading-relaxed max-w-2xl">
                Reduce time-to-context during incidents, improve onboarding, and keep decisions grounded in your org’s real history—
                not tribal memory.
              </p>
            </div>
            <Link
              to="/agents"
              className="inline-flex items-center gap-2 px-5 py-3 rounded-xl bg-gradient-to-r from-blue-600 to-violet-600 text-white text-sm font-semibold shadow-sm hover:opacity-95 transition-opacity"
            >
              Try the Agents UI
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>

        <div className="py-8 text-center text-xs text-slate-500">
          © {new Date().getFullYear()} busfactor AI. All rights reserved.
        </div>
      </Section>
    </div>
  );
}
