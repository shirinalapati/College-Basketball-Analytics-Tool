import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../lib/api';
import { OverviewData } from '../types';
import { SKILL_LABELS, NEED_EXPLANATIONS } from '../types';
import DemoBanner from '../components/DemoBanner';
import StatCard from '../components/StatCard';
import ApiError from '../components/ApiError';

export default function Overview() {
  const [data, setData] = useState<OverviewData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    api
      .overview()
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p className="text-gray-400">Loading overview…</p>;
  if (error) return <ApiError message={error} />;
  if (!data) return <p className="text-red-400">Failed to load overview.</p>;

  const illiniNeeds = data.featured_team_needs
    ? Object.entries(data.featured_team_needs)
        .filter(([k]) => k.endsWith('_need'))
        .map(([k, v]) => ({
          key: k.replace('_need', ''),
          score: v as number,
          label: SKILL_LABELS[k.replace('_need', '')] || k,
        }))
        .sort((a, b) => b.score - a.score)
        .slice(0, 3)
    : [];

  return (
    <div className="space-y-6">
      <DemoBanner />
      <section className="card border-l-4 border-illini-orange">
        <h2 className="font-display text-2xl font-bold text-white mb-2">
          Player Development Decision Support
        </h2>
        <p className="text-gray-300 leading-relaxed max-w-3xl">
          DevelopmentIQ is a college basketball player-development decision-support tool. It identifies
          which player-skill improvements would create the most value for a team by combining player
          weaknesses, team needs, role/minutes leverage, improvement realism, and basketball impact.
        </p>
        <p className="mt-3 text-sm text-illini-orange font-medium">
          Central question: Which skill improvement would create the most value for this player and this team?
        </p>
      </section>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard label="Teams" value={data.teams_count} sub="Curated high-major universe" />
        <StatCard label="Rotation Players" value={data.players_count} sub="≥10 MPG or 250 min" accent="blue" />
        <StatCard label="Skill Categories" value={9} sub="Team-relative priorities" />
        <StatCard label="Season" value="2024-25" sub="Demo dataset" accent="blue" />
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        <div className="card">
          <h3 className="font-display text-lg font-semibold text-illini-orange mb-3">
            Top Team Needs (Dataset Average)
          </h3>
          <ul className="space-y-2">
            {data.top_team_needs.map((n, i) => (
              <li key={n.category} className="flex justify-between items-center py-2 border-b border-surface-border last:border-0">
                <span className="text-gray-300">
                  {i + 1}. {SKILL_LABELS[n.category] || n.category}
                </span>
                <span className="font-bold text-illini-orange">{n.score}</span>
              </li>
            ))}
          </ul>
        </div>

        <div className="card">
          <h3 className="font-display text-lg font-semibold text-illini-orange mb-3">
            Development Leverage Leaders
          </h3>
          <ul className="space-y-2">
            {data.top_leverage_players.slice(0, 8).map((p, i) => (
              <li key={i} className="flex justify-between text-sm py-1.5 border-b border-surface-border/50">
                <span>
                  <span className="text-white font-medium">{p.player_name}</span>
                  <span className="text-gray-500 ml-2">{p.team_name}</span>
                </span>
                <span className="text-illini-orange font-semibold">
                  {p.development_leverage_score?.toFixed(0)}
                </span>
              </li>
            ))}
          </ul>
          <Link to="/leaderboard" className="inline-block mt-4 text-sm text-illini-orange hover:underline">
            View full leaderboard →
          </Link>
        </div>
      </div>

      <section className="card bg-illini-blue/40 border-illini-orange/30">
        <h3 className="font-display text-xl font-bold mb-2">
          Featured: <span className="text-illini-orange">Illinois Fighting Illini</span>
        </h3>
        <p className="text-gray-300 text-sm mb-4">
          Explore how team needs shape player development priorities for the program you are applying to support.
        </p>
        {illiniNeeds.length > 0 && (
          <ul className="mb-4 space-y-2 text-sm">
            {illiniNeeds.map((n, i) => (
              <li key={n.key} className="text-gray-300">
                <span className="text-illini-orange font-semibold">{i + 1}. {n.label}</span>
                {' '}(need score {Math.round(n.score)}) —{' '}
                {NEED_EXPLANATIONS[n.key]?.slice(0, 90)}…
              </li>
            ))}
          </ul>
        )}
        <div className="flex flex-wrap gap-3">
          <Link to="/team-needs?team=illinois" className="btn-primary text-sm">
            Illinois Team Needs Map
          </Link>
          <Link to="/development-board?team=illinois" className="btn-secondary text-sm">
            Illinois Development Board
          </Link>
        </div>
      </section>
    </div>
  );
}
