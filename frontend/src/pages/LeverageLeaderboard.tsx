import { useEffect, useMemo, useState, useRef } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { api } from '../lib/api';
import { LeverageRow, Team } from '../types';
import { SKILL_LABELS } from '../types';
import { LEVERAGE_PROJ_VALUE_NOTE, PROJ_VALUE_COLUMN_TOOLTIP } from '../lib/projectionCopy';
import TeamSelect from '../components/TeamSelect';

const PRIORITY_OPTIONS = Object.entries(SKILL_LABELS).map(([id, label]) => ({ id, label }));

const CLASS_OPTIONS = [
  { id: 'So', label: 'Sophomore' },
  { id: 'Jr', label: 'Junior' },
  { id: 'Sr', label: 'Senior' },
  { id: 'Gr', label: 'Graduate' },
];

export default function LeverageLeaderboard() {
  const [searchParams, setSearchParams] = useSearchParams();
  const highlightPlayer = searchParams.get('player');
  const teamFilter = searchParams.get('team') || '';
  const rowRefs = useRef<Record<string, HTMLTableRowElement | null>>({});
  const [rows, setRows] = useState<LeverageRow[]>([]);
  const [teams, setTeams] = useState<Team[]>([]);
  const [positionFilter, setPositionFilter] = useState('');
  const [priorityFilter, setPriorityFilter] = useState('');
  const [conferenceFilter, setConferenceFilter] = useState('');
  const [minMpg, setMinMpg] = useState(10);
  const [classFilter, setClassFilter] = useState('');
  const [minTeamNeed, setMinTeamNeed] = useState(0);
  const [minLeverage, setMinLeverage] = useState(0);

  const setTeamFilter = (id: string) => {
    const next = new URLSearchParams(searchParams);
    if (id) next.set('team', id);
    else next.delete('team');
    next.delete('player');
    setSearchParams(next, { replace: true });
  };

  useEffect(() => {
    api.teams().then(setTeams);
  }, []);

  useEffect(() => {
    api.leverageLeaderboard(1000, teamFilter || undefined).then(setRows);
  }, [teamFilter]);

  useEffect(() => {
    if (!highlightPlayer || !rows.length) return;
    const row = rowRefs.current[highlightPlayer];
    row?.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
  }, [highlightPlayer, rows]);

  const conferences = useMemo(
    () => [...new Set(teams.map((t) => t.conference).filter(Boolean))].sort(),
    [teams]
  );

  const filteredRows = useMemo(() => {
    return rows.filter((r) => {
      if (positionFilter && r.position !== positionFilter) return false;
      if (priorityFilter && r.top_priority !== priorityFilter) return false;
      if (conferenceFilter && r.conference !== conferenceFilter) return false;
      if ((r.mpg ?? 0) < minMpg) return false;
      if (classFilter && (r.class_year_2026_27 ?? 'Unknown') !== classFilter) return false;
      if ((r.team_need_match ?? 0) < minTeamNeed) return false;
      if ((r.development_leverage_score ?? 0) < minLeverage) return false;
      return true;
    });
  }, [rows, positionFilter, priorityFilter, conferenceFilter, minMpg, classFilter, minTeamNeed, minLeverage]);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap justify-between gap-4">
        <div>
          <h2 className="font-display text-2xl font-bold">Development Leverage Leaderboard</h2>
          <p className="text-gray-400 text-sm mt-1">
            Which rotation players have the clearest high-value development path for their current team?{' '}
            <Link
              to="/methodology#development-leverage-score"
              className="text-illini-orange hover:underline"
            >
              See Methodology for leverage score calculation
            </Link>
            .
          </p>
        </div>
        <TeamSelect
          teams={[{ team_id: '', team_name: 'All Teams', conference: '' } as Team, ...teams]}
          value={teamFilter}
          onChange={setTeamFilter}
          label="Filter by team (optional)"
        />
      </div>

      <div className="card !p-4">
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 xl:grid-cols-7 gap-3">
          <label className="flex flex-col gap-1 text-xs text-gray-400">
            Position
            <select
              value={positionFilter}
              onChange={(e) => setPositionFilter(e.target.value)}
              className="bg-surface-card border border-surface-border rounded-lg px-3 py-2 text-sm text-gray-200"
            >
              <option value="">All positions</option>
              <option value="G">Guards</option>
              <option value="F">Wings/Forwards</option>
              <option value="C">Bigs/Centers</option>
            </select>
          </label>

          <label className="flex flex-col gap-1 text-xs text-gray-400">
            Top Priority
            <select
              value={priorityFilter}
              onChange={(e) => setPriorityFilter(e.target.value)}
              className="bg-surface-card border border-surface-border rounded-lg px-3 py-2 text-sm text-gray-200"
            >
              <option value="">All priorities</option>
              {PRIORITY_OPTIONS.map((p) => (
                <option key={p.id} value={p.id}>{p.label}</option>
              ))}
            </select>
          </label>

          <label className="flex flex-col gap-1 text-xs text-gray-400">
            Conference
            <select
              value={conferenceFilter}
              onChange={(e) => setConferenceFilter(e.target.value)}
              className="bg-surface-card border border-surface-border rounded-lg px-3 py-2 text-sm text-gray-200"
            >
              <option value="">All conferences</option>
              {conferences.map((conf) => (
                <option key={conf} value={conf}>{conf}</option>
              ))}
            </select>
          </label>

          <label className="flex flex-col gap-1 text-xs text-gray-400">
            Minutes
            <select
              value={minMpg}
              onChange={(e) => setMinMpg(Number(e.target.value))}
              className="bg-surface-card border border-surface-border rounded-lg px-3 py-2 text-sm text-gray-200"
            >
              {[10, 15, 20, 25, 30].map((mpg) => (
                <option key={mpg} value={mpg}>{mpg}+ MPG</option>
              ))}
            </select>
          </label>

          <label className="flex flex-col gap-1 text-xs text-gray-400">
            Class
            <select
              value={classFilter}
              onChange={(e) => setClassFilter(e.target.value)}
              className="bg-surface-card border border-surface-border rounded-lg px-3 py-2 text-sm text-gray-200"
            >
              <option value="">All classes</option>
              {CLASS_OPTIONS.map((cls) => (
                <option key={cls.id} value={cls.id}>{cls.label}</option>
              ))}
            </select>
          </label>

          <label className="flex flex-col gap-1 text-xs text-gray-400">
            Team Need
            <select
              value={minTeamNeed}
              onChange={(e) => setMinTeamNeed(Number(e.target.value))}
              className="bg-surface-card border border-surface-border rounded-lg px-3 py-2 text-sm text-gray-200"
            >
              <option value={0}>Any team need</option>
              {[50, 70, 85].map((need) => (
                <option key={need} value={need}>Team need ≥ {need}</option>
              ))}
            </select>
          </label>

          <label className="flex flex-col gap-1 text-xs text-gray-400">
            Leverage
            <select
              value={minLeverage}
              onChange={(e) => setMinLeverage(Number(e.target.value))}
              className="bg-surface-card border border-surface-border rounded-lg px-3 py-2 text-sm text-gray-200"
            >
              <option value={0}>All leverage</option>
              {[60, 70, 80].map((lev) => (
                <option key={lev} value={lev}>Leverage ≥ {lev}</option>
              ))}
            </select>
          </label>
        </div>
        <p className="text-xs text-gray-500 mt-3">
          Showing {filteredRows.length} of {rows.length} players.
          <span className="block mt-1">
            Class reflects projected 2026-27 roster status when available. Incoming high-school freshmen are not
            included in this player stats baseline.
          </span>
        </p>
      </div>

      <div className="card overflow-x-auto">
        <p className="mb-3 text-xs text-gray-500">{LEVERAGE_PROJ_VALUE_NOTE}</p>
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-gray-400 border-b border-surface-border">
              <th className="py-2">#</th>
              <th className="py-2">Player</th>
              <th className="py-2">Team</th>
              <th className="py-2">Conf</th>
              <th className="py-2">Pos</th>
              <th
                className="py-2"
                title="Class reflects projected 2026-27 roster status when available."
              >
                Class
              </th>
              <th className="py-2">MPG</th>
              <th className="py-2">Leverage</th>
              <th className="py-2">Top Priority</th>
              <th className="py-2">Team Need</th>
              <th className="py-2" title={PROJ_VALUE_COLUMN_TOOLTIP}>
                Proj. Value
              </th>
            </tr>
          </thead>
          <tbody>
            {filteredRows.map((r, i) => (
              <tr
                key={r.player_id}
                ref={(el) => { rowRefs.current[r.player_id] = el; }}
                className={`table-row-hover border-b border-surface-border/50 ${
                  highlightPlayer === r.player_id
                    ? 'bg-illini-orange/10 ring-1 ring-inset ring-illini-orange'
                    : ''
                }`}
              >
                <td className="py-2 text-gray-500">{i + 1}</td>
                <td>
                  <Link to={`/player/${r.player_id}`} className="text-illini-orange font-medium hover:underline">
                    {r.player_name}
                  </Link>
                </td>
                <td>{r.team_name}</td>
                <td>{r.conference}</td>
                <td>{r.position}</td>
                <td>{r.class_year_2026_27 || 'Unknown'}</td>
                <td>{r.mpg?.toFixed(1)}</td>
                <td className="font-bold text-illini-orange">{r.development_leverage_score?.toFixed(1)}</td>
                <td><span className="badge-blue">{SKILL_LABELS[r.top_priority] || r.top_priority}</span></td>
                <td>{r.team_need_match?.toFixed(0)}</td>
                <td>+{r.projected_impact?.toFixed(1)}</td>
              </tr>
            ))}
            {!filteredRows.length && (
              <tr>
                <td colSpan={11} className="py-8 text-center text-gray-500">
                  No players match the current filters.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
