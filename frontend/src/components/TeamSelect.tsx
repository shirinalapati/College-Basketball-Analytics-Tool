import { Team } from '../types';

interface Props {
  teams: Team[];
  value: string;
  onChange: (id: string) => void;
  label?: string;
}

export default function TeamSelect({ teams, value, onChange, label = 'Select Team' }: Props) {
  return (
    <label className="flex flex-col gap-1">
      <span className="text-sm text-gray-400">{label}</span>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="bg-surface-card border border-surface-border rounded-lg px-3 py-2 text-white min-w-[220px]"
      >
        <option value="">— Choose team —</option>
        {teams.map((t) => (
          <option key={t.team_id} value={t.team_id}>
            {t.team_name} ({t.conference})
          </option>
        ))}
      </select>
    </label>
  );
}
