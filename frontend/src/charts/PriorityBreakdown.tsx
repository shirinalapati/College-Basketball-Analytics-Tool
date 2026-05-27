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

const COLORS = ['#FF5F05', '#13294B', '#FF5F05', '#4a6fa5', '#FF5F05'];

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
        <XAxis type="number" domain={[0, 100]} tick={{ fill: '#9ca3af' }} />
        <YAxis type="category" dataKey="name" tick={{ fill: '#e5e7eb', fontSize: 11 }} width={75} />
        <Tooltip
          contentStyle={{ background: '#162236', border: '1px solid #2a3f5f' }}
          labelStyle={{ color: '#fff' }}
        />
        <Bar dataKey="dps" name="DPS" radius={[0, 4, 4, 0]}>
          {data.map((_, i) => (
            <Cell key={i} fill={COLORS[i % COLORS.length]} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
