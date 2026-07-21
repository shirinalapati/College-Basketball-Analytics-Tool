export const ORANGE = '#003087';
/** Duke royal blue — primary accent for charts and highlights */
export const BRAND_BLUE = '#001A57';
/** Readable blues on neutral dark cards (~#181a1f) */
export const CHART_BLUE = '#5B9FD4';
export const CHART_BLUE_SOFT = '#7EB8E8';
export const MUTED = '#7A9CC4';
export const GRID = '#3d556f';
export const CHART_TEXT = '#e5e7eb';
export const CHART_TICK = '#b8c4d4';

/** @deprecated Use CHART_BLUE for fills; kept so imports keep working */
export const BLUE = CHART_BLUE;

export const tooltipProps = {
  contentStyle: {
    background: '#181a1f',
    border: `1px solid ${GRID}`,
    borderRadius: 8,
    color: CHART_TEXT,
  },
  labelStyle: { color: '#f9fafb', fontWeight: 600 },
  itemStyle: { color: CHART_TEXT },
  wrapperStyle: { outline: 'none', zIndex: 20 },
};

export const legendStyle = { fontSize: 11, color: CHART_TEXT };

export const axisTick = { fill: CHART_TICK, fontSize: 10 };
export const categoryTick = { fill: CHART_TEXT, fontSize: 10 };

export const DPS_COMPONENT_COLORS = {
  opportunity: ORANGE,
  teamNeed: CHART_BLUE,
  role: CHART_BLUE_SOFT,
  realism: '#94a3b8',
  impact: '#cbd5e1',
} as const;

export const PRIORITY_BAR_COLORS = [
  ORANGE,
  CHART_BLUE,
  ORANGE,
  MUTED,
  CHART_BLUE_SOFT,
] as const;
