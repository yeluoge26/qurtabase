import { useState, useEffect } from "react";
import QuantTerminal from "./QuantTerminal";
import LeagueDashboard from "./components/LeagueDashboard";

export default function App() {
  const [matches, setMatches] = useState([]);
  const [selectedMatch, setSelectedMatch] = useState(null);
  const [loading, setLoading] = useState(true);
  const [leaguePredictions, setLeaguePredictions] = useState(null);

  // Poll /api/matches/live every 30s
  useEffect(() => {
    let mounted = true;
    async function fetchMatches() {
      try {
        const resp = await fetch("/api/matches/live");
        if (resp.ok && mounted) {
          const data = await resp.json();
          setMatches(data);
          if (data.length > 0 && !selectedMatch) {
            setSelectedMatch(data[0].match_id || data[0].id);
          }
          if (selectedMatch && data.length > 0) {
            const ids = data.map(m => m.match_id || m.id);
            if (!ids.includes(selectedMatch)) {
              setSelectedMatch(data[0].match_id || data[0].id);
            }
          }
          // Clear selection if no matches
          if (data.length === 0 && selectedMatch) {
            setSelectedMatch(null);
          }
        }
      } catch {
        // API error — keep current state
      } finally {
        if (mounted) setLoading(false);
      }
    }
    fetchMatches();
    const iv = setInterval(fetchMatches, 30000);
    return () => { mounted = false; clearInterval(iv); };
  }, []);

  // Fetch league predictions when no live match
  useEffect(() => {
    if (selectedMatch) return;

    let mounted = true;
    async function fetchLeaguePredictions() {
      try {
        const resp = await fetch("/api/predictions/leagues");
        if (resp.ok && mounted) {
          setLeaguePredictions(await resp.json());
        }
      } catch { /* ignore */ }
    }
    fetchLeaguePredictions();
    const iv = setInterval(fetchLeaguePredictions, 60000);
    return () => { mounted = false; clearInterval(iv); };
  }, [selectedMatch]);

  if (loading) {
    return (
      <div style={{ background: "#0a0e17", color: "#00ffc8", minHeight: "100vh",
        display: "flex", alignItems: "center", justifyContent: "center",
        fontFamily: "'JetBrains Mono', monospace", fontSize: "14px" }}>
        <div style={{ textAlign: "center" }}>
          <div style={{ marginBottom: 12, opacity: 0.7 }}>CONNECTING TO DATA FEED...</div>
          <div style={{ fontSize: 10, color: "#6B7280", marginBottom: 12, letterSpacing: 2 }}>Powered by Techspace</div>
          <div style={{ width: 200, height: 2, background: "#1a2332", borderRadius: 1, overflow: "hidden" }}>
            <div style={{ width: "60%", height: "100%", background: "#00ffc8",
              animation: "pulse 1.5s ease-in-out infinite" }} />
          </div>
        </div>
      </div>
    );
  }

  // Live match active — show QuantTerminal
  if (selectedMatch) {
    return <QuantTerminal matchId={selectedMatch} />;
  }

  // No live match — show league prediction dashboard
  return <LeagueDashboard data={leaguePredictions} />;
}
