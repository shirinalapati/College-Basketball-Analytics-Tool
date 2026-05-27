import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
} from 'recharts';
import { SKILL_LABELS } from '../types';

interface Props {
  needs: Record<string, number>;
}

export default function NeedsRadar({ needs }: Props) {
  const data = Object.entries(needs)
    .filter(([k]) => k.endsWith('_need'))
    .map(([k, v]) => ({
      skill: (SKILL_LABELS[k.replace('_need', '')] || k).split(' ')[0],
      score: Math.round(v),
      fullMark: 100,
    }));

  if (!data.length) return null;

  return (
    <ResponsiveContainer width="100%" height={320}>
      <RadarChart data={data}>
        <PolarGrid stroke="#2a3f5f" />
        <PolarAngleAxis dataKey="skill" tick={{ fill: '#9ca3af', fontSize: 11 }} />
        <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fill: '#6b7280' }} />
        <Radar
          name="Team Need"
          dataKey="score"
          stroke="#FF5F05"
          fill="#FF5F05"
          fillOpacity={0.35}
        />
      </RadarChart>
    </ResponsiveContainer>
  );
}
