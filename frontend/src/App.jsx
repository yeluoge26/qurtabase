import { useState, useEffect } from "react";
import QuantTerminal from "./QuantTerminal";

export default function App() {
  const [matches, setMatches] = useState([]);
  const [selectedMatch, setSelectedMatch] = useState(null);

  useEffect(() => {
    async function fetchMatches() {
      try {
        const resp = await fetch("/api/matches/live");
        if (resp.ok) {
          const data = await resp.json();
          setMatches(data);
          if (data.length > 0 && !selectedMatch) {
            setSelectedMatch(data[0].match_id || data[0].id || "demo");
          }
        }
      } catch {
        setSelectedMatch("demo");
      }
    }
    fetchMatches();
    const iv = setInterval(fetchMatches, 30000);
    return () => clearInterval(iv);
  }, []);

  return <QuantTerminal matchId={selectedMatch || "demo"} />;
}
