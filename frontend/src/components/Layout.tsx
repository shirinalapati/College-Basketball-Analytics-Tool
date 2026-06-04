import { Link, useLocation } from 'react-router-dom';
import { ReactNode } from 'react';
import GlobalSearch from './GlobalSearch';

const NAV = [
  { to: '/', label: 'Overview' },
  { to: '/team-needs', label: 'Team Needs' },
  { to: '/development-board', label: 'Dev Board' },
  { to: '/simulator', label: 'Simulator' },
  { to: '/leaderboard', label: 'Leverage' },
  { to: '/methodology', label: 'Methodology' },
];

export default function Layout({ children }: { children: ReactNode }) {
  const loc = useLocation();

  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b border-surface-border bg-illini-blue sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 py-3 flex flex-wrap items-center justify-between gap-3">
          <Link to="/" className="flex items-center gap-3 shrink-0">
            <div className="w-10 h-10 rounded-lg bg-illini-orange flex items-center justify-center font-display font-bold text-illini-blue text-lg">
              IQ
            </div>
            <div>
              <h1 className="font-display text-xl font-bold tracking-wide text-white">
                Development<span className="text-illini-orange">IQ</span>
              </h1>
              <p className="text-xs text-gray-400">College Basketball Player Development Engine</p>
            </div>
          </Link>
          <GlobalSearch />
          <nav className="flex flex-wrap gap-1 shrink-0">
            {NAV.map(({ to, label }) => (
              <Link
                key={to}
                to={to}
                className={`px-3 py-1.5 rounded-lg text-sm font-medium transition ${
                  loc.pathname === to
                    ? 'bg-illini-orange text-white'
                    : 'text-gray-300 hover:bg-illini-blue-light hover:text-white'
                }`}
              >
                {label}
              </Link>
            ))}
          </nav>
        </div>
      </header>
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 py-6">{children}</main>
    </div>
  );
}
