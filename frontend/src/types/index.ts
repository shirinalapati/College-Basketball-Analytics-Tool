export interface Team {
  team_id: string;
  team_name: string;
  conference: string;
  season: number;
  games_played: number;
  pace: number;
  offensive_rating: number;
  defensive_rating: number;
  efg_pct: number;
  three_point_rate: number;
  turnover_rate: number;
  offensive_rebound_rate: number;
  defensive_rebound_rate: number;
  free_throw_rate: number;
  assist_rate: number;
  block_rate: number;
  steal_rate: number;
  foul_rate: number;
  data_source?: string;
}

export interface TeamNeeds {
  team_id: string;
  shooting_need: number;
  free_throw_need: number;
  ball_security_need: number;
  offensive_rebounding_need: number;
  defensive_rebounding_need: number;
  foul_discipline_need: number;
  playmaking_need: number;
  defensive_activity_need: number;
  rim_pressure_need: number;
}

export interface Player {
  player_id: string;
  player_name: string;
  team_id: string;
  position: string;
  class_year: string;
  games_played: number;
  minutes: number;
  mpg: number;
  usage_rate: number;
  points: number;
  ppg: number;
  efg_pct: number;
  ts_pct: number;
  three_point_attempts: number;
  three_point_pct: number;
  free_throw_attempts: number;
  free_throw_pct: number;
  turnover_rate: number;
  assist_rate: number;
  offensive_rebound_rate: number;
  defensive_rebound_rate: number;
  steal_rate: number;
  block_rate: number;
  foul_rate: number;
}

export interface DevelopmentPriority {
  player_id: string;
  team_id: string;
  skill_category: string;
  development_priority_score: number;
  player_improvement_opportunity: number;
  team_need_alignment: number;
  role_leverage: number;
  improvement_realism: number;
  basketball_impact_value: number;
  projected_points_added: number;
  explanation: string;
}

export interface DevelopmentBoardRow {
  player_id: string;
  player_name: string;
  position: string;
  mpg: number;
  top_priority: string;
  development_priority_score: number;
  projected_points_added: number;
  development_leverage_score: number | null;
  main_reason: string;
}

export interface LeverageRow {
  player_name: string;
  player_id: string;
  position: string;
  mpg: number;
  team_id: string;
  team_name: string;
  development_leverage_score: number;
  top_priority: string;
  projected_impact: number;
  team_need_match: number;
}

export interface OverviewData {
  teams_count: number;
  players_count: number;
  top_team_needs: { category: string; score: number }[];
  top_leverage_players: {
    player_name: string;
    team_name: string;
    development_leverage_score: number;
    top_priority: string;
  }[];
  featured_team_id: string;
  featured_team_needs: Record<string, number>;
}

export const SKILL_LABELS: Record<string, string> = {
  shooting: 'Three-Point Shooting',
  free_throw: 'Free Throw Shooting',
  ball_security: 'Ball Security',
  defensive_rebounding: 'Defensive Rebounding',
  offensive_rebounding: 'Offensive Rebounding',
  foul_discipline: 'Foul Discipline',
  playmaking: 'Playmaking',
  defensive_activity: 'Defensive Activity',
  rim_pressure: 'Rim Pressure / Finishing',
};

export const NEED_EXPLANATIONS: Record<string, string> = {
  shooting: 'Poor spacing or low three-point volume reduces offensive efficiency and floor spacing.',
  ball_security: 'High turnover rate reduces shot volume and creates transition opportunities for opponents.',
  defensive_rebounding: 'Poor defensive rebounding extends opponent possessions and second-chance opportunities.',
  foul_discipline: 'High foul rate gives opponents free points and creates rotation instability.',
  playmaking: 'Low assist rate may indicate over-reliance on iso offense and fewer open looks.',
  free_throw: 'Low free throw rate or efficiency leaves points on the table in close games.',
  offensive_rebounding: 'Weak offensive rebounding limits second-chance points and extends droughts.',
  defensive_activity: 'Low steal/block activity or poor defensive rating suggests passive team defense.',
  rim_pressure: 'Inefficient finishing or low rim pressure reduces paint scoring and free throw generation.',
};
