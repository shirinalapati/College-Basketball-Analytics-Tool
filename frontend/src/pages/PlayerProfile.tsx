import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { api } from '../lib/api';
import { Player, Team, DevelopmentPriority } from '../types';
import { SKILL_LABELS } from '../types';
import DemoBanner from '../components/DemoBanner';
import PriorityBreakdown from '../charts/PriorityBreakdown';

export default function PlayerProfile() {
  const { playerId } = useParams<{ playerId: string }>();
  const [player, setPlayer] = useState<Player | null>(null);
  const [team, setTeam] = useState<Team | null>(null);
  const [priorities, setPriorities] = useState<DevelopmentPriority[]>([]);
  const [leverage, setLeverage] = useState<Record<string, unknown>>({});

  useEffect(() => {
    if (!playerId) return;
    api.player(playerId).then((r) => {
      setPlayer(r.player);
      setTeam(r.team);
      setPriorities(r.priorities);
      setLeverage(r.leverage || {});
    });
  }, [playerId]);

  if (!player) return <p className="text-gray-400">Loading player profile…</p>;

  const top3 = priorities.slice(0, 3);
  const strengths: string[] = [];
  const weaknesses: string[] = [];

  if (player.three_point_pct >= 0.36) strengths.push('Three-point shooting');
  else if (player.three_point_attempts > 40) weaknesses.push('Three-point shooting');

  if (player.turnover_rate <= 0.14) strengths.push('Ball security');
  else weaknesses.push('Turnover rate');

  if (player.defensive_rebound_rate >= 0.15) strengths.push('Defensive rebounding');
  else weaknesses.push('Defensive rebounding');

  if (player.foul_rate <= 0.04) strengths.push('Foul discipline');
  else weaknesses.push('Foul discipline');

  return (
    <div className="space-y-6">
      <DemoBanner />
      <Link to="/development-board" className="text-sm text-illini-orange hover:underline">← Development Board</Link>

      <div className="card border-l-4 border-illini-orange">
        <div className="flex flex-wrap justify-between gap-4">
          <div>
            <h2 className="font-display text-3xl font-bold">{player.player_name}</h2>
            <p className="text-gray-400">
              {team?.team_name} · {player.position} · {player.class_year} · {player.mpg} MPG
            </p>
          </div>
          <div className="text-right">
            <p className="text-xs text-gray-500">Development Leverage</p>
            <p className="text-3xl font-bold text-illini-orange">
              {(leverage.development_leverage_score as number)?.toFixed(1) ?? '—'}
            </p>
          </div>
        </div>
      </div>

      <div className="grid md:grid-cols-3 gap-4">
        <div className="card">
          <h3 className="text-sm text-gray-400 mb-2">Production</h3>
          <dl className="space-y-1 text-sm">
            <div className="flex justify-between"><dt>PPG</dt><dd>{player.ppg}</dd></div>
            <div className="flex justify-between"><dt>TS%</dt><dd>{(player.ts_pct * 100).toFixed(1)}%</dd></div>
            <div className="flex justify-between"><dt>Usage</dt><dd>{(player.usage_rate * 100).toFixed(1)}%</dd></div>
            <div className="flex justify-between"><dt>3P%</dt><dd>{(player.three_point_pct * 100).toFixed(1)}%</dd></div>
          </dl>
        </div>
        <div className="card">
          <h3 className="text-sm text-illini-orange mb-2">Strengths</h3>
          <ul className="text-sm space-y-1">
            {strengths.length ? strengths.map((s) => <li key={s}>✓ {s}</li>) : <li className="text-gray-500">No clear strengths vs peers</li>}
          </ul>
        </div>
        <div className="card">
          <h3 className="text-sm text-red-400 mb-2">Weaknesses</h3>
          <ul className="text-sm space-y-1">
            {weaknesses.map((w) => <li key={w}>△ {w}</li>)}
          </ul>
        </div>
      </div>

      <div className="card">
        <h3 className="font-display text-lg font-semibold text-illini-orange mb-4">Top 3 Development Priorities</h3>
        <div className="space-y-6">
          {top3.map((p, i) => (
            <div key={p.skill_category} className="border border-surface-border rounded-lg p-4">
              <h4 className="font-bold text-lg">
                #{i + 1} {SKILL_LABELS[p.skill_category]} — DPS {p.development_priority_score.toFixed(1)}
              </h4>
              <p className="text-gray-300 mt-2 text-sm leading-relaxed">{p.explanation}</p>
              <div className="grid grid-cols-2 md:grid-cols-5 gap-2 mt-4 text-xs">
                <div className="bg-surface rounded p-2"><span className="text-gray-500">Opportunity</span><br />{p.player_improvement_opportunity}</div>
                <div className="bg-surface rounded p-2"><span className="text-gray-500">Team Need</span><br />{p.team_need_alignment}</div>
                <div className="bg-surface rounded p-2"><span className="text-gray-500">Role</span><br />{p.role_leverage}</div>
                <div className="bg-surface rounded p-2"><span className="text-gray-500">Realism</span><br />{p.improvement_realism}</div>
                <div className="bg-surface rounded p-2"><span className="text-gray-500">Proj. Value</span><br />+{p.projected_points_added} pts</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="card">
        <h3 className="text-sm text-gray-400 mb-2">Priority Score Comparison</h3>
        <PriorityBreakdown priorities={priorities} limit={9} />
      </div>

      <Link
        to={`/simulator?player=${player.player_id}`}
        className="btn-primary inline-block"
      >
        Open Improvement Simulator →
      </Link>
    </div>
  );
}
