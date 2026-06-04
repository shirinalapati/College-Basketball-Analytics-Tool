import type { ReactNode } from 'react';

interface Props {
  title: string;
  caption?: string;
  children: ReactNode;
  className?: string;
}

export default function ChartCard({ title, caption, children, className = '' }: Props) {
  return (
    <div className={`rounded-lg border border-surface-border bg-surface/40 p-4 ${className}`}>
      <p className="text-xs font-semibold text-gray-300 mb-3">{title}</p>
      {children}
      {caption ? <p className="text-xs text-gray-500 mt-2">{caption}</p> : null}
    </div>
  );
}
