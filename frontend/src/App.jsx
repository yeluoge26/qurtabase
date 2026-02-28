import { useState, useEffect } from "react";
import QuantTerminal from "./QuantTerminal";

export default function App() {
  const [matches, setMatches] = useState([]);
  const [selectedMatch, setSelectedMatch] = useState(null);
  const [loading, setLoading] = useState(true);

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
          // Clear selection if current match is no longer in the list
          if (selectedMatch && data.length > 0) {
            const ids = data.map(m => m.match_id || m.id);
            if (!ids.includes(selectedMatch)) {
              setSelectedMatch(data[0].match_id || data[0].id);
            }
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

  if (loading) {
    return (
      <div style={{ background: "#0a0e17", color: "#00ffc8", minHeight: "100vh",
        display: "flex", alignItems: "center", justifyContent: "center",
        fontFamily: "'JetBrains Mono', monospace", fontSize: "14px" }}>
        <div style={{ textAlign: "center" }}>
          <div style={{ marginBottom: 12, opacity: 0.7 }}>CONNECTING TO DATA FEED...</div>
          <div style={{ width: 200, height: 2, background: "#1a2332", borderRadius: 1, overflow: "hidden" }}>
            <div style={{ width: "60%", height: "100%", background: "#00ffc8",
              animation: "pulse 1.5s ease-in-out infinite" }} />
          </div>
        </div>
      </div>
    );
  }

  if (!selectedMatch) {
    return (
      <div style={{ background: "#0a0e17", color: "#8899aa", minHeight: "100vh",
        display: "flex", alignItems: "center", justifyContent: "center",
        fontFamily: "'JetBrains Mono', monospace", fontSize: "13px" }}>
        <div style={{ textAlign: "center", maxWidth: 420 }}>
          <div style={{ fontSize: 28, marginBottom: 16 }}>QURTABASE</div>
          <div style={{ color: "#556677", marginBottom: 24, lineHeight: 1.6 }}>
            NO LIVE MATCHES DETECTED
          </div>
          <div style={{ color: "#334455", fontSize: 11, marginBottom: 8 }}>
            Auto-scanning every 30s for live fixtures...
          </div>
          <div style={{ width: 120, height: 2, background: "#1a2332", borderRadius: 1,
            overflow: "hidden", margin: "0 auto" }}>
            <div style={{ width: "30%", height: "100%", background: "#334455",
              animation: "pulse 2s ease-in-out infinite" }} />
          </div>
          {matches.length === 0 && (
            <div style={{ marginTop: 32, color: "#334455", fontSize: 10 }}>
              Waiting for match data from AllSportsApi...
            </div>
          )}
        </div>
      </div>
    );
  }

  return <QuantTerminal matchId={selectedMatch} />;
}
