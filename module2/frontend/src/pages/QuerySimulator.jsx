import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";
import TierBadge from "../components/TierBadge";
import ScoreBar from "../components/ScoreBar";

const EXAMPLE_QUERIES = [
  "compact drone under 250g with 4K camera",
  "professional enterprise drone for surveying",
  "educational programmable drone for STEM",
  "FPV racing drone",
  "budget drone for beginners under $200",
  "cinema drone with heavy lift payload",
  "autonomous tracking drone for outdoor sports",
];

export default function QuerySimulator() {
  const navigate = useNavigate();
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e?.preventDefault();
    if (!question.trim()) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const data = await api.simulateQuery(question);
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleExample = (q) => {
    setQuestion(q);
    setResult(null);
    setError(null);
  };

  const selected = result?.selected || [];
  const notSelected = result?.not_selected || [];
  const matched = [...selected, ...notSelected.filter(p => p.matched_query)];
  const notMatched = notSelected.filter(p => !p.matched_query);

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Agent Query Simulator</h1>
          <p className="page-subtitle">
            Simulate how an AI buying agent would respond to a buyer's natural-language question.
          </p>
        </div>
      </div>

      {/* Query Input */}
      <div className="card" style={{ marginBottom: 24 }}>
        <form onSubmit={handleSubmit}>
          <label style={{ display: "block", fontSize: "0.875rem", fontWeight: 600, marginBottom: 10, color: "var(--text-secondary)" }}>
            💬 Buyer-style question
          </label>
          <div className="query-input-group">
            <input
              id="query-input"
              className="input"
              type="text"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="e.g. I need a lightweight drone under $400 with 4K video..."
              style={{ flex: 1 }}
            />
            <button
              id="submit-query-btn"
              className="btn btn-primary"
              type="submit"
              disabled={loading || !question.trim()}
            >
              {loading ? (
                <><span className="spinner" style={{ width: 16, height: 16, borderWidth: 2 }} /> Simulating…</>
              ) : (
                <><span>🔍</span> Simulate</>
              )}
            </button>
          </div>
        </form>

        {/* Example queries */}
        <div style={{ marginTop: 14 }}>
          <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginBottom: 8, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.06em" }}>
            Try an example
          </div>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            {EXAMPLE_QUERIES.map((q) => (
              <button
                key={q}
                className="filter-chip"
                onClick={() => handleExample(q)}
                style={{ fontSize: "0.75rem" }}
              >
                {q}
              </button>
            ))}
          </div>
        </div>
      </div>

      {error && <div className="error-state" style={{ marginBottom: 20 }}>⚠️ {error}</div>}

      {/* Results */}
      {result && (
        <div>
          {/* Summary Banner */}
          <div style={{
            background: "var(--bg-card)",
            border: "1px solid var(--border)",
            borderRadius: 12,
            padding: "16px 20px",
            marginBottom: 24,
            display: "flex",
            gap: 24,
            alignItems: "center",
            flexWrap: "wrap",
          }}>
            <div style={{ fontSize: "0.875rem", color: "var(--text-secondary)" }}>
              Query: <strong style={{ color: "var(--text-primary)" }}>"{result.question}"</strong>
            </div>
            <div style={{ marginLeft: "auto", display: "flex", gap: 16, fontSize: "0.8rem" }}>
              <span>📊 {result.total_products_evaluated} evaluated</span>
              <span style={{ color: "var(--green)" }}>✅ {result.selected_count} selected</span>
              <span style={{ color: "var(--red)" }}>❌ {result.total_products_evaluated - result.selected_count} excluded</span>
            </div>
          </div>

          {/* Selected Products */}
          {selected.length > 0 && (
            <div style={{ marginBottom: 28 }}>
              <h3 style={{ marginBottom: 14, display: "flex", alignItems: "center", gap: 8 }}>
                <span style={{ color: "var(--green)" }}>✅</span>
                Agent Selected ({selected.length})
              </h3>
              {selected.map((p) => (
                <div
                  key={p.product_id}
                  className="result-item selected"
                  style={{ cursor: "pointer" }}
                  onClick={() => navigate(`/products/${p.product_id}`)}
                  id={`selected-${p.product_id}`}
                >
                  <div className="result-status-icon selected">✅</div>
                  <div className="result-meta">
                    <div className="result-name">{p.product_name}</div>
                    <div className="result-reason">{p.reason}</div>
                  </div>
                  <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 8, flexShrink: 0, minWidth: 120 }}>
                    <TierBadge tier={p.tier} />
                    <ScoreBar score={p.overall_score} />
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Matched but excluded */}
          {matched.filter(p => !p.selected).length > 0 && (
            <div style={{ marginBottom: 28 }}>
              <h3 style={{ marginBottom: 14, display: "flex", alignItems: "center", gap: 8 }}>
                <span style={{ color: "var(--yellow)" }}>⚠️</span>
                Matched Query — Excluded Due to Low AEO Score
              </h3>
              {matched.filter(p => !p.selected).map((p) => (
                <div
                  key={p.product_id}
                  className="result-item excluded"
                  style={{ cursor: "pointer" }}
                  onClick={() => navigate(`/products/${p.product_id}`)}
                  id={`excluded-${p.product_id}`}
                >
                  <div className="result-status-icon excluded">❌</div>
                  <div className="result-meta">
                    <div className="result-name">{p.product_name}</div>
                    <div className="result-reason">{p.reason}</div>
                  </div>
                  <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 8, flexShrink: 0, minWidth: 120 }}>
                    <TierBadge tier={p.tier} />
                    <ScoreBar score={p.overall_score} />
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Not matched */}
          {notMatched.length > 0 && (
            <details style={{ marginTop: 8 }}>
              <summary style={{
                cursor: "pointer",
                color: "var(--text-muted)",
                fontSize: "0.8rem",
                fontWeight: 600,
                padding: "10px 0",
                userSelect: "none",
              }}>
                {notMatched.length} products did not match query
              </summary>
              <div style={{ marginTop: 10 }}>
                {notMatched.map((p) => (
                  <div
                    key={p.product_id}
                    className="result-item"
                    style={{ opacity: 0.5, cursor: "pointer" }}
                    onClick={() => navigate(`/products/${p.product_id}`)}
                  >
                    <div className="result-status-icon not-matched">—</div>
                    <div className="result-meta">
                      <div className="result-name">{p.product_name}</div>
                      <div className="result-reason">{p.reason}</div>
                    </div>
                    <TierBadge tier={p.tier} />
                  </div>
                ))}
              </div>
            </details>
          )}

          {selected.length === 0 && matched.length === 0 && (
            <div className="empty-state">
              <div className="empty-icon">🤖</div>
              <p>No products matched this query. Try a more specific question.</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
