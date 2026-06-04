import { REALISTIC_TARGET_BY_SKILL, SKILL_LABELS, SKILL_ORDER } from '../types';

/** User-facing copy for Projected Value and the Improvement Simulator (shared across tabs). */

export const RECOMMENDED_SCENARIO_LABEL = 'Load Recommended Improvement Scenario';

export const PROJECTED_VALUE_SUMMARY =
  'Projected Value estimates the rough season value of improving a skill by a realistic amount, in point terms. It is separate from DPS: DPS picks the best development priority; Projected Value estimates the possible size of the gain if that skill improves.';

export const REALISTIC_TARGET_CALIBRATION =
  'A realistic target is based on the 75th percentile of positive year-over-year improvement among returning rotation players from 2024–25 to 2025–26. In other words, it uses a strong but historically observed one-season jump, not an average gain and not an extreme outlier. The target is then capped by a high-end ceiling, the 90th percentile current-season level for that stat, so the model does not project unrealistic outcomes. Each skill has its own fixed calibrated increment in the pool; projected value is computed for all nine skills when ranking development priorities, but the Dev Board shows Proj. Value only for the player’s Top Priority skill.';

export const DEV_BOARD_PROJ_VALUE_HEADLINE =
  'If this skill improves by the model’s realistic target, about how much value could it create?';

export const DEV_BOARD_PROJ_VALUE_NOTE =
  'Proj. Value on the Dev Board is shown once per player for the selected Top Priority skill only — not for all nine skills.';

export const LEVERAGE_PROJ_VALUE_NOTE =
  'Proj. Value reflects a realistic one-season improvement for that player’s Top Priority skill.';

export const PROFILE_PROJ_VALUE_NOTE =
  'Proj. Value here uses each skill’s realistic improvement target. The Dev Board column shows Proj. Value for Top Priority only.';

export const PROJ_VALUE_COLUMN_TOOLTIP =
  'Rough season points if the player improves by a realistic amount in that skill.';

export const SIMULATOR_INTRO =
  'Nine sliders match the nine skill categories. Set what-if improvements and play around with the slider values, then press Calculate Projected Value to see the results. These manual sliders are your own scenario; the recommended scenario is player-specific and scaled by development priority and opportunity for each skill.';

export const RECOMMENDED_SCENARIO_DESCRIPTION = `${RECOMMENDED_SCENARIO_LABEL} fills the sliders with player-specific realistic improvements. It starts with the calibrated increment for each skill, then scales by adjusted DPS rank and Player Improvement Opportunity. Top priorities with real gaps get larger suggested changes; lower-priority or low-opportunity skills get smaller or zero changes.`;

export const MANUAL_SIMULATOR_DESCRIPTION =
  'Calculate Projected Value uses the slider values on screen. Manual sliders are user-controlled what-if scenarios — they do not have to match the recommended scenario.';

export const PRIORITY_VS_UPSIDE_EXPLANATION =
  'Top Development Priority is based on adjusted DPS and actionability. Highest Raw Point Upside is the largest projected value in the current slider scenario. These can differ because high-volume scoring skills can produce more raw points while another skill may still be the better development priority.';

export const SIMULATOR_CHART_NOTE =
  `Projected value is a what-if estimate from your slider scenario. High-volume skills, especially ${SKILL_LABELS.shooting}, can show large point totals from small percentage gains across many attempts.`;

export const REALISTIC_TARGET_SUMMARY =
  'A realistic target is the model’s calibrated one-season improvement for a skill, based on year-over-year gains from returning college players, then capped by a ceiling or floor so outcomes stay plausible.';

export const REALISTIC_TARGET_EXAMPLES = [
  'Three-point shooting: about +5 percentage points on 3P%, capped at a high-end benchmark.',
  'Free throws: about +8 percentage points on FT%, capped at a high-end benchmark.',
  'Ball security / foul discipline: about a 12% reduction, floored at a realistic low level.',
  'Rebounding, playmaking, defensive activity: small per-game improvements scaled to the player’s current role.',
  'Paint pressure: about +4.5 percentage points on TS%, capped at a high-end benchmark.',
] as const;

export const RECOMMENDED_SCENARIO_RESULT_NOTE =
  'The recommended scenario may count less projected value for skills with small opportunity gaps.';
