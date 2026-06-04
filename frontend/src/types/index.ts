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
  team_rim_attempt_rate?: number | null;
  team_rim_fg_pct?: number | null;
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
  /** Per-skill explanations keyed by skill id (e.g. shooting, ball_security). */
  need_explanations?: Record<string, string>;
}

export interface Player {
  player_id: string;
  player_name: string;
  team_id: string;
  position: string;
  class_year: string;
  class_year_2026_27?: string;
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
  /** FTA per FGA — player-level free throw rate (not team FTr). */
  free_throw_rate?: number | null;
  turnover_rate: number;
  assist_rate: number;
  offensive_rebound_rate: number;
  defensive_rebound_rate: number;
  steal_rate: number;
  block_rate: number;
  foul_rate: number;
  field_goal_attempts?: number | null;
  three_point_attempt_rate?: number | null;
  two_point_pct?: number | null;
  assist_turnover_ratio?: number | null;
  fouls_per_40?: number | null;
  steal_pct?: number | null;
  block_pct?: number | null;
  bpm?: number | null;
  obpm?: number | null;
  dbpm?: number | null;
  per?: number | null;
  player_ortg?: number | null;
  player_drtg?: number | null;
  win_shares?: number | null;
  win_shares_per_40?: number | null;
  shot_profile_source?: string | null;
  rim_attempts?: number | null;
  rim_makes?: number | null;
  rim_fg_pct?: number | null;
  rim_attempt_rate?: number | null;
  midrange_attempts?: number | null;
  midrange_makes?: number | null;
  midrange_fg_pct?: number | null;
  midrange_attempt_rate?: number | null;
  corner_three_attempts?: number | null;
  corner_three_makes?: number | null;
  corner_three_pct?: number | null;
  corner_three_attempt_rate?: number | null;
  above_break_three_attempts?: number | null;
  above_break_three_makes?: number | null;
  above_break_three_pct?: number | null;
  above_break_three_attempt_rate?: number | null;
  assisted_rim_rate?: number | null;
  assisted_three_rate?: number | null;
}

export interface StatRank {
  rank: number;
  pool: number;
}

const OFFICIAL_SHOT_SOURCES = new Set([
  'tracking',
  'official',
  'synergy',
  'sports_reference',
  'hoop_explorer',
]);

export function hasRimLocationData(player: Player | null | undefined): boolean {
  if (!player?.shot_profile_source) return false;
  if (!OFFICIAL_SHOT_SOURCES.has(player.shot_profile_source.toLowerCase())) return false;
  return player.rim_attempt_rate != null || player.rim_attempts != null;
}

export function rimPressureLabel(player?: Player | null): string {
  return hasRimLocationData(player)
    ? SKILL_LABELS.rim_pressure
    : 'Rim Pressure / Finishing (proxy)';
}

export function hasShotProfileLayer(player?: Player | null): boolean {
  if (!player) return false;
  return (
    player.rim_attempt_rate != null ||
    player.midrange_attempt_rate != null ||
    player.corner_three_attempt_rate != null
  );
}

export interface SimulatorPresets {
  calibration_source: string;
  dps_full_scale: number;
  bases_at_full_focus: Record<string, number>;
  suggested?: Record<string, number>;
}

export interface DevelopmentPriority {
  player_id: string;
  team_id: string;
  skill_category: string;
  development_priority_score: number;
  raw_priority_score?: number;
  position_fit_multiplier?: number;
  player_improvement_opportunity: number;
  team_need_alignment: number;
  role_leverage: number;
  improvement_realism: number;
  basketball_impact_value: number;
  projected_points_added: number;
  actionable?: number;
  explanation: string;
}

export interface DevelopmentBoardRow {
  player_id: string;
  player_name: string;
  position: string;
  class_year_2026_27: string;
  mpg: number;
  /** 2026-27 transfer portal arrival at current team */
  is_transfer_in?: boolean;
  transfer_from?: string | null;
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
  class_year_2026_27: string;
  mpg: number;
  team_id: string;
  team_name: string;
  conference: string;
  development_leverage_score: number;
  top_priority: string;
  projected_impact: number;
  team_need_match: number;
}

export interface SearchResultTeam {
  type: 'team';
  team_id: string;
  team_name: string;
  conference: string;
}

export interface SearchResultPlayer {
  type: 'player';
  player_id: string;
  player_name: string;
  team_id: string;
  team_name: string;
  conference: string;
  position: string;
  mpg: number;
}

export type SearchResult = SearchResultTeam | SearchResultPlayer;

export interface SearchResponse {
  query: string;
  teams: SearchResultTeam[];
  players: SearchResultPlayer[];
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
  roster_projection_last_updated?: string;
  roster_status_warning?: string;
}

/** Stable order for charts (matches backend SKILL_CATEGORIES). */
export const SKILL_ORDER = [
  'shooting',
  'free_throw',
  'ball_security',
  'defensive_rebounding',
  'offensive_rebounding',
  'foul_discipline',
  'playmaking',
  'defensive_activity',
  'rim_pressure',
] as const;

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

