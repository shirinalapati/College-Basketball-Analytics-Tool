import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { api } from '../lib/api';
import { PROFILE_PROJ_VALUE_NOTE, PROJ_VALUE_COLUMN_TOOLTIP } from '../lib/projectionCopy';
import { Player, Team, DevelopmentPriority, StatRank } from '../types';
import {
  hasRimLocationData,
  hasShotProfileLayer,
  rimPressureLabel,
  SKILL_DEFINITIONS,
  SKILL_LABELS,
} from '../types';
import ChartCard from '../charts/ChartCard';
import { DpsBySkillChart, DpsSkillsComparisonChart } from '../charts/AppCharts';

/** Vs rotation pool: low opportunity = at/above peers; high = clear gap. */
const OPP_STRENGTH_MAX = 25;
const OPP_WEAKNESS_MIN = 50;

function isStrongThreePointShooter(player: Player): boolean {
  const pct = player.three_point_pct ?? 0;
  const att = player.three_point_attempts ?? 0;
  return att >= 80 && pct >= 0.34;
}

const STAT_TIPS: Record<string, string> = {
  PPG: 'Points per game — average scoring output.',
  'TS%': 'True Shooting Percentage — scoring efficiency including twos, threes, and free throws.',
  Usage: 'Usage rate — share of team possessions a player finishes while on the floor.',
  '3P%': 'Three-point percentage — made threes divided by three-point attempts.',
  BPM: 'Box Plus/Minus — points added per 100 possessions vs an average player.',
  OBPM: 'Offensive Box Plus/Minus — offensive contribution vs average.',
  DBPM: 'Defensive Box Plus/Minus — defensive contribution vs average.',
  PER: 'Player Efficiency Rating — per-minute production vs league average (15 = average).',
  'Player ORtg': 'Player offensive rating — points produced per 100 possessions (when available).',
  'Player DRtg': 'Player defensive rating — points allowed per 100 possessions (when available).',
  'WS/40': 'Win Shares per 40 minutes — contribution to team wins scaled to minutes.',
  '3PA rate': 'Share of field-goal attempts from three — spacing / shooting role.',
  FTr: 'Free throw rate — free throw attempts per field goal attempt (getting to the line).',
  'AST/TOV': 'Assist-to-turnover ratio — playmaking vs ball security.',
  '2P%': 'Two-point field-goal percentage — made twos divided by two-point attempts.',
  'F/40': 'Fouls per 40 minutes — foul discipline context.',
  'STL%': 'Steals per 100 possessions — defensive activity.',
  'BLK%': 'Blocks per 100 possessions — rim protection activity.',
  'Rim attempt rate': 'Rim attempt rate — share of field-goal attempts taken at the rim.',
  'Rim FG%': 'Rim FG% — field-goal percentage on attempts at the rim.',
  'Midrange attempt rate': 'Midrange attempt rate — share of field-goal attempts taken from midrange.',
  'Midrange FG%': 'Midrange FG% — field-goal percentage on midrange attempts.',
  'Corner 3 rate': 'Corner 3 rate — share of field-goal attempts taken from the corners.',
  'FTr (FTA/FGA)': 'Free throw rate — free throw attempts per field goal attempt.',
};

const STAT_GLOSSARY = [
  'PPG',
  'TS%',
  'Usage',
  '3P%',
  '3PA rate',
  'FTr',
  'AST/TOV',
  '2P%',
  'F/40',
  'STL%',
  'BLK%',
  'BPM',
  'OBPM',
  'DBPM',
  'PER',
  'WS/40',
  'Rim attempt rate',
  'Rim FG%',
  'Midrange attempt rate',
  'Midrange FG%',
  'Corner 3 rate',
] as const;

function fmtPct(v: number) {
  return `${(v * 100).toFixed(1)}%`;
}

function skillLabel(skill: string, player: Player) {
  if (skill === 'rim_pressure') return rimPressureLabel(player);
  return SKILL_LABELS[skill] || skill;
}

function ProductionRank({ rank }: { rank?: StatRank }) {
  if (!rank) return null;
  return <span className="ml-2 text-xs text-gray-500 whitespace-nowrap">#{rank.rank} of {rank.pool}</span>;
}

type StatTile = { label: string; value: string; rankKey?: string; tip?: string };

