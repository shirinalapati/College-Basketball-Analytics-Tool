import { useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';

import { FEATURED_TEAM_ID } from './brand';

const DEFAULT_TEAM = FEATURED_TEAM_ID;
const STORAGE_KEY = 'developmentiq:selectedTeamId';

export function useTeamQuery(): [string, (id: string) => void] {
  const [params, setParams] = useSearchParams();
  const storedTeamId =
    typeof window !== 'undefined' ? window.localStorage.getItem(STORAGE_KEY) : '';
  const teamId = params.get('team') || storedTeamId || DEFAULT_TEAM;

  useEffect(() => {
    window.localStorage.setItem(STORAGE_KEY, teamId);
  }, [teamId]);

  const setTeamId = (id: string) => {
    const next = new URLSearchParams(params);
    if (id) {
      next.set('team', id);
      window.localStorage.setItem(STORAGE_KEY, id);
    } else {
      next.delete('team');
    }
    setParams(next, { replace: true });
  };

  return [teamId, setTeamId];
}
