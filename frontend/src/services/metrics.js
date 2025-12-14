const METRICS_VERSION = 1;

export function getMetricsKey({ userId, teamId }) {
  return `busfactor_metrics_v${METRICS_VERSION}_${userId || 'anon'}_${teamId || 'noteam'}`;
}

export function readMetrics(key) {
  try {
    const raw = window.localStorage.getItem(key);
    if (!raw) {
      return {
        totalTasks: 0,
        byAgent: {},
        dynamicAgentsCount: 0,
        chatByAgent: {},
        completedTasks: [],
        updatedAt: null,
      };
    }
    const parsed = JSON.parse(raw);
    return {
      totalTasks: parsed.totalTasks || 0,
      byAgent: parsed.byAgent || {},
      dynamicAgentsCount: parsed.dynamicAgentsCount || 0,
      chatByAgent: parsed.chatByAgent || {},
      completedTasks: parsed.completedTasks || [],
      updatedAt: parsed.updatedAt || null,
    };
  } catch {
    return {
      totalTasks: 0,
      byAgent: {},
      dynamicAgentsCount: 0,
      chatByAgent: {},
      completedTasks: [],
      updatedAt: null,
    };
  }
}

export function writeMetrics(key, metrics) {
  window.localStorage.setItem(
    key,
    JSON.stringify({
      ...metrics,
      updatedAt: new Date().toISOString(),
    })
  );
}

export function incrementAgentTask(key, agentIdOrName) {
  const metrics = readMetrics(key);
  const byAgent = { ...metrics.byAgent };
  byAgent[agentIdOrName] = (byAgent[agentIdOrName] || 0) + 1;
  writeMetrics(key, {
    ...metrics,
    totalTasks: (metrics.totalTasks || 0) + 1,
    byAgent,
  });
}

export function setDynamicAgentsCount(key, count) {
  const metrics = readMetrics(key);
  writeMetrics(key, {
    ...metrics,
    dynamicAgentsCount: count,
  });
}

export function setChatForAgent(key, agentId, messages) {
  const metrics = readMetrics(key);
  const chatByAgent = { ...(metrics.chatByAgent || {}) };
  // Only persist serializable messages
  chatByAgent[agentId] = (messages || []).map((m) => ({
    ...m,
    content: typeof m.content === 'string' ? m.content : '',
  }));

  writeMetrics(key, {
    ...metrics,
    chatByAgent,
  });
}

export function setCompletedTasks(key, tasks) {
  const metrics = readMetrics(key);
  writeMetrics(key, {
    ...metrics,
    completedTasks: (tasks || []).slice(0, 10),
  });
}
