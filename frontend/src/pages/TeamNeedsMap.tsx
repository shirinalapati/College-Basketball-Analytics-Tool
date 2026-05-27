import { useEffect, useState } from 'react';
import { api } from '../lib/api';
import { Team, TeamNeeds } from '../types';
import { SKILL_LABELS, NEED_EXPLANATIONS } from '../types';
import { useTeamQuery } from '../lib/useTeamQuery';
import DemoBanner from '../components/DemoBanner';
import TeamSelect from '../components/TeamSelect';
import NeedsRadar from '../charts/NeedsRadar';
import ApiError from '../components/ApiError';

export default function TeamNeedsMap() {
  const [teams, setTeams] = useState<Team[]>([]);
  const [teamId, setTeamId] = useTeamQuery();
  const [team, setTeam] = useState<Team | null>(null);
  const [needs, setNeeds] = useState<TeamNeeds | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    api.teams().then(setTeams).catch((e) => setError(e.message));
  }, []);

  useEffect(() => {
    if (!teamId) return;
    setError('');
    api
      .team(teamId)
      .then((r) => {
        setTeam(r.team);
        setNeeds(r.needs as TeamNeeds);
      })
      .catch((e) => setError(e.message));
  }, [teamId]);

  const ranked = needs
    ? Object.entries(needs)
        .filter(([k]) => k.endsWith('_need'))
        .map(([k, v]) => ({
          key: k.replace('_need', ''),
          score: v as number,
          label: SKILL_LABELS[k.replace('_need', '')] || k,
        }))
        .sort((a, b) => b.score - a.score)
    : [];

  return (
    <div className="space-y-6">
      <DemoBanner />
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h2 className="font-display text-2xl font-bold">Team Needs Map</h2>
          <p className="text-gray-400 text-sm mt-1">
            Ranked weaknesses that weight player development priorities on this roster.
          </p>
        </div>
        <TeamSelect teams={teams} value={teamId} onChange={setTeamId} />
      </div>

      {error && <ApiError message={error} />}

      {team && !error && (
        <>
          <div className="grid md:grid-cols-3 gap-4">
            <div className="card md:col-span-1">
              <h3 className="font-display text-lg text-illini-orange">{team.team_name}</h3>
              <p className="text-sm text-gray-400">{team.conference} · {team.season}</p>
              <dl className="mt-4 space-y-2 text-sm">
                <div className="flex justify-between"><dt className="text-gray-500">Off Rtg</dt><dd>{team.offensive_rating?.toFixed(1)}</dd></div>
                <div className="flex justify-between"><dt className="text-gray-500">Def Rtg</dt><dd>{team.defensive_rating?.toFixed(1)}</dd></div>
                <div className="flex justify-between"><dt className="text-gray-500">Pace</dt><dd>{team.pace?.toFixed(1)}</dd></div>
                <div className="flex justify-between"><dt className="text-gray-500">eFG%</dt><dd>{(team.efg_pct * 100).toFixed(1)}%</dd></div>
                <div className="flex justify-between"><dt className="text-gray-500">TOV Rate</dt><dd>{(team.turnover_rate * 100).toFixed(1)}%</dd></div>
                <div className="flex justify-between"><dt className="text-gray-500">Def Reb%</dt><dd>{(team.defensive_rebound_rate * 100).toFixed(1)}%</dd></div>
              </dl>
            </div>
            <div className="card md:col-span-2">
              <h3 className="text-sm text-gray-400 mb-2">Team Needs Radar</h3>
              {needs && <NeedsRadar needs={needs as unknown as Record<string, number>} />}
            </div>
          </div>

          <div className="card">
            <h3 className="font-display text-lg font-semibold mb-4">Ranked Team Needs</h3>
            <div className="space-y-4">
              {ranked.map((n, i) => (
                <div key={n.key} className="border-l-4 border-illini-orange pl-4 py-2">
                  <h4 className="font-semibold text-white">
                    {i + 1}. {n.label} — <span className="text-illini-orange">{Math.round(n.score)}</span>
                  </h4>
                  <p className="text-sm text-gray-400 mt-1">
                    {NEED_EXPLANATIONS[n.key] || 'Team-relative need score based on public efficiency metrics.'}
                  </p>
                  <div className="mt-2 h-2 bg-surface rounded-full overflow-hidden">
                    <div
                      className="h-full bg-illini-orange rounded-full"
                      style={{ width: `${Math.min(100, n.score)}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
