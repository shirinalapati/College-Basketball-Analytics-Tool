import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
  PieChart,
  Pie,
  Legend,
} from 'recharts';
import { DevelopmentBoardRow, DevelopmentPriority } from '../types';
import { SKILL_LABELS } from '../types';
import ChartCard from './ChartCard';
import {
  axisTick,
  categoryTick,
  DPS_COMPONENT_COLORS,
  legendStyle,
  MUTED,
  ORANGE,
  CHART_BLUE,
  tooltipProps,
} from './chartTheme';

const DPS_WEIGHTS = [
  { name: 'Opportunity', value: 30, fill: DPS_COMPONENT_COLORS.opportunity },
  { name: 'Team need', value: 30, fill: DPS_COMPONENT_COLORS.teamNeed },
  { name: 'Role (MPG)', value: 20, fill: DPS_COMPONENT_COLORS.role },
  { name: 'Realism', value: 10, fill: DPS_COMPONENT_COLORS.realism },
  { name: 'Impact', value: 10, fill: DPS_COMPONENT_COLORS.impact },
];

/** DPS formula weights — used on Overview and Methodology */
export function DpsWeightDonut({ compact = false }: { compact?: boolean }) {
  const height = compact ? 160 : 200;
  const inner = compact ? 36 : 48;
  const outer = compact ? 58 : 72;
  return (
    <>
      <ResponsiveContainer width="100%" height={height}>
        <PieChart margin={{ top: 4, bottom: 4 }}>
          <Pie
            data={DPS_WEIGHTS}
            dataKey="value"
            nameKey="name"
            cx="50%"
            cy="48%"
            innerRadius={inner}
            outerRadius={outer}
            paddingAngle={2}
            label={compact ? false : ({ value }) => `${value}%`}
          >
            {DPS_WEIGHTS.map((d, i) => (
              <Cell key={i} fill={d.fill} />
            ))}
          </Pie>
          <Tooltip
            {...tooltipProps}
            formatter={(v: number, _n: string, p: { payload?: { name: string } }) => [
              `${v}% of DPS`,
              p.payload?.name ?? 'Weight',
            ]}
          />
        </PieChart>
      </ResponsiveContainer>
      <div className="flex flex-wrap justify-center gap-x-4 gap-y-1.5 mt-2 pt-2 border-t border-surface-border">
        {DPS_WEIGHTS.map((d) => (
          <span key={d.name} className="flex items-center gap-1.5 text-[10px] text-gray-300">
            <span className="w-2.5 h-2.5 rounded-sm shrink-0" style={{ backgroundColor: d.fill }} />
            {d.name}
          </span>
        ))}
      </div>
    </>
  );
}

export function DpsWeightCard({ compact }: { compact?: boolean }) {
  return (
    <ChartCard
      title="What goes into DPS (per player, per skill)"
      caption="Player + team stats drive 80%; fixed priors are 20%."
    >
      <DpsWeightDonut compact={compact} />
    </ChartCard>
  );
}

interface NeedItem {
  key: string;
  label: string;
  score: number;
}