function StatGlossary({ open }: { open: boolean }) {
  if (!open) return null;
  return (
    <div className="card">
      <h3 className="text-sm text-gray-400 mb-3">Stat Glossary</h3>
      <dl className="grid md:grid-cols-2 gap-x-6 gap-y-2 text-xs">
        {STAT_GLOSSARY.map((label) => (
          <div key={label} className="border-b border-surface-border/40 pb-2">
            <dt className="font-semibold text-gray-300">{label}</dt>
            <dd className="text-gray-500 leading-relaxed">{STAT_TIPS[label]}</dd>
          </div>
        ))}
      </dl>
    </div>
  );
}

function ShotProfileCard({ player, statRanks }: { player: Player; statRanks: Record<string, StatRank> }) {
  if (!hasShotProfileLayer(player)) return null;
  const tracked = hasRimLocationData(player);
  const rows: StatTile[] = [];
  if (player.rim_attempt_rate != null) {
    rows.push({ label: 'Rim attempt rate', value: fmtPct(player.rim_attempt_rate), rankKey: 'rim_attempt_rate' });
  }
  if (player.rim_fg_pct != null) {
    rows.push({ label: 'Rim FG%', value: fmtPct(player.rim_fg_pct), rankKey: 'rim_fg_pct' });
  }
  if (player.midrange_attempt_rate != null) {
    rows.push({
      label: 'Midrange attempt rate',
      value: fmtPct(player.midrange_attempt_rate),
      rankKey: 'midrange_attempt_rate',
    });
  }
  if (player.midrange_fg_pct != null) {
    rows.push({ label: 'Midrange FG%', value: fmtPct(player.midrange_fg_pct), rankKey: 'midrange_fg_pct' });
  }
  if (player.three_point_attempt_rate != null) {
    rows.push({ label: '3PA rate', value: fmtPct(player.three_point_attempt_rate), rankKey: 'three_point_attempt_rate' });
  }
  if (player.corner_three_attempt_rate != null) {
    rows.push({
      label: 'Corner 3 rate',
      value: fmtPct(player.corner_three_attempt_rate),
      rankKey: 'corner_three_attempt_rate',
    });
  }
  if (player.free_throw_rate != null) {
    rows.push({ label: 'FTr (FTA/FGA)', value: fmtPct(player.free_throw_rate), rankKey: 'free_throw_rate' });
  }

  return (
    <div className="card">
      <h3 className="text-sm text-gray-400 mb-2">Shot Profile</h3>
      <p className="text-xs text-gray-500 mb-3 leading-relaxed">
        Shot-profile data is used when available to separate finishing, shot selection, and spacing role.
        When unavailable, DevelopmentIQ falls back to public efficiency proxies.
        {player.shot_profile_source === 'estimated' && (
          <span className="block mt-1 text-gray-600">
            Zone mix below is estimated from box-score totals — not tracked rim-location data.
          </span>
        )}
        {tracked && (
          <span className="block mt-1 text-illini-orange/90">
            Official rim-location data — {rimPressureLabel(player)} uses rim FG% and rim attempt rate.
          </span>
        )}
      </p>
      <dl className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-sm">
        {rows.map((s) => (
          <div key={s.label} className="bg-surface/50 rounded px-2 py-1.5">
            <dt className="text-gray-500 text-xs">{s.label}</dt>
            <dd className="font-medium text-white tabular-nums">
              {s.value}
              <ProductionRank rank={s.rankKey ? statRanks[s.rankKey] : undefined} />
            </dd>
          </div>
        ))}
      </dl>
    </div>
  );
}

