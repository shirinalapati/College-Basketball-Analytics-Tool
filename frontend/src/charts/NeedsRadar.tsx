import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Tooltip,
} from 'recharts';
import { SKILL_ORDER, SKILL_RADAR_LABELS } from '../types';
import { axisTick, categoryTick, GRID, ORANGE, tooltipProps } from './chartTheme';

interface Props {
  needs: Record<string, number>;
}

export default function NeedsRadar({ needs }: Props) {
  const data = SKILL_ORDER.map((key) => {
    const raw = needs[`${key}_need`];
    const score = typeof raw === 'number' ? raw : Number(raw);
    return {
      skill: SKILL_RADAR_LABELS[key] || key,
      score: Number.isFinite(score) ? Math.round(score) : 0,
      fullMark: 100,
    };
  });

  if (!data.some((d) => d.score > 0)) {
    return (
      <p className="text-sm text-gray-500 py-8 text-center">
        No team need scores available for this team.
      </p>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={320}>
      <RadarChart
        cx="50%"
        cy="50%"
        outerRadius="75%"
        data={data}
        margin={{ top: 16, right: 24, bottom: 16, left: 24 }}
      >
        <PolarGrid stroke={GRID} />
        <PolarAngleAxis dataKey="skill" tick={{ ...categoryTick, fontSize: 10 }} />
        <PolarRadiusAxis angle={90} domain={[0, 100]} tick={axisTick} />
        <Tooltip
          {...tooltipProps}
          formatter={(value: number) => [`${value}`, 'Need score']}
          labelFormatter={(label) => label}
        />
        <Radar
          name="Team Need"
          dataKey="score"
          stroke={ORANGE}
          fill={ORANGE}
          fillOpacity={0.45}
          strokeWidth={2}
          dot={{ r: 3, fill: ORANGE, stroke: '#fff', strokeWidth: 1 }}
          isAnimationActive={false}
        />
      </RadarChart>
    </ResponsiveContainer>
  );
}
