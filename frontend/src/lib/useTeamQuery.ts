import { useSearchParams } from 'react-router-dom';

const DEFAULT_TEAM = 'illinois';

export function useTeamQuery(): [string, (id: string) => void] {
  const [params, setParams] = useSearchParams();
  const teamId = params.get('team') || DEFAULT_TEAM;

  const setTeamId = (id: string) => {
    setParams(id ? { team: id } : {}, { replace: true });
  };

  return [teamId, setTeamId];
}
