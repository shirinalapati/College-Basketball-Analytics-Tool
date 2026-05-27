export default function Methodology() {
  return (
    <div className="space-y-8 max-w-4xl">
      <h2 className="font-display text-3xl font-bold">
        Methodology & <span className="text-illini-orange">Write-Up</span>
      </h2>
      <p className="text-gray-400">
        Illinois Men&apos;s Basketball Analytics Internship — submission-ready documentation.
      </p>

      {[
        {
          title: '1. What Problem This Solves',
          body: `College basketball teams have limited practice time and player-development bandwidth. DevelopmentIQ helps identify which specific skill improvements would create the most team value, rather than evaluating player weaknesses in isolation. The central question: "Which skill improvement would create the most value for this player and this team?"`,
        },
        {
          title: '2. What Data Was Used',
          body: `Public college basketball team and player statistics structured to mirror BartTorvik, Sports Reference, and NCAA-style exports: season team efficiency (ORtg, DRtg, pace), shooting (eFG%, 3P rate), rebounding, turnovers, fouls, assists, steals/blocks, and rotation player box-score rates. Version 1 ships with labeled DEMO data (64 teams, 600+ rotation players) via a clean ingestion layer ready for live CSV/API feeds.`,
        },
        {
          title: '3. How The Solution Was Built',
          body: `Python (pandas, numpy, scikit-learn for normalization), SQLite (PostgreSQL-friendly schema), FastAPI REST API, React + TypeScript + Vite + Tailwind CSS frontend, Recharts visualizations. Scoring functions produce 0–100 normalized indices for team needs, player opportunity, and composite Development Priority Scores.`,
        },
        {
          title: '4. How The Model Works',
          body: `Development Priority Score (DPS) = 0.30×Player Improvement Opportunity + 0.30×Team Need Alignment + 0.20×Minutes/Role Leverage + 0.10×Improvement Realism + 0.10×Basketball Impact Value. Nine skill categories: three-point shooting, free throws, ball security, defensive/offensive rebounding, foul discipline, playmaking, defensive activity, rim pressure. Development Leverage Score ranks players with clearest team-relative pathways (production, upside, need match, minutes, class-year runway). Projected impact uses transparent formulas (e.g., added_points = 3PA × Δ3P% × 3).`,
        },
        {
          title: '5. Why Useful To GM / Coaching Staff',
          body: `Coaching: prioritize development plans, connect workouts to team needs, identify high-leverage skills, support practice planning. GM: roster weakness visibility, internal upside evaluation, portal/offseason planning (which gaps cannot be solved internally), ceiling-change candidates.`,
        },
        {
          title: '6. Limitations',
          body: `Public data does not capture defensive assignments, scheme, shot quality, or film context. Player development is non-linear. Improvement estimates are heuristics, not guarantees. The app supplements — not replaces — coaching judgment. Proxies used where public data is limited. Role, injuries, and lineup context affect true development value.`,
        },
        {
          title: '7. Future Improvements',
          body: `Live BartTorvik/Sports Reference ingestion, lineup-on/off context, shot-quality layers, practice-tracking integration, multi-season development curves, and opponent-specific weighting for in-season prep.`,
        },
      ].map((s) => (
        <section key={s.title} className="card">
          <h3 className="font-display text-lg font-semibold text-illini-orange mb-2">{s.title}</h3>
          <p className="text-gray-300 leading-relaxed text-sm">{s.body}</p>
        </section>
      ))}

      <p className="text-sm text-gray-500">
        Full write-up: <code className="text-illini-orange">docs/writeup.md</code> · Technical detail:{' '}
        <code className="text-illini-orange">docs/methodology.md</code>
      </p>
    </div>
  );
}
