import { useEffect, useMemo, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { useTeamQuery } from '../lib/useTeamQuery';
import { api } from '../lib/api';
import { Team, DevelopmentBoardRow, DevelopmentPriority, SimulatorPresets } from '../types';
import {
  MANUAL_SIMULATOR_DESCRIPTION,
  PRIORITY_VS_UPSIDE_EXPLANATION,
  REALISTIC_TARGET_CALIBRATION,
  REALISTIC_TARGET_EXAMPLES,
  REALISTIC_TARGET_SUMMARY,
  RECOMMENDED_SCENARIO_DESCRIPTION,
  RECOMMENDED_SCENARIO_LABEL,
  RECOMMENDED_SCENARIO_RESULT_NOTE,
  SIMULATOR_CHART_NOTE,
  SIMULATOR_INTRO,
} from '../lib/projectionCopy';
import { SKILL_DEFINITIONS, SKILL_LABELS } from '../types';
import TeamSelect from '../components/TeamSelect';
import ChartCard from '../charts/ChartCard';
import { DpsBySkillChart, SimulatorImpactChart } from '../charts/AppCharts';

const SLIDER_SKILL_MAP: Record<string, string> = {
  three_point_pct_delta: 'shooting',
  free_throw_pct_delta: 'free_throw',
  turnover_reduction_pct: 'ball_security',
  foul_reduction_pct: 'foul_discipline',
  defensive_rebounding_delta: 'defensive_rebounding',
  offensive_rebounding_delta: 'offensive_rebounding',
  assist_improvement_pct: 'playmaking',
  ts_pct_improvement_pts: 'rim_pressure',
  stl_blk_improvement_pct: 'defensive_activity',
};

const SLIDERS = [
  { key: 'three_point_pct_delta', label: '3P% Improvement (pts)', max: 8, step: 0.5 },
  { key: 'free_throw_pct_delta', label: 'FT% Improvement (pts)', max: 10, step: 0.5 },
  { key: 'turnover_reduction_pct', label: 'Turnover Reduction %', max: 20, step: 1 },
  { key: 'foul_reduction_pct', label: 'Foul Reduction %', max: 20, step: 1 },
  { key: 'defensive_rebounding_delta', label: 'Def Reb Rate Δ (%)', max: 5, step: 0.5 },
  { key: 'offensive_rebounding_delta', label: 'Off Reb Rate Δ (%)', max: 5, step: 0.5 },
  { key: 'assist_improvement_pct', label: 'Playmaking Improvement %', max: 15, step: 1 },
  { key: 'ts_pct_improvement_pts', label: 'Paint / TS% Improvement (pts)', max: 5, step: 0.5 },
  { key: 'stl_blk_improvement_pct', label: 'Def Activity (STL+BLK) %', max: 25, step: 1 },
] as const;

export default function ImprovementSimulator() {
  const [searchParams] = useSearchParams();
  const [teams, setTeams] = useState<Team[]>([]);
  const [teamId, setTeamId] = useTeamQuery();
  const [players, setPlayers] = useState<DevelopmentBoardRow[]>([]);
  const [playerId, setPlayerId] = useState(() => searchParams.get('player') || '');
  const [priorities, setPriorities] = useState<DevelopmentPriority[]>([]);
  const [topPrioritySkill, setTopPrioritySkill] = useState<string | null>(null);
  const [simulatorPresets, setSimulatorPresets] = useState<SimulatorPresets | null>(null);
  const [sliders, setSliders] = useState<Record<string, number>>({});
  const [lastScenario, setLastScenario] = useState<'manual' | 'suggested'>('manual');
  const [result, setResult] = useState<{
    impacts_by_skill: Record<string, number>;
    total_projected_value: number;
  } | null>(null);

  const dpsBySlider = useMemo(() => {
    const bySkill = Object.fromEntries(priorities.map((p) => [p.skill_category, p]));
    const map: Record<string, DevelopmentPriority | undefined> = {};
    SLIDERS.forEach((s) => {
      map[s.key] = bySkill[SLIDER_SKILL_MAP[s.key]];
    });
    return map;
  }, [priorities]);

  const topDevelopmentLabel = useMemo(() => {
    if (topPrioritySkill) return SKILL_LABELS[topPrioritySkill] || topPrioritySkill;
    const sorted = [...priorities].sort(
      (a, b) => b.development_priority_score - a.development_priority_score
    );
    const top = sorted[0];
    return top ? SKILL_LABELS[top.skill_category] || top.skill_category : '—';
  }, [priorities, topPrioritySkill]);

  const highestUpsideLabel = useMemo(() => {
    if (!result?.impacts_by_skill) return '—';
    let bestSkill: string | null = null;
    let bestVal = 0;
    for (const [skill, val] of Object.entries(result.impacts_by_skill)) {
      if (val > bestVal) {
        bestVal = val;
        bestSkill = skill;
      }
    }
    return bestSkill && bestVal > 0 ? SKILL_LABELS[bestSkill] || bestSkill : '—';
  }, [result]);

  useEffect(() => {
    api.teams().then(setTeams);
  }, []);

  useEffect(() => {
    const fromUrl = searchParams.get('player');
    if (fromUrl) setPlayerId(fromUrl);
  }, [searchParams]);

  useEffect(() => {
    if (!teamId) return;
    api.developmentBoard(teamId).then((list) => {
      setPlayers(list);
      const urlPlayer = searchParams.get('player');
      if (urlPlayer && list.some((p) => p.player_id === urlPlayer)) {
        setPlayerId(urlPlayer);
      } else if (!playerId && list.length) {
        setPlayerId(list[0].player_id);
      } else if (playerId && !list.some((p) => p.player_id === playerId) && list.length) {
        setPlayerId(list[0].player_id);
      }
    });
  }, [teamId]);

  useEffect(() => {
    if (!playerId) return;
    api.player(playerId).then((data) => {
      setPriorities(data.priorities ?? []);
      setSimulatorPresets(data.simulator_presets ?? null);
      const lev = data.leverage as { top_priority?: string } | undefined;
      setTopPrioritySkill(lev?.top_priority ?? null);
    });
    const init: Record<string, number> = {};
    SLIDERS.forEach((s) => {
      init[s.key] = 0;
    });
    setSliders(init);
    setResult(null);
    setLastScenario('manual');
  }, [playerId]);

  const runSim = (inputs: Record<string, number>, scenario: 'manual' | 'suggested') => {
    if (!playerId) return;
    setLastScenario(scenario);
    api.simulate({ player_id: playerId, scenario, ...inputs }).then(setResult);
  };

  const loadSuggestedPreset = () => {
    const preset = simulatorPresets?.suggested;
    if (!preset) return;
    setSliders(preset);
    runSim(preset, 'suggested');
  };

  return (
    <div className="space-y-6">
      <h2 className="font-display text-2xl font-bold">Improvement Simulator</h2>
      <p className="text-gray-400 text-sm max-w-3xl leading-relaxed">{SIMULATOR_INTRO}</p>
      <p className="text-xs text-gray-500 max-w-3xl leading-relaxed">
        See{' '}
        <Link
          to="/methodology#load-recommended-improvement-scenario"
          className="text-illini-orange hover:underline"
        >
          Methodology
        </Link>{' '}
        for how the {RECOMMENDED_SCENARIO_LABEL} is calculated.
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
              <option key={p.player_id} value={p.player_id}>
                {p.player_name} ({p.position})
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        <div className="card space-y-5">
          {priorities.length > 0 && (
            <ChartCard
              title="Focus scores (DPS per skill)"
              caption="Higher = more worth emphasizing for this player on this roster (0–100)."
              className="!p-3 !bg-surface/50"
            >
              <DpsBySkillChart priorities={priorities} limit={9} />
            </ChartCard>
          )}

          {simulatorPresets?.bases_at_full_focus && (
            <details className="text-xs text-gray-500 rounded-lg border border-surface-border bg-surface/40 px-3 py-2">
              <summary className="cursor-pointer text-gray-400 hover:text-gray-300">
                How is the <span className="text-gray-300">realistic target</span> calculated?
              </summary>
              <p className="mt-2 text-gray-400 font-sans leading-relaxed">{REALISTIC_TARGET_CALIBRATION}</p>
              <p className="mt-2 text-gray-400 font-sans leading-relaxed">{REALISTIC_TARGET_SUMMARY}</p>
              <ul className="mt-2 space-y-1 text-gray-400 leading-relaxed list-disc pl-5">
                {REALISTIC_TARGET_EXAMPLES.map((line) => (
                  <li key={line}>{line}</li>
                ))}
              </ul>
              <p className="mt-2 text-gray-400 font-sans leading-relaxed">
                Sliders can go past the realistic target for stretch what-if scenarios. Values above the target are
                aggressive assumptions, not the model&apos;s recommendation.
              </p>
            </details>
          )}

          {SLIDERS.map((s) => {
            const pri = dpsBySlider[s.key];
            const dps = pri?.development_priority_score ?? 0;
            const fullBase = simulatorPresets?.bases_at_full_focus?.[s.key];
            return (
              <div key={s.key}>
                <div className="flex justify-between text-sm mb-1 gap-2">
                  <span>{s.label}</span>
                  <div className="flex items-center gap-3 shrink-0">
                    {fullBase != null && (
                      <span
                        className="text-xs text-gray-600 tabular-nums hidden sm:inline"
                        title="Full realistic target for this player at 100% of the recommended increment. Slider max is higher for stretch what-ifs."
                      >
                        realistic target {fullBase}
                      </span>
                    )}
                    <span
                      className="text-xs text-gray-500 tabular-nums"
                      title="Development Priority Score (DPS) for this skill"
                    >
                      Focus {dps.toFixed(0)}
                    </span>
                    <span className="text-illini-orange tabular-nums w-8 text-right">
                      {sliders[s.key] ?? 0}
                    </span>
                  </div>
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
            );
          })}
          <p className="text-xs text-gray-500 leading-relaxed">{RECOMMENDED_SCENARIO_DESCRIPTION}</p>
          <p className="text-xs text-gray-400 leading-relaxed mt-2">{MANUAL_SIMULATOR_DESCRIPTION}</p>
          <div className="flex flex-col sm:flex-row gap-2">
            <button
              type="button"
              onClick={() => runSim(sliders, 'manual')}
              className="btn-primary flex-1"
              title="Calculate using the slider values currently set by the user."
            >
              Calculate Projected Value
            </button>
            <button
              type="button"
              onClick={loadSuggestedPreset}
              className="btn-secondary text-xs sm:text-sm px-3 py-2 leading-snug"
              disabled={!simulatorPresets?.suggested}
              title="Load player-specific realistic improvements scaled by DPS rank and opportunity."
            >
              {RECOMMENDED_SCENARIO_LABEL}
            </button>
          </div>
          {result && result.total_projected_value === 0 && (
            <p className="text-xs text-gray-500">
              All sliders are at zero — move at least one slider or use {RECOMMENDED_SCENARIO_LABEL} to see
              impact.
            </p>
          )}
        </div>

        <div className="card">
          <h3 className="font-display text-lg text-illini-orange mb-4">Projected Results</h3>
          <p className="text-sm text-gray-500 leading-relaxed mb-3">{PRIORITY_VS_UPSIDE_EXPLANATION}</p>
          {result && (
            <div className="grid sm:grid-cols-2 gap-3 mb-4 text-sm">
              <div className="rounded-lg border border-surface-border bg-surface/40 px-3 py-2">
                <p className="text-[10px] uppercase tracking-wide text-gray-500 mb-0.5">
                  Top Development Priority
                </p>
                <p className="font-semibold text-white">{topDevelopmentLabel}</p>
                <p className="text-xs text-gray-500 mt-0.5">Based on adjusted DPS</p>
                {topPrioritySkill && SKILL_DEFINITIONS[topPrioritySkill] && (
                  <p className="text-xs text-gray-500 mt-1.5 leading-relaxed">
                    {SKILL_DEFINITIONS[topPrioritySkill]}
                  </p>
                )}
              </div>
              <div className="rounded-lg border border-surface-border bg-surface/40 px-3 py-2">
                <p className="text-[10px] uppercase tracking-wide text-gray-500 mb-0.5">
                  Highest Raw Point Upside
                </p>
                <p className="font-semibold text-illini-orange">{highestUpsideLabel}</p>
                <p className="text-xs text-gray-500 mt-0.5">
                  {lastScenario === 'suggested'
                    ? 'This recommended improvement scenario'
                    : 'Current slider scenario'}
                </p>
              </div>
            </div>
          )}
          {result ? (
            <>
              <p className="text-3xl font-bold mb-1">
                +{result.total_projected_value.toFixed(1)}
              </p>
              <p className="text-sm font-semibold text-gray-300 mb-1">Total Projected Value</p>
              <p className="text-xs text-gray-500 mb-4">
                Transparent points proxy from your slider inputs — not a guaranteed scoring projection.
                {lastScenario === 'suggested' && (
                  <span className="block mt-1 text-gray-500">{RECOMMENDED_SCENARIO_RESULT_NOTE}</span>
                )}
              </p>
              <p className="text-xs text-gray-500 leading-relaxed mb-3">{SIMULATOR_CHART_NOTE}</p>
              <SimulatorImpactChart impacts={result.impacts_by_skill} />
              <ul className="space-y-2 text-sm mt-4">
                {Object.entries(result.impacts_by_skill).map(([k, v]) => (
                  <li key={k} className="flex justify-between border-b border-surface-border py-2">
                    <span>{SKILL_LABELS[k] || k}</span>
                    <span className={v > 0 ? 'text-illini-orange font-semibold' : 'text-gray-500'}>
                      {v > 0 ? `+${v.toFixed(1)}` : '—'}
                    </span>
                  </li>
                ))}
              </ul>
              <p className="text-xs text-gray-500 leading-relaxed mt-3">
                <strong className="text-gray-400">Why some values are blank or +0.0:</strong> A blank means the
                scenario did not apply that skill, usually because the player had little development opportunity
                there or the slider is set to 0. A +0.0 means the model calculated a tiny positive value, but it
                rounds to 0.0 at one decimal place.
              </p>
            </>
          ) : (
            <p className="text-gray-500 text-sm">
              Results appear here after you run Calculate Projected Value or {RECOMMENDED_SCENARIO_LABEL}.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
