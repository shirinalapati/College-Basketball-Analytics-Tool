import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useTeamQuery } from '../lib/useTeamQuery';
import { api } from '../lib/api';
import { Team, Player } from '../types';
import { SKILL_LABELS } from '../types';
import DemoBanner from '../components/DemoBanner';
import TeamSelect from '../components/TeamSelect';

const SLIDERS = [
  { key: 'three_point_pct_delta', label: '3P% Improvement (pts)', max: 8, step: 0.5 },
  { key: 'free_throw_pct_delta', label: 'FT% Improvement (pts)', max: 10, step: 0.5 },
  { key: 'turnover_reduction_pct', label: 'Turnover Reduction %', max: 20, step: 1 },
  { key: 'foul_reduction_pct', label: 'Foul Reduction %', max: 20, step: 1 },
  { key: 'defensive_rebounding_delta', label: 'Def Reb Rate Δ (%)', max: 5, step: 0.5 },
  { key: 'offensive_rebounding_delta', label: 'Off Reb Rate Δ (%)', max: 5, step: 0.5 },
  { key: 'assist_improvement_pct', label: 'Playmaking Improvement %', max: 15, step: 1 },
] as const;

export default function ImprovementSimulator() {
  const [searchParams] = useSearchParams();
  const [teams, setTeams] = useState<Team[]>([]);
  const [teamId, setTeamId] = useTeamQuery();
  const [players, setPlayers] = useState<Player[]>([]);
  const [playerId, setPlayerId] = useState(searchParams.get('player') || '');
  const [sliders, setSliders] = useState<Record<string, number>>({});
  const [result, setResult] = useState<{
    impacts_by_skill: Record<string, number>;
    total_projected_value: number;
  } | null>(null);

  useEffect(() => {
    api.teams().then(setTeams);
  }, []);

  useEffect(() => {
    if (!teamId) return;
    api.teamPlayers(teamId).then((list: Player[]) => {
      setPlayers(list);
      if (!playerId && list.length) setPlayerId(list[0].player_id);
    });
  }, [teamId]);

  useEffect(() => {
    const init: Record<string, number> = {};
    SLIDERS.forEach((s) => { init[s.key] = 0; });
    setSliders(init);
  }, [playerId]);

  const REALISTIC_PRESET: Record<string, number> = {
    three_point_pct_delta: 4,
    free_throw_pct_delta: 7,
    turnover_reduction_pct: 10,
    foul_reduction_pct: 10,
    defensive_rebounding_delta: 2,
    offensive_rebounding_delta: 1.5,
    assist_improvement_pct: 8,
  };

  const runSim = (override?: Record<string, number>) => {
    if (!playerId) return;
    const inputs = override ?? sliders;
    api.simulate({ player_id: playerId, ...inputs }).then(setResult);
  };

  const loadPreset = () => {
    setSliders(REALISTIC_PRESET);
    runSim(REALISTIC_PRESET);
  };

  return (
    <div className="space-y-6">
      <DemoBanner />
      <h2 className="font-display text-2xl font-bold">Improvement Simulator</h2>
      <p className="text-gray-400 text-sm">
        Adjust realistic improvement scenarios and see projected seasonal point value with team context.
      </p>

      <div className="flex flex-wrap gap-4">
        <TeamSelect teams={teams} value={teamId} onChange={setTeamId} />
        <label className="flex flex-col gap-1">
          <span className="text-sm text-gray-400">Player</span>
          <select
            value={playerId}
            onChange={(e) => setPlayerId(e.target.value)}
            className="bg-surface-card border border-surface-border rounded-lg px-3 py-2 min-w-[200px]"
          >
            {players.map((p) => (
              <option key={p.player_id} value={p.player_id}>{p.player_name}</option>
            ))}
          </select>
        </label>
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        <div className="card space-y-5">
          {SLIDERS.map((s) => (
            <div key={s.key}>
              <div className="flex justify-between text-sm mb-1">
                <span>{s.label}</span>
                <span className="text-illini-orange">{sliders[s.key] ?? 0}</span>
              </div>
              <input
                type="range"
                min={0}
                max={s.max}
                step={s.step}
                value={sliders[s.key] ?? 0}
                onChange={(e) => setSliders({ ...sliders, [s.key]: parseFloat(e.target.value) })}
                className="w-full accent-illini-orange"
              />
            </div>
          ))}
          <div className="flex gap-2">
            <button type="button" onClick={() => runSim()} className="btn-primary flex-1">
              Calculate Projected Impact
            </button>
            <button type="button" onClick={loadPreset} className="btn-secondary text-sm">
              Realistic preset
            </button>
          </div>
          {result && result.total_projected_value === 0 && (
            <p className="text-xs text-gray-500">
              All sliders are at zero — move at least one slider or use &quot;Realistic preset&quot; to see impact.
            </p>
          )}
        </div>

        <div className="card">
          <h3 className="font-display text-lg text-illini-orange mb-4">Projected Results</h3>
          {result ? (
            <>
              <p className="text-3xl font-bold mb-4">
                +{result.total_projected_value.toFixed(1)}{' '}
                <span className="text-base font-normal text-gray-400">season value (pts proxy)</span>
              </p>
              <ul className="space-y-2 text-sm">
                {Object.entries(result.impacts_by_skill).map(([k, v]) => (
                  <li key={k} className="flex justify-between border-b border-surface-border py-2">
                    <span>{SKILL_LABELS[k] || k}</span>
                    <span className={v > 0 ? 'text-illini-orange font-semibold' : 'text-gray-500'}>
                      {v > 0 ? `+${v.toFixed(1)}` : '—'}
                    </span>
                  </li>
                ))}
              </ul>
              <p className="text-xs text-gray-500 mt-4">
                Estimates use transparent heuristics (3PA×Δ3P%, FTA×ΔFT%, TOV/foul/reb proxies). Supplement coaching judgment — not guaranteed projections.
              </p>
            </>
          ) : (
            <p className="text-gray-500">
              Move sliders (or click &quot;Realistic preset&quot;), then calculate to see projected seasonal value by skill.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