function AdvancedContextCard({ player, statRanks }: { player: Player; statRanks: Record<string, StatRank> }) {
  const derived: StatTile[] = [];
  if (player.three_point_attempt_rate != null) {
    derived.push({
      label: '3PA rate',
      value: fmtPct(player.three_point_attempt_rate),
      rankKey: 'three_point_attempt_rate',
      tip: STAT_TIPS['3PA rate'],
    });
  }
  if (player.free_throw_rate != null) {
    derived.push({
      label: 'FTr',
      value: fmtPct(player.free_throw_rate),
      rankKey: 'free_throw_rate',
      tip: STAT_TIPS.FTr,
    });
  }
  if (player.assist_turnover_ratio != null) {
    derived.push({
      label: 'AST/TOV',
      value: player.assist_turnover_ratio.toFixed(2),
      rankKey: 'assist_turnover_ratio',
      tip: STAT_TIPS['AST/TOV'],
    });
  }
  if (player.two_point_pct != null) {
    derived.push({
      label: '2P%',
      value: fmtPct(player.two_point_pct),
      rankKey: 'two_point_pct',
      tip: STAT_TIPS['2P%'],
    });
  }
  if (player.fouls_per_40 != null) {
    derived.push({
      label: 'F/40',
      value: player.fouls_per_40.toFixed(1),
      rankKey: 'fouls_per_40',
      tip: STAT_TIPS['F/40'],
    });
  }
  if (player.steal_pct != null) {
    derived.push({
      label: 'STL%',
      value: `${player.steal_pct.toFixed(1)}`,
      rankKey: 'steal_pct',
      tip: STAT_TIPS['STL%'],
    });
  }
  if (player.block_pct != null) {
    derived.push({
      label: 'BLK%',
      value: `${player.block_pct.toFixed(1)}`,
      rankKey: 'block_pct',
      tip: STAT_TIPS['BLK%'],
    });
  }

  const advanced: StatTile[] = [];
  if (player.bpm != null) advanced.push({ label: 'BPM', value: player.bpm.toFixed(1), rankKey: 'bpm', tip: STAT_TIPS.BPM });
  if (player.obpm != null) advanced.push({ label: 'OBPM', value: player.obpm.toFixed(1), rankKey: 'obpm', tip: STAT_TIPS.OBPM });
  if (player.dbpm != null) advanced.push({ label: 'DBPM', value: player.dbpm.toFixed(1), rankKey: 'dbpm', tip: STAT_TIPS.DBPM });
  if (player.per != null) advanced.push({ label: 'PER', value: player.per.toFixed(1), rankKey: 'per', tip: STAT_TIPS.PER });
  if (player.player_ortg != null) {
    advanced.push({
      label: 'Player ORtg',
      value: player.player_ortg.toFixed(1),
      rankKey: 'player_ortg',
      tip: STAT_TIPS['Player ORtg'],
    });
  }
  if (player.player_drtg != null) {
    advanced.push({
      label: 'Player DRtg',
      value: player.player_drtg.toFixed(1),
      rankKey: 'player_drtg',
      tip: STAT_TIPS['Player DRtg'],
    });
  }
  const ws40 = player.win_shares_per_40 ?? player.win_shares;
  if (ws40 != null) {
    advanced.push({
      label: player.win_shares_per_40 != null ? 'WS/40' : 'Win Shares',
      value: ws40.toFixed(2),
      rankKey: player.win_shares_per_40 != null ? 'win_shares_per_40' : 'win_shares',
      tip: STAT_TIPS['WS/40'],
    });
  }

  if (!derived.length && !advanced.length) return null;

  return (
    <div className="card">
      <h3 className="text-sm text-gray-400 mb-2">Advanced Context</h3>
      <p className="text-xs text-gray-500 mb-3 leading-relaxed">
        Derived rate stats used in opportunity scoring. BPM/PER/Win Shares from Sports Reference Advanced when
        ingested for the full player pool.
      </p>
      {derived.length > 0 && (
        <dl className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-sm mb-3">
          {derived.map((s) => (
            <div key={s.label} className="bg-surface/50 rounded px-2 py-1.5">
              <dt className="text-gray-500 text-xs" title={s.tip}>
                {s.label}
              </dt>
              <dd className="font-medium text-white tabular-nums">
                {s.value}
                <ProductionRank rank={s.rankKey ? statRanks[s.rankKey] : undefined} />
              </dd>
            </div>
          ))}
        </dl>
      )}
      {advanced.length > 0 ? (
        <dl className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-sm">
          {advanced.map((s) => (
            <div key={s.label} className="bg-surface/50 rounded px-2 py-1.5">
              <dt className="text-gray-500 text-xs" title={s.tip}>
                {s.label}
              </dt>
              <dd className="font-medium text-illini-orange tabular-nums">
                {s.value}
                <ProductionRank rank={s.rankKey ? statRanks[s.rankKey] : undefined} />
              </dd>
            </div>
          ))}
        </dl>
      ) : null}
    </div>
  );
}

