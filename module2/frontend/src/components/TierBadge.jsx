const TIER_CONFIG = {
  green: { dot: "🟢", label: "Agent-Ready" },
  yellow: { dot: "🟡", label: "Needs Work" },
  red: { dot: "🔴", label: "Not Ready" },
};

export default function TierBadge({ tier }) {
  const config = TIER_CONFIG[tier] || TIER_CONFIG.red;
  return (
    <span className={`tier-badge ${tier}`}>
      <span>{config.dot}</span>
      {config.label}
    </span>
  );
}