/** Use rimPressureLabel(player) when player context is available. */

/** Short unique labels for radar chart axes. */
export const SKILL_RADAR_LABELS: Record<string, string> = {
  shooting: '3PT Shooting',
  free_throw: 'Free Throws',
  ball_security: 'Ball Security',
  defensive_rebounding: 'Def. Rebounding',
  offensive_rebounding: 'Off. Rebounding',
  foul_discipline: 'Foul Discipline',
  playmaking: 'Playmaking',
  defensive_activity: 'Def. Activity',
  rim_pressure: 'Rim Pressure',
};

export const SKILL_DEFINITIONS: Record<string, string> = {
  shooting: 'Spacing and catch-and-shoot value — 3P% and volume vs position peers.',
  free_throw: 'Closing possessions at the line — FT% and how often the player gets to the stripe (FTr).',
  ball_security: 'Protecting possessions — turnover rate and assist-to-turnover vs usage.',
  defensive_rebounding: 'Ending defensive possessions — DRB% gap vs position and pool.',
  offensive_rebounding: 'Second-chance offense — ORB% (down-weighted for guards).',
  foul_discipline: 'Staying on the floor — foul rate and fouls per 40, weighted by minutes.',
  playmaking: 'Creating open looks — assist rate and AST/TOV (guards emphasized).',
  defensive_activity: 'Disrupting offense — steals and blocks, position-weighted (G/F/C).',
  rim_pressure:
    'Rim and paint scoring — rim attempt rate, rim FG%, free throw rate (FTr), and true shooting (TS%). Projected value uses a calibrated TS% increment; opportunity and team need also use efficiency at the rim when shot-profile data exists.',
};

/** Realistic-target table rows (methodology, simulator) — keyed by skill id. */
export const REALISTIC_TARGET_BY_SKILL: Record<
  (typeof SKILL_ORDER)[number],
  { increment: string; ceiling: string }
> = {
  shooting: {
    increment: '+5.0 percentage points on 3P%',
    ceiling: 'capped at high-end 3P% benchmark',
  },
  free_throw: {
    increment: '+8.0 percentage points on FT%',
    ceiling: 'capped at high-end FT% benchmark',
  },
  ball_security: {
    increment: '12% fewer turnovers',
    ceiling: 'floored at realistic low turnover level',
  },
  rim_pressure: {
    increment: '+4.5 percentage points on TS%',
    ceiling: 'capped at high-end TS% benchmark',
  },
  defensive_rebounding: {
    increment: '+0.04 DRB/G',
    ceiling: 'capped at high-end DRB/G benchmark',
  },
  offensive_rebounding: {
    increment: '+0.02 ORB/G',
    ceiling: 'capped at high-end ORB/G benchmark',
  },
  playmaking: {
    increment: '+0.04 AST/G',
    ceiling: 'capped at high-end AST/G benchmark',
  },
  defensive_activity: {
    increment: '+0.025 STL+BLK/G',
    ceiling: 'capped at high-end STL+BLK/G benchmark',
  },
  foul_discipline: {
    increment: '12% fewer fouls',
    ceiling: 'floored at realistic low foul level',
  },
};

/** One-line projected-value examples per skill (methodology bullets). */
export const PROJ_VALUE_EXAMPLE_BY_SKILL: Record<(typeof SKILL_ORDER)[number], string> = {
  shooting: 'extra made shots from improved percentage and attempt volume',
  free_throw: 'extra points from improved FT% and FTA volume',
  ball_security: 'turnovers prevented × possession value',
  defensive_rebounding: 'extra defensive rebounds × possession value',
  offensive_rebounding: 'extra offensive rebounds × possession value',
  playmaking: 'extra assists × estimated point value',
  defensive_activity: 'extra steals/blocks × possession value',
  rim_pressure: 'scoring volume × true shooting (TS%) gain in the paint and at the rim',
  foul_discipline: 'fouls prevented × possession value',
};

/** Comma-separated list of all nine display names (glossary, methodology intros). */
export const NINE_SKILL_NAMES_LIST = SKILL_ORDER.map((k) => SKILL_LABELS[k]).join(', ');

export const NEED_EXPLANATIONS: Record<string, string> = {
  shooting: 'Poor spacing or low three-point volume reduces offensive efficiency and floor spacing.',
  ball_security: 'High turnover rate reduces shot volume and creates transition opportunities for opponents.',
  defensive_rebounding: 'Poor defensive rebounding extends opponent possessions and second-chance opportunities.',
  foul_discipline: 'High foul rate gives opponents free points and creates rotation instability.',
  playmaking: 'Low assist rate may indicate over-reliance on iso offense and fewer open looks.',
  free_throw: 'Low free throw rate or efficiency leaves points on the table in close games.',
  offensive_rebounding: 'Weak offensive rebounding limits second-chance points and extends droughts.',
  defensive_activity: 'Low steal/block activity or poor defensive rating suggests passive team defense.',
  rim_pressure:
    'Inefficient finishing or low rim pressure reduces paint scoring and free throw generation.',
};
