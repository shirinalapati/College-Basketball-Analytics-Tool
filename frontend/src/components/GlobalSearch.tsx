import { useEffect, useRef, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { api } from '../lib/api';
import type { SearchResponse, SearchResult } from '../types';

const WORKSPACE_PATHS = ['/team-needs', '/development-board', '/simulator', '/leaderboard'];

export default function GlobalSearch() {
  const location = useLocation();
  const navigate = useNavigate();
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResponse | null>(null);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const wrapRef = useRef<HTMLDivElement>(null);

  const show = WORKSPACE_PATHS.includes(location.pathname);

  useEffect(() => {
    if (!show) return;
    const q = query.trim();
    if (q.length < 2) {
      setResults(null);
      setLoading(false);
      return;
    }
    setLoading(true);
    const t = window.setTimeout(() => {
      api
        .search(q)
        .then((data) => {
          setResults(data);
          setOpen(true);
        })
        .catch(() => setResults(null))
        .finally(() => setLoading(false));
    }, 200);
    return () => window.clearTimeout(t);
  }, [query, show]);

  useEffect(() => {
    const onDoc = (e: MouseEvent) => {
      if (wrapRef.current && !wrapRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener('mousedown', onDoc);
    return () => document.removeEventListener('mousedown', onDoc);
  }, []);

  if (!show) return null;

  const goToResult = (item: SearchResult) => {
    setOpen(false);
    setQuery('');
    setResults(null);

    if (item.type === 'team') {
      const params = new URLSearchParams({ team: item.team_id });
      navigate(`${location.pathname}?${params}`);
      return;
    }

    const params = new URLSearchParams({
      team: item.team_id,
      player: item.player_id,
    });
    if (location.pathname === '/team-needs') {
      navigate(`/development-board?${params}`);
      return;
    }
    navigate(`${location.pathname}?${params}`);
  };

  const hasResults =
    results && (results.teams.length > 0 || results.players.length > 0);

  return (
    <div ref={wrapRef} className="relative w-full max-w-md min-w-[200px] flex-1">
      <label className="sr-only" htmlFor="global-search">
        Search teams and players
      </label>
      <div className="relative">
        <input
          id="global-search"
          type="search"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => results && setOpen(true)}
          placeholder="Search teams or players…"
          className="w-full bg-illini-blue-light/80 border border-surface-border rounded-lg pl-9 pr-3 py-2 text-sm text-white placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-illini-orange/60"
          autoComplete="off"
        />
        <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500 pointer-events-none" aria-hidden>
          ⌕
        </span>
        {loading && (
          <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-gray-500">…</span>
        )}
      </div>

      {open && query.trim().length >= 2 && (
        <div className="absolute z-[100] mt-1 w-full rounded-lg border border-surface-border bg-surface-card shadow-xl max-h-80 overflow-y-auto">
          {!hasResults && !loading && (
            <p className="px-3 py-4 text-sm text-gray-500">No teams or players match &quot;{query}&quot;</p>
          )}
          {results?.teams && results.teams.length > 0 && (
            <div className="py-1">
              <p className="px-3 py-1 text-xs uppercase tracking-wide text-gray-500">Teams</p>
              {results.teams.map((t) => (
                <button
                  key={t.team_id}
                  type="button"
                  onClick={() => goToResult(t)}
                  className="w-full text-left px-3 py-2 text-sm hover:bg-illini-blue-light/50 transition"
                >
                  <span className="text-white font-medium">{t.team_name}</span>
                  <span className="text-gray-500 ml-2">{t.conference}</span>
                </button>
              ))}
            </div>
          )}
          {results?.players && results.players.length > 0 && (
            <div className="py-1 border-t border-surface-border">
              <p className="px-3 py-1 text-xs uppercase tracking-wide text-gray-500">Players</p>
              {results.players.map((p) => (
                <button
                  key={p.player_id}
                  type="button"
                  onClick={() => goToResult(p)}
                  className="w-full text-left px-3 py-2 text-sm hover:bg-illini-blue-light/50 transition"
                >
                  <span className="text-illini-orange font-medium">{p.player_name}</span>
                  <span className="text-gray-500 ml-2">
                    {p.team_name}
                    {p.position ? ` · ${p.position}` : ''}
                    {p.mpg != null ? ` · ${p.mpg.toFixed(1)} MPG` : ''}
                  </span>
                </button>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
