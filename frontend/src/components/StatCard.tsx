interface Props {
  label: string;
  value: string | number;
  sub?: string;
  accent?: 'orange' | 'blue';
}

export default function StatCard({ label, value, sub, accent = 'orange' }: Props) {
  const border = accent === 'orange' ? 'border-illini-orange/50' : 'border-illini-blue';
  return (
    <div className={`card border-l-4 ${border}`}>
      <p className="text-xs text-gray-400 uppercase tracking-wider">{label}</p>
      <p className="text-2xl font-bold font-display mt-1">{value}</p>
      {sub && <p className="text-xs text-gray-500 mt-1">{sub}</p>}
    </div>
  );
}
