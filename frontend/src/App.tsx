import { Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Overview from './pages/Overview';
import TeamNeedsMap from './pages/TeamNeedsMap';
import PlayerDevelopmentBoard from './pages/PlayerDevelopmentBoard';
import PlayerProfile from './pages/PlayerProfile';
import ImprovementSimulator from './pages/ImprovementSimulator';
import LeverageLeaderboard from './pages/LeverageLeaderboard';
import Methodology from './pages/Methodology';

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Overview />} />
        <Route path="/team-needs" element={<TeamNeedsMap />} />
        <Route path="/development-board" element={<PlayerDevelopmentBoard />} />
        <Route path="/player/:playerId" element={<PlayerProfile />} />
        <Route path="/simulator" element={<ImprovementSimulator />} />
        <Route path="/leaderboard" element={<LeverageLeaderboard />} />
        <Route path="/methodology" element={<Methodology />} />
      </Routes>
    </Layout>
  );
}
