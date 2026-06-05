import { Team } from '../types';

interface Props {
  teams: Team[];
  value: string;
  onChange: (id: string) => void;
  label?: string;
  /** When set, renders a single empty-value option (e.g. "All Teams") instead of "Choose team". */
  allOptionLabel?: string;
}

export default function TeamSelect({
  teams,
  value,
  onChange,
  label = 'Select Team',
  allOptionLabel,
}: Props) {
  const emptyLabel = allOptionLabel ?? '— Choose team —';

  return (
    <label className="flex flex-col gap-1">
      <span className="text-sm text-gray-400">{label}</span>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="bg-surface-card border border-surface-border rounded-lg px-3 py-2 text-white min-w-[220px]"
      >
        <option value="">{emptyLabel}</option>
        {teams.map((t) => (
          <option key={t.team_id} value={t.team_id}>
            {t.team_name} ({t.conference})
          </option>
        ))}
      </select>
    </label>
  );
}
