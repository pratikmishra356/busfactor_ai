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
        updatedAt: null,
      };
    }
    const parsed = JSON.parse(raw);
    return {
      totalTasks: parsed.totalTasks || 0,
      byAgent: parsed.byAgent || {},
      dynamicAgentsCount: parsed.dynamicAgentsCount || 0,
      updatedAt: parsed.updatedAt || null,
    };
  } catch {
    return {
      totalTasks: 0,
      byAgent: {},
      dynamicAgentsCount: 0,
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