function strengthsAndWeaknesses(priorities: DevelopmentPriority[], player: Player) {
  const shootingOpp =
    priorities.find((p) => p.skill_category === 'shooting')?.player_improvement_opportunity ?? 100;

  const strengthLabels = new Set<string>();

  if (isStrongThreePointShooter(player) || shootingOpp <= OPP_STRENGTH_MAX) {
    strengthLabels.add(SKILL_LABELS.shooting);
  }

  priorities
    .filter(
      (p) =>
        p.skill_category !== 'shooting' &&
        p.player_improvement_opportunity <= OPP_STRENGTH_MAX
    )
    .sort((a, b) => a.player_improvement_opportunity - b.player_improvement_opportunity)
    .slice(0, 4)
    .forEach((p) => strengthLabels.add(SKILL_LABELS[p.skill_category] || p.skill_category));

  const strengths = [...strengthLabels];
  if (strengths.includes(SKILL_LABELS.shooting)) {
    const rest = strengths.filter((s) => s !== SKILL_LABELS.shooting);
    strengths.length = 0;
    strengths.push(SKILL_LABELS.shooting, ...rest);
  }

  const weaknesses = priorities
    .filter((p) => {
      if (p.skill_category === 'shooting' && (isStrongThreePointShooter(player) || shootingOpp < OPP_WEAKNESS_MIN)) {
        return false;
      }
      return p.player_improvement_opportunity >= OPP_WEAKNESS_MIN;
    })
    .sort((a, b) => b.player_improvement_opportunity - a.player_improvement_opportunity)
    .slice(0, 4)
    .map((p) => SKILL_LABELS[p.skill_category] || p.skill_category);

  return { strengths, weaknesses };
}

