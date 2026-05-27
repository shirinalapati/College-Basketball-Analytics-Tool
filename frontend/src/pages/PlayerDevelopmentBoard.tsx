import { useEffect, useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../lib/api';
import { Team, DevelopmentBoardRow } from '../types';
import { SKILL_LABELS } from '../types';
import { useTeamQuery } from '../lib/useTeamQuery';
import DemoBanner from '../components/DemoBanner';
import TeamSelect from '../components/TeamSelect';
import ApiError from '../components/ApiError';

const PRIORITY_OPTIONS = Object.entries(SKILL_LABELS).map(([k, v]) => ({ id: k, label: v }));

export default function PlayerDevelopmentBoard() {
  const [teams, setTeams] = useState<Team[]>([]);
  const [teamId, setTeamId] = useTeamQuery();
  const [board, setBoard] = useState<DevelopmentBoardRow[]>([]);
  const [posFilter, setPosFilter] = useState('');
  const [priorityFilter, setPriorityFilter] = useState('');
  const [sortBy, setSortBy] = useState<'dps' | 'leverage' | 'mpg'>('dps');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.teams().then(setTeams).catch((e) => setError(e.message));
  }, []);

  useEffect(() => {
    if (!teamId) return;
    setLoading(true);
    setError('');
    api
      .developmentBoard(teamId)
      .then(setBoard)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [teamId]);

  const filtered = useMemo(() => {
    let rows = [...board];
    if (posFilter) rows = rows.filter((r) => r.position === posFilter);
    if (priorityFilter) rows = rows.filter((r) => r.top_priority === priorityFilter);
    rows.sort((a, b) => {
      if (sortBy === 'leverage')
        return (b.development_leverage_score ?? 0) - (a.development_leverage_score ?? 0);
      if (sortBy === 'mpg') return b.mpg - a.mpg;
      return b.development_priority_score - a.development_priority_score;
    });
    return rows;
  }, [board, posFilter, priorityFilter, sortBy]);

  return (
    <div className="space-y-6">
      <DemoBanner />
      <div className="flex flex-wrap gap-4 items-end justify-between">
        <div>
          <h2 className="font-display text-2xl font-bold">Player Development Board</h2>
          <p className="text-gray-400 text-sm">Rotation players ranked by development priority for the selected team.</p>
        </div>
        <TeamSelect teams={teams} value={teamId} onChange={setTeamId} />
      </div>

      <div className="flex flex-wrap gap-3">
        <select
          value={posFilter}
          onChange={(e) => setPosFilter(e.target.value)}
          className="bg-surface-card border border-surface-border rounded-lg px-3 py-1.5 text-sm"
        >
          <option value="">All positions</option>
          <option value="G">Guards</option>
          <option value="F">Forwards</option>
          <option value="C">Centers</option>
        </select>
        <select
          value={priorityFilter}
          onChange={(e) => setPriorityFilter(e.target.value)}
          className="bg-surface-card border border-surface-border rounded-lg px-3 py-1.5 text-sm"
        >
          <option value="">All priorities</option>
          {PRIORITY_OPTIONS.map((p) => (
            <option key={p.id} value={p.id}>{p.label}</option>
          ))}
        </select>
        <select
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value as typeof sortBy)}
          className="bg-surface-card border border-surface-border rounded-lg px-3 py-1.5 text-sm"
        >
          <option value="dps">Sort by DPS</option>
          <option value="leverage">Sort by Leverage</option>
          <option value="mpg">Sort by MPG</option>
        </select>
      </div>

      {error && <ApiError message={error} />}

      <div className="card overflow-x-auto">
        {loading ? (
          <p className="text-gray-400 py-8 text-center">Loading board…</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-gray-400 border-b border-surface-border">
                <th className="py-2 pr-4">Player</th>
                <th className="py-2">Pos</th>
                <th className="py-2">MPG</th>
                <th className="py-2">Top Priority</th>
                <th className="py-2">DPS</th>
                <th className="py-2">Proj. Value</th>
                <th className="py-2">Leverage</th>
                <th className="py-2 min-w-[200px]">Main Reason</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((row) => (
                <tr key={row.player_id} className="table-row-hover border-b border-surface-border/50">
                  <td className="py-3 pr-4">
                    <Link to={`/player/${row.player_id}`} className="text-illini-orange font-medium hover:underline">
                      {row.player_name}
                    </Link>
                  </td>
                  <td>{row.position}</td>
                  <td>{row.mpg?.toFixed(1)}</td>
                  <td>
                    <span className="badge-orange">
                      {SKILL_LABELS[row.top_priority] || row.top_priority}
                    </span>
                  </td>
                  <td className="font-bold">{row.development_priority_score?.toFixed(1)}</td>
                  <td>+{row.projected_points_added?.toFixed(1)}</td>
                  <td>{row.development_leverage_score?.toFixed(1) ?? '—'}</td>
                  <td className="text-gray-400 text-xs max-w-xs" title={row.main_reason}>
                    {row.main_reason && row.main_reason.length > 120
                      ? `${row.main_reason.slice(0, 120)}…`
                      : row.main_reason}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        {!loading && !filtered.length && !error && (
          <p className="text-gray-500 py-6 text-center">No players match filters.</p>
        )}
      </div>
    </div>
  );
}
