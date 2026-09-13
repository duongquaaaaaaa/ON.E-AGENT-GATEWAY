export default function ScoreBar({ score, showLabel = true }) {
  const tier = score >= 80 ? "green" : score >= 50 ? "yellow" : "red";
  return (
    <div className="score-bar-container">
      <div className="score-bar-track">
        <div
          className={`score-bar-fill ${tier}`}
          style={{ width: `${Math.min(100, Math.max(0, score))}%` }}
        />
      </div>
      {showLabel && (
        <span className={`score-value ${tier}`}>{score?.toFixed(0)}</span>
      )}
    </div>
  );
}
