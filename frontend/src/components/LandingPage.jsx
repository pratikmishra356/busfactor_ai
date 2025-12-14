import React, { useMemo, useState } from 'react';
import { Boxes, Cpu, Database, GitBranch, Layers, ShieldCheck, Sparkles, Workflow } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { useAuth } from '@/context/AuthContext';
import { useToast } from '@/hooks/use-toast';
import { listDynamicAgents } from '@/services/api';
import { getMetricsKey, readMetrics, setDynamicAgentsCount } from '@/services/metrics';

function StatCard({ label, value }) {
  return (
    <div className="bg-white border border-slate-200 rounded-2xl shadow-sm p-5">
      <div className="text-xs text-slate-500">{label}</div>
      <div className="mt-1 text-2xl font-bold text-slate-900">{value}</div>
    </div>
  );
}


const TOOL_BADGES = [
  { id: 'slack', name: 'Slack', icon: Workflow },
  { id: 'jira', name: 'Jira', icon: ShieldCheck },
  { id: 'linear', name: 'Linear', icon: Layers },
  { id: 'github', name: 'GitHub', icon: GitBranch },
  { id: 'bitbucket', name: 'Bitbucket', icon: GitBranch },
  { id: 'zoom', name: 'Zoom', icon: Sparkles },
  { id: 'meet', name: 'Google Meet', icon: Sparkles },
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
  const navigate = useNavigate();
  const { isAuthenticated, login, refreshTeam, refreshUser, user, team } = useAuth();
  const { toast } = useToast();

  const [dialogOpen, setDialogOpen] = useState(false);
  const [teamName, setTeamName] = useState('');
  const [selectedTools, setSelectedTools] = useState(() => new Set());
  const [metrics, setMetrics] = useState(null);

  const metricsKey = user && team?.team_id ? getMetricsKey({ userId: user.user_id, teamId: team.team_id }) : null;

  const tools = useMemo(() => TOOL_BADGES, []);
  const canSubmit = teamName.trim().length > 0 && selectedTools.size > 0;

  const toggleTool = (toolId) => {
    setSelectedTools((prev) => {
      const next = new Set(prev);
      if (next.has(toolId)) next.delete(toolId);
      else next.add(toolId);
      return next;
    });
  };

  const handleCreateTeam = async () => {
    // Team creation is now stored server-side after login
    const payload = {
      team_name: teamName.trim(),
      tools: Array.from(selectedTools),
    };

    const apiBase = process.env.REACT_APP_BACKEND_URL || '';
    const token = window.localStorage.getItem('session_token');
    const res = await fetch(`${apiBase}/api/team/create`, {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      throw new Error('Failed to create team');
    }

    setDialogOpen(false);
    navigate('/agents');
  };

  return (
    <div className="h-full overflow-auto bg-white">
      {/* Hero */}
      <div className="relative overflow-hidden border-b border-slate-200">
        <div className="absolute inset-0 builder-grid opacity-30" />
        <div className="absolute -top-24 right-[-140px] w-[420px] h-[420px] rounded-full bg-gradient-to-br from-blue-200/60 to-violet-200/60 blur-3xl" />
        <div className="absolute -bottom-24 left-[-140px] w-[420px] h-[420px] rounded-full bg-gradient-to-tr from-sky-200/60 to-blue-200/60 blur-3xl" />

        <Section className="relative py-16 sm:py-20">
          <div className="text-center flex flex-col items-center gap-4">
            <h1 className="font-heading font-bold text-4xl sm:text-5xl lg:text-6xl tracking-tight text-slate-900">
              busfactor AI
            </h1>

            <div
              className="inline-flex items-center justify-center gap-2 px-4 py-2 rounded-full border border-slate-200 bg-white/70 text-slate-700 shadow-sm text-sm sm:text-base w-[90vw] sm:w-[30vw] max-w-[520px]"
              aria-label="MCP Layer for indexed engineering context"
            >
              <Cpu className="w-5 h-5 text-blue-600" />
              <span className="font-semibold">MCP Layer for indexed engineering context</span>
            </div>

            <p className="max-w-3xl text-sm sm:text-base md:text-lg text-slate-600 leading-relaxed">
              Build a RAG-powered knowledge base, and ship AI agents that work the way your org works.
            </p>

            <Dialog
              open={dialogOpen}
              onOpenChange={async (open) => {
                if (open) {
                  // Always re-check session server-side to avoid stale auth state
                  const u = await refreshUser();
                  if (!u) {
                    toast({
                      title: 'Login required',
                      description: 'Please login first to create your team.',
                    });
                    login('/');
                    return;
                  }
                }
                setDialogOpen(open);
              }}
            >
              <DialogTrigger asChild>
                <Button className="h-11 px-6 rounded-xl bg-blue-600 hover:bg-blue-700 text-white shadow-sm">
                  Create Team
                </Button>
              </DialogTrigger>

              <DialogContent className="sm:max-w-xl">
                <DialogHeader>
                  <DialogTitle>Create your team{user?.name ? ` — ${user.name}` : ''}</DialogTitle>
                  <DialogDescription>
                    Pick the tools you want to integrate. You can change these later.
                  </DialogDescription>
                </DialogHeader>

                <div className="grid gap-4">
                  <div className="grid gap-2">
                    <label className="text-sm font-medium text-slate-900">Team name</label>
                    <Input
                      value={teamName}
                      onChange={(e) => setTeamName(e.target.value)}
                      placeholder="e.g. Platform Engineering"
                    />
                  </div>

                  <div className="grid gap-2">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-slate-900">Integrate tools</span>
                      <span className="text-xs text-slate-500">Select 1+ tools</span>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      {tools.map((t) => {
                        const Icon = t.icon;
                        const checked = selectedTools.has(t.id);
                        return (
                          <div
                            key={t.id}
                            role="button"
                            tabIndex={0}
                            onClick={() => toggleTool(t.id)}
                            onKeyDown={(e) => {
                              if (e.key === 'Enter' || e.key === ' ') {
                                e.preventDefault();
                                toggleTool(t.id);
                              }
                            }}
                            className={`flex items-center justify-between gap-3 rounded-xl border px-3 py-2 text-left shadow-sm transition-colors cursor-pointer ${
                              checked
                                ? 'border-blue-300 bg-blue-50'
                                : 'border-slate-200 bg-white hover:bg-slate-50'
                            }`}
                          >
                            <div className="flex items-center gap-2">
                              <Icon className="w-4 h-4 text-slate-500" />
                              <span className="text-sm text-slate-800">{t.name}</span>
                            </div>
                            <Checkbox checked={checked} className="pointer-events-none" />
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </div>

                <DialogFooter>
                  <Button
                    variant="outline"
                    onClick={() => setDialogOpen(false)}
                  >
                    Cancel
                  </Button>
                  <Button
                    onClick={async () => {
                      try {
                        await handleCreateTeam();
                        await refreshTeam();
                      } catch {
                        toast({
                          title: 'Could not create team',
                          description: 'Please try again.',
                        });
                      }
                    }}
                    disabled={!canSubmit}
                    className="bg-blue-600 hover:bg-blue-700"
                  >
                    Continue
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
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
                  key={t.id}
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
                <h3 className="font-heading font-semibold text-slate-900">Connect</h3>
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
                <h3 className="font-heading font-semibold text-slate-900">Index + RAG</h3>
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
                <h3 className="font-heading font-semibold text-slate-900">Build agents</h3>
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

      <Section className="py-12">
        <div className="py-8 text-center text-xs text-slate-500">
          © {new Date().getFullYear()} busfactor AI. All rights reserved.
        </div>
      </Section>
    </div>
  );
}
