import { useState } from "react";
import { api } from "../api/client";
import TierBadge from "../components/TierBadge";

const SAMPLE_QUERIES = [
  "4K monitor for graphic design",
  "gaming monitor 144Hz",
  "office monitor budget",
  "ultrawide curved monitor for video editing",
  "monitor compatible with MacBook Pro",
];

export default function BeforeAfter() {
  const [question, setQuestion] = useState("");
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (q) => {
    const query = q || question;
    if (!query.trim()) return;
    setLoading(true);
    setError("");
    try {
      const result = await api.compareBeforeAfter(query);
      setData(result);
    } catch (err) {
      setError(err.message || "Failed to compare");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>Before / After Comparison</h1>
        <p className="page-subtitle">
          See how catalog standardization improves product discovery for AI agents.
          The same query is run against raw data (name + category only) vs enriched data
          (agent_text, structured specs, tags, and use-cases).
        </p>
      </div>

      {/* Search bar */}
      <div className="compare-search-bar">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSubmit();
          }}
        >
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Enter a buyer-style query, e.g. '4K monitor for graphic design'"
            className="compare-input"
          />
          <button type="submit" disabled={loading} className="compare-btn">
            {loading ? "Comparing…" : "Compare"}
          </button>
        </form>

        <div className="sample-queries">
          <span className="sample-label">Try:</span>
          {SAMPLE_QUERIES.map((q) => (
            <button
              key={q}
              className="sample-chip"
              onClick={() => {
                setQuestion(q);
                handleSubmit(q);
              }}
            >
              {q}
            </button>
          ))}
        </div>
      </div>

      {error && <div className="error-banner">{error}</div>}

      {data && (
        <>
          {/* Summary card */}
          <div className="compare-summary">
            <div className="summary-stat">
              <span className="stat-number stat-before">{data.summary.before_matches}</span>
              <span className="stat-label">Before</span>
            </div>
            <div className="summary-arrow">→</div>
            <div className="summary-stat">
              <span className="stat-number stat-after">{data.summary.after_matches}</span>
              <span className="stat-label">After</span>
            </div>
            <div className="summary-delta">
              <span className="delta-badge">
                {data.summary.new_matches_from_enrichment > 0
                  ? `+${data.summary.new_matches_from_enrichment} new products discovered`
                  : data.summary.improvement}
              </span>
            </div>
          </div>

          {/* Side-by-side results */}
          <div className="compare-grid">
            {/* BEFORE */}
            <div className="compare-column before">
              <div className="column-header before-header">
                <h2>❌ Before Standardization</h2>
                <p className="column-method">{data.before.method}</p>
                <span className="result-count">{data.before.results.length} results</span>
              </div>
              {data.before.results.length === 0 ? (
                <div className="empty-state">No matches found with raw keyword search</div>
              ) : (
                data.before.results.map((r) => (
                  <div key={r.product_id} className="compare-card before-card">
                    <div className="card-title">{r.product_name}</div>
                    <div className="card-meta">{r.category}</div>
                    <div className="card-tokens">
                      Matched: {r.matched_tokens.map((t) => (
                        <span key={t} className="token-badge before-token">{t}</span>
                      ))}
                    </div>
                    <div className="card-quality">{r.match_quality}</div>
                  </div>
                ))
              )}
            </div>

            {/* AFTER */}
            <div className="compare-column after">
              <div className="column-header after-header">
                <h2>✅ After Standardization</h2>
                <p className="column-method">{data.after.method}</p>
                <span className="result-count">{data.after.results.length} results</span>
              </div>
              {data.after.results.length === 0 ? (
                <div className="empty-state">No matches found</div>
              ) : (
                data.after.results.map((r) => (
                  <div key={r.product_id} className="compare-card after-card">
                    <div className="card-top-row">
                      <span className="card-title">{r.product_name}</span>
                      <TierBadge tier={r.tier} />
                    </div>
                    <div className="card-meta">{r.category}</div>
                    <div className="card-score">
                      AEO Score: <strong>{r.aeo_score}</strong>/100
                    </div>
                    <div className="card-tokens">
                      Matched: {r.matched_tokens.map((t) => (
                        <span key={t} className="token-badge after-token">{t}</span>
                      ))}
                    </div>
                    {r.matched_specs && r.matched_specs.length > 0 && (
                      <div className="card-specs">
                        Matched specs: {r.matched_specs.map((s) => (
                          <span key={s} className="spec-badge">{s}</span>
                        ))}
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
