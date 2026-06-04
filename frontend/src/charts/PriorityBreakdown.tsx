import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import { DevelopmentPriority } from '../types';
import { SKILL_LABELS } from '../types';
import { axisTick, categoryTick, PRIORITY_BAR_COLORS, tooltipProps } from './chartTheme';

interface Props {
  priorities: DevelopmentPriority[];
  limit?: number;
}

export default function PriorityBreakdown({ priorities, limit = 5 }: Props) {
  const data = priorities.slice(0, limit).map((p) => ({
    name: (SKILL_LABELS[p.skill_category] || p.skill_category).slice(0, 12),
    dps: p.development_priority_score,
    opp: p.player_improvement_opportunity,
    need: p.team_need_alignment,
    role: p.role_leverage,
  }));

  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart data={data} layout="vertical" margin={{ left: 80 }}>
        <XAxis type="number" domain={[0, 100]} tick={axisTick} />
        <YAxis type="category" dataKey="name" tick={{ ...categoryTick, fontSize: 11 }} width={75} />
        <Tooltip {...tooltipProps} formatter={(v: number) => [v.toFixed(1), 'DPS']} />
        <Bar dataKey="dps" name="DPS" radius={[0, 4, 4, 0]}>
          {data.map((_, i) => (
            <Cell key={i} fill={PRIORITY_BAR_COLORS[i % PRIORITY_BAR_COLORS.length]} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