export function TeamNeedsBarChart({ items, limit = 9 }: { items: NeedItem[]; limit?: number }) {
  const data = [...items]
    .sort((a, b) => b.score - a.score)
    .slice(0, limit)
    .map((n) => ({
      name: n.label.length > 18 ? `${n.label.slice(0, 16)}…` : n.label,
      fullName: n.label,
      score: Math.round(n.score),
    }));

  if (!data.length) {
    return <p className="text-sm text-gray-500 py-6 text-center">No need scores to chart.</p>;
  }

  return (
    <ResponsiveContainer width="100%" height={Math.max(252, data.length * 28)}>
      <BarChart data={data} layout="vertical" margin={{ left: 4, right: 16 }}>
        <XAxis type="number" domain={[0, 100]} tick={axisTick} />
        <YAxis type="category" dataKey="name" tick={categoryTick} width={112} />
        <Tooltip
          {...tooltipProps}
          formatter={(v: number) => [v, 'Need score']}
          labelFormatter={(_l, payload) =>
            (payload?.[0]?.payload as { fullName?: string })?.fullName ?? _l
          }
        />
        <Bar dataKey="score" name="Need" fill={ORANGE} radius={[0, 4, 4, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}

interface LeverageItem {
  name: string;
  score: number;
  sub?: string;
}

export function LeverageBarChart({ items, limit = 12 }: { items: LeverageItem[]; limit?: number }) {
  const data = items.slice(0, limit).map((r, i) => ({
    rank: i + 1,
    name: r.name.length > 18 ? `${r.name.slice(0, 16)}…` : r.name,
    fullName: r.name,
    sub: r.sub,
    score: r.score,
  }));

  if (!data.length) {
    return <p className="text-sm text-gray-500 py-6 text-center">No leverage scores to chart.</p>;
  }

  return (
    <ResponsiveContainer width="100%" height={Math.max(240, data.length * 32)}>
      <BarChart data={data} layout="vertical" margin={{ left: 4, right: 16 }}>
        <XAxis type="number" domain={[0, 100]} tick={axisTick} />
        <YAxis type="category" dataKey="name" tick={categoryTick} width={110} />
        <Tooltip
          {...tooltipProps}
          formatter={(v: number) => [v.toFixed(1), 'Leverage']}
          labelFormatter={(_l, payload) => {
            const p = payload?.[0]?.payload as { fullName?: string; sub?: string };
            return p?.sub ? `${p.fullName} · ${p.sub}` : p?.fullName ?? _l;
          }}
        />
        <Bar dataKey="score" name="Leverage" fill={ORANGE} radius={[0, 4, 4, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}

export function DevBoardDpsChart({ board }: { board: DevelopmentBoardRow[] }) {
  const data = [...board]
    .sort((a, b) => b.development_priority_score - a.development_priority_score)
    .map((r) => ({
      name: r.player_name.split(' ').pop() ?? r.player_name,
      fullName: r.player_name,
      dps: Number(r.development_priority_score?.toFixed(1)),
      priority: SKILL_LABELS[r.top_priority] || r.top_priority,
    }));

  if (!data.length) {
    return <p className="text-sm text-gray-500 py-6 text-center">Select a team to see DPS by player.</p>;
  }

  return (
    <ResponsiveContainer width="100%" height={Math.max(200, data.length * 32)}>
      <BarChart data={data} layout="vertical" margin={{ left: 4, right: 12 }}>
        <XAxis type="number" domain={[0, 100]} tick={axisTick} />
        <YAxis type="category" dataKey="name" tick={{ ...categoryTick, fontSize: 11 }} width={72} />
        <Tooltip
          {...tooltipProps}
          formatter={(v: number) => [v, 'Top-priority DPS']}
          labelFormatter={(_l, payload) => {
            const p = payload?.[0]?.payload as { fullName?: string; priority?: string };
            return `${p?.fullName} — ${p?.priority}`;
          }}
        />
        <Bar dataKey="dps" name="DPS" fill={ORANGE} radius={[0, 4, 4, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}

/** Stacked-style comparison: DPS + five inputs for top skills */
export function DpsSkillsComparisonChart({
  priorities,
  limit = 5,
}: {
  priorities: DevelopmentPriority[];
  limit?: number;
}) {
  const data = priorities.slice(0, limit).map((p) => ({
    name: (SKILL_LABELS[p.skill_category] || p.skill_category).slice(0, 14),
    fullName: SKILL_LABELS[p.skill_category] || p.skill_category,
    dps: p.development_priority_score,
    opportunity: p.player_improvement_opportunity,
    teamNeed: p.team_need_alignment,
    role: p.role_leverage,
    realism: p.improvement_realism,
    impact: p.basketball_impact_value,
  }));

  if (!data.length) return null;

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={data} margin={{ bottom: 8 }}>
        <XAxis dataKey="name" tick={{ ...axisTick, fontSize: 9 }} interval={0} angle={-25} textAnchor="end" height={56} />
        <YAxis domain={[0, 100]} tick={axisTick} />
        <Tooltip
          {...tooltipProps}
          labelFormatter={(_l, payload) =>
            (payload?.[0]?.payload as { fullName?: string })?.fullName ?? _l
          }
        />
        <Legend wrapperStyle={legendStyle} />
        <Bar dataKey="opportunity" name="Opportunity" stackId="c" fill={DPS_COMPONENT_COLORS.opportunity} />
        <Bar dataKey="teamNeed" name="Team need" stackId="c" fill={DPS_COMPONENT_COLORS.teamNeed} />
        <Bar dataKey="role" name="Role" stackId="c" fill={DPS_COMPONENT_COLORS.role} />
        <Bar dataKey="realism" name="Realism" stackId="c" fill={DPS_COMPONENT_COLORS.realism} />
        <Bar dataKey="impact" name="Impact" stackId="c" fill={DPS_COMPONENT_COLORS.impact} radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}

export function DpsBySkillChart({
  priorities,
  limit = 9,
}: {
  priorities: DevelopmentPriority[];
  limit?: number;
}) {
  const data = priorities.slice(0, limit).map((p) => ({
    name: (SKILL_LABELS[p.skill_category] || p.skill_category).slice(0, 12),
    fullName: SKILL_LABELS[p.skill_category] || p.skill_category,
    dps: p.development_priority_score,
  }));

  return (
    <ResponsiveContainer width="100%" height={Math.max(220, data.length * 26)}>
      <BarChart data={data} layout="vertical" margin={{ left: 4, right: 12 }}>
        <XAxis type="number" domain={[0, 100]} tick={axisTick} />
        <YAxis type="category" dataKey="name" tick={{ ...categoryTick, fontSize: 11 }} width={95} />
        <Tooltip
          {...tooltipProps}
          formatter={(v: number) => [v.toFixed(1), 'DPS']}
          labelFormatter={(_l, payload) =>
            (payload?.[0]?.payload as { fullName?: string })?.fullName ?? _l
          }
        />
        <Bar dataKey="dps" name="DPS" radius={[0, 4, 4, 0]}>
          {data.map((_, i) => (
            <Cell key={i} fill={i === 0 ? ORANGE : i % 2 === 0 ? MUTED : CHART_BLUE} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

export function SimulatorImpactChart({
  impacts,
  title = 'Projected Value by Skill',
}: {
  impacts: Record<string, number>;
  title?: string;
}) {
  const data = Object.entries(impacts)
    .filter(([, v]) => v > 0)
    .map(([k, v]) => ({
      name: (SKILL_LABELS[k] || k).slice(0, 14),
      fullName: SKILL_LABELS[k] || k,
      pts: v,
    }))
    .sort((a, b) => b.pts - a.pts);

  if (!data.length) {
    return <p className="text-sm text-gray-500">Move a slider to see projected value by skill.</p>;
  }

  return (
    <div className="space-y-2">
      <p className="text-sm font-semibold text-gray-300">{title}</p>
      <ResponsiveContainer width="100%" height={Math.max(180, data.length * 32)}>
      <BarChart data={data} layout="vertical" margin={{ left: 4, right: 12 }}>
        <XAxis type="number" tick={axisTick} />
        <YAxis type="category" dataKey="name" tick={categoryTick} width={100} />
        <Tooltip
          {...tooltipProps}
          formatter={(v: number) => [`+${v.toFixed(1)}`, 'Pts proxy']}
          labelFormatter={(_l, payload) =>
            (payload?.[0]?.payload as { fullName?: string })?.fullName ?? _l
          }
        />
        <Bar dataKey="pts" name="Projected" fill={ORANGE} radius={[0, 4, 4, 0]} />
      </BarChart>
    </ResponsiveContainer>
    </div>
  );
}