export default function PlayerProfile() {
  const { playerId } = useParams<{ playerId: string }>();
  const [player, setPlayer] = useState<Player | null>(null);
  const [team, setTeam] = useState<Team | null>(null);
  const [priorities, setPriorities] = useState<DevelopmentPriority[]>([]);
  const [leverage, setLeverage] = useState<Record<string, unknown>>({});
  const [statRanks, setStatRanks] = useState<Record<string, StatRank>>({});
  const [showGlossary, setShowGlossary] = useState(false);

  useEffect(() => {
    if (!playerId) return;
    api.player(playerId).then((r) => {
      setPlayer(r.player);
      setTeam(r.team);
      setPriorities(r.priorities);
      setLeverage(r.leverage || {});
      setStatRanks((r as { stat_ranks?: Record<string, StatRank> }).stat_ranks || {});
    });
  }, [playerId]);

  if (!player) return <p className="text-gray-400">Loading player profile…</p>;

  const top3 = priorities.slice(0, 3);
  const { strengths, weaknesses } = strengthsAndWeaknesses(priorities, player);

  return (
    <div className="space-y-6">
      <Link to="/development-board" className="text-sm text-illini-orange hover:underline">← Development Board</Link>

      <div className="card border-l-4 border-illini-orange">
        <div className="flex flex-wrap justify-between gap-4">
          <div>
            <h2 className="font-display text-3xl font-bold">{player.player_name}</h2>
            <p className="text-gray-400">
              {team?.team_name} · {player.position} · {player.class_year_2026_27 || 'Unknown'} · {player.mpg} MPG
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

      <div className="flex justify-end">
        <button
          type="button"
          onClick={() => setShowGlossary((open) => !open)}
          className="rounded-lg border border-surface-border bg-surface-card px-3 py-1.5 text-xs text-gray-300 hover:border-illini-orange hover:text-white"
        >
          {showGlossary ? 'Hide Glossary' : 'View Glossary'}
        </button>
      </div>
      <StatGlossary open={showGlossary} />

      <div className="grid md:grid-cols-3 gap-4">
        <div className="card">
          <h3 className="text-sm text-gray-400 mb-2">Production</h3>
          <dl className="space-y-1 text-sm">
            <div className="flex justify-between gap-3">
              <dt>PPG</dt>
              <dd className="text-right tabular-nums">{player.ppg}<ProductionRank rank={statRanks.ppg} /></dd>
            </div>
            <div className="flex justify-between gap-3">
              <dt>TS%</dt>
              <dd className="text-right tabular-nums">{(player.ts_pct * 100).toFixed(1)}%<ProductionRank rank={statRanks.ts_pct} /></dd>
            </div>
            <div className="flex justify-between gap-3">
              <dt>Usage</dt>
              <dd className="text-right tabular-nums">{(player.usage_rate * 100).toFixed(1)}%<ProductionRank rank={statRanks.usage_rate} /></dd>
            </div>
            <div className="flex justify-between gap-3">
              <dt>3P%</dt>
              <dd className="text-right tabular-nums">{(player.three_point_pct * 100).toFixed(1)}%<ProductionRank rank={statRanks.three_point_pct} /></dd>
            </div>
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
            {weaknesses.length ? (
              weaknesses.map((w) => <li key={w}>△ {w}</li>)
            ) : (
              <li className="text-gray-500">No clear weaknesses vs peers</li>
            )}
          </ul>
        </div>
      </div>

      <AdvancedContextCard player={player} statRanks={statRanks} />
      <ShotProfileCard player={player} statRanks={statRanks} />

      <div className="card">
        <h3 className="font-display text-lg font-semibold text-illini-orange mb-2">Top 3 Development Priorities</h3>
        <p className="text-xs text-gray-500 mb-4 leading-relaxed">{PROFILE_PROJ_VALUE_NOTE}</p>
        <div className="space-y-6">
          {top3.map((p, i) => (
            <div key={p.skill_category} className="border border-surface-border rounded-lg p-4">
              <h4 className="font-bold text-lg flex flex-wrap items-center gap-2">
                #{i + 1} {skillLabel(p.skill_category, player)} — DPS {p.development_priority_score.toFixed(1)}
                {i === 0 &&
                  p.skill_category === 'rim_pressure' &&
                  !hasRimLocationData(player) && (
                  <span className="text-xs font-normal text-gray-500">(proxy)</span>
                )}
                {p.actionable ? (
                  <span className="text-xs font-normal badge-blue">Actionable focus</span>
                ) : (
                  <span className="text-xs font-normal text-gray-500">Relative focus (limited gap)</span>
                )}
              </h4>
              {i === 0 && SKILL_DEFINITIONS[p.skill_category] && (
                <p className="text-xs text-gray-500 mt-1">{SKILL_DEFINITIONS[p.skill_category]}</p>
              )}
              <p className="text-gray-300 mt-2 text-sm leading-relaxed">{p.explanation}</p>
              <div className="grid grid-cols-2 md:grid-cols-5 gap-2 mt-4 text-xs">
                <div className="bg-surface rounded p-2"><span className="text-gray-500">Opportunity</span><br />{p.player_improvement_opportunity}</div>
                <div className="bg-surface rounded p-2"><span className="text-gray-500">Team Need</span><br />{p.team_need_alignment}</div>
                <div className="bg-surface rounded p-2"><span className="text-gray-500">Role</span><br />{p.role_leverage}</div>
                <div className="bg-surface rounded p-2"><span className="text-gray-500">Realism</span><br />{p.improvement_realism}</div>
                <div
                  className="bg-surface rounded p-2"
                  title={PROJ_VALUE_COLUMN_TOOLTIP}
                >
                  <span className="text-gray-500">Proj. Value</span>
                  <br />
                  {p.projected_points_added >= 0 ? '+' : ''}
                  {p.projected_points_added} pts
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="grid md:grid-cols-2 gap-4">
        <ChartCard
          title="DPS by skill (ranked)"
          caption="Development Priority Score for all nine skill categories."
          className="card"
        >
          <DpsBySkillChart priorities={priorities} limit={9} />
        </ChartCard>
        <ChartCard
          title="What drives DPS (top 5 skills)"
          caption="Stacked inputs: opportunity, team need, role, realism, impact (each 0–100 before weighting)."
          className="card"
        >
          <DpsSkillsComparisonChart priorities={priorities} limit={5} />
        </ChartCard>
      </div>

      {top3[0]?.skill_category === 'shooting' && (player.three_point_attempts ?? 0) < 30 && (
        <p className="text-xs text-illini-orange/90 rounded-lg border border-illini-orange/30 bg-illini-orange/5 px-3 py-2">
          Shooting opportunity is halved in the model ({player.three_point_attempts} season 3PA &lt; 30) — low volume
          or non-spacing role.
        </p>
      )}

      <Link
        to={`/simulator?player=${player.player_id}`}
        className="btn-primary inline-block"
      >
        Open Improvement Simulator →
      </Link>
    </div>
  );
}
