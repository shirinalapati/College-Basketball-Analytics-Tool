import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../lib/api';
import { LeverageRow, Team } from '../types';
import { SKILL_LABELS } from '../types';
import DemoBanner from '../components/DemoBanner';
import TeamSelect from '../components/TeamSelect';

export default function LeverageLeaderboard() {
  const [rows, setRows] = useState<LeverageRow[]>([]);
  const [teams, setTeams] = useState<Team[]>([]);
  const [teamFilter, setTeamFilter] = useState('');

  useEffect(() => {
    api.teams().then(setTeams);
  }, []);

  useEffect(() => {
    api.leverageLeaderboard(75, teamFilter || undefined).then(setRows);
  }, [teamFilter]);

  return (
    <div className="space-y-6">
      <DemoBanner />
      <div className="flex flex-wrap justify-between gap-4">
        <div>
          <h2 className="font-display text-2xl font-bold">Development Leverage Leaderboard</h2>
          <p className="text-gray-400 text-sm mt-1">
            Which rotation players have the clearest high-value development path for their current team?
          </p>
        </div>
        <TeamSelect
          teams={[{ team_id: '', team_name: 'All Teams', conference: '' } as Team, ...teams]}
          value={teamFilter}
          onChange={setTeamFilter}
          label="Filter by team (optional)"
        />
      </div>

      <div className="card overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-gray-400 border-b border-surface-border">
              <th className="py-2">#</th>
              <th className="py-2">Player</th>
              <th className="py-2">Team</th>
              <th className="py-2">Pos</th>
              <th className="py-2">MPG</th>
              <th className="py-2">Leverage</th>
              <th className="py-2">Top Priority</th>
              <th className="py-2">Team Need</th>
              <th className="py-2">Proj. Impact</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r, i) => (
              <tr key={r.player_id} className="table-row-hover border-b border-surface-border/50">
                <td className="py-2 text-gray-500">{i + 1}</td>
                <td>
                  <Link to={`/player/${r.player_id}`} className="text-illini-orange font-medium hover:underline">
                    {r.player_name}
                  </Link>
                </td>
                <td>{r.team_name}</td>
                <td>{r.position}</td>
                <td>{r.mpg?.toFixed(1)}</td>
                <td className="font-bold text-illini-orange">{r.development_leverage_score?.toFixed(1)}</td>
                <td><span className="badge-blue">{SKILL_LABELS[r.top_priority] || r.top_priority}</span></td>
                <td>{r.team_need_match?.toFixed(0)}</td>
                <td>+{r.projected_impact?.toFixed(1)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
