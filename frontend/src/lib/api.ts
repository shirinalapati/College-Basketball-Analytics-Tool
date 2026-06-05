const API_BASE = import.meta.env.VITE_API_URL || '/api';

async function fetchJson<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error((err as { detail?: string }).detail || 'API error');
  }
  return res.json();
}

export const api = {
  meta: () => fetchJson<{ teams_count: number; players_count: number; data_label: string }>('/meta'),
  overview: () => fetchJson<import('../types').OverviewData>('/overview'),
  teams: () => fetchJson<import('../types').Team[]>('/teams'),
  team: (id: string) => fetchJson<{ team: import('../types').Team; needs: import('../types').TeamNeeds }>(`/teams/${id}`),
  teamPlayers: (id: string) => fetchJson<import('../types').Player[]>(`/teams/${id}/players`),
  // alias used by simulator
  getTeamPlayers: (id: string) => fetchJson<import('../types').Player[]>(`/teams/${id}/players`),
  developmentBoard: (id: string) => fetchJson<import('../types').DevelopmentBoardRow[]>(`/teams/${id}/development-board`),
  player: (id: string) => fetchJson<{
    player: import('../types').Player;
    team: import('../types').Team;
    priorities: import('../types').DevelopmentPriority[];
    leverage: Record<string, unknown>;
    stat_ranks: Record<string, import('../types').StatRank>;
    simulator_presets: import('../types').SimulatorPresets;
  }>(`/players/${id}`),
  search: (q: string, limit = 12) => {
    const params = new URLSearchParams({ q, limit: String(limit) });
    return fetchJson<import('../types').SearchResponse>(`/search?${params}`);
  },
  leverageLeaderboard: (limit = 50, teamId?: string) => {
    const q = new URLSearchParams({ limit: String(limit) });
    if (teamId) q.set('team_id', teamId);
    return fetchJson<import('../types').LeverageRow[]>(`/leaderboard/leverage?${q}`);
  },
  simulate: (body: Record<string, number | string>) =>
    fetch(`${API_BASE}/simulate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    }).then((r) => r.json()),
};
