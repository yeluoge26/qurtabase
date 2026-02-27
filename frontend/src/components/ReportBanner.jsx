/**
 * ReportBanner — v1.1
 * Shows HT/FT report ready notification
 */

const C = {
  accent: "#F4C430",
  bgCard: "#131720",
  border: "#1E2530",
};

export default function ReportBanner({ report }) {
  if (!report) return null;

  const show = report.halfTimeReady || report.fullTimeReady;
  if (!show) return null;

  const label = report.fullTimeReady ? "FT REPORT READY" : "HT REPORT READY";

  return (
    <div
      style={{
        textAlign: "center",
        padding: "6px 0",
        fontSize: 10,
        letterSpacing: 2,
        fontWeight: 700,
        fontFamily: "mono",
        color: C.accent,
        background: C.accent + "12",
        borderTop: `1px solid ${C.accent}30`,
        borderBottom: `1px solid ${C.accent}30`,
        animation: "blink 1.5s infinite",
      }}
    >
      {label} — PRESS [R] TO EXPORT
    </div>
  );
}
