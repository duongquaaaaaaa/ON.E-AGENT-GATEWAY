import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";
import TierBadge from "../components/TierBadge";
import ScoreBar from "../components/ScoreBar";

const SORT_OPTIONS = [
  { value: "score_desc", label: "Score: High → Low" },
  { value: "score_asc", label: "Score: Low → High" },
  { value: "name_asc", label: "Name A → Z" },
];

const AXIS_ICONS = {
  completeness: "📋",
  machine_readability: "🤖",
  retrievability: "🔍",
  answerability: "💬",
  transactability: "💳",
};

export default function ProductList() {
  const navigate = useNavigate();
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [tierFilter, setTierFilter] = useState("all");
  const [sort, setSort] = useState("score_desc");
  const [scoring, setScoring] = useState(false);
  const [scoringResult, setScoringResult] = useState(null);

  const fetchProducts = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = { sort };
      if (tierFilter !== "all") params.tier = tierFilter;
      const data = await api.getProducts(params);
      setProducts(data.products || []);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [tierFilter, sort]);

  useEffect(() => { fetchProducts(); }, [fetchProducts]);

  const handleRunScoring = async () => {
    setScoring(true);
    setScoringResult(null);
    try {
      const res = await api.runScoring();
      setScoringResult(res);
      fetchProducts();
    } catch (e) {
      setError(e.message);
    } finally {
      setScoring(false);
    }
  };

  const greenCount = products.filter(p => p.tier === "green").length;
  const yellowCount = products.filter(p => p.tier === "yellow").length;
  const redCount = products.filter(p => p.tier === "red").length;
  const avgScore = products.length
    ? (products.reduce((s, p) => s + p.overall_score, 0) / products.length).toFixed(1)
    : 0;

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Product AEO Scores</h1>
          <p className="page-subtitle">
            Agent-Experience Optimization — {products.length} products evaluated
          </p>
        </div>
        <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
          <button
            id="run-scoring-btn"
            className="btn btn-primary"
            onClick={handleRunScoring}
            disabled={scoring}
          >
            {scoring ? (
              <><span className="spinner" style={{ width: 16, height: 16, borderWidth: 2 }} /> Scoring…</>
            ) : (
              <><span>⚡</span> Run Scoring</>
            )}
          </button>
        </div>
      </div>

      {scoringResult && (
        <div style={{
          background: "rgba(34,197,94,0.08)",
          border: "1px solid rgba(34,197,94,0.25)",
          borderRadius: 12,
          padding: "12px 20px",
          marginBottom: 20,
          fontSize: "0.875rem",
          color: "var(--green)",
          display: "flex",
          gap: 16,
        }}>
          ✅ Scoring complete — {scoringResult.products_scored} products scored.
          🟢 {scoringResult.summary.green} ready · 🟡 {scoringResult.summary.yellow} needs work · 🔴 {scoringResult.summary.red} not ready
        </div>
      )}

      {/* Stats Row */}
      <div className="stats-row">
        <div className="stat-card">
          <span className="stat-label">Avg AEO Score</span>
          <span className={`stat-value ${avgScore >= 80 ? "green" : avgScore >= 50 ? "yellow" : "red"}`}>
            {avgScore}
          </span>
        </div>
        <div className="stat-card">
          <span className="stat-label">🟢 Agent-Ready</span>
          <span className="stat-value green">{greenCount}</span>
        </div>
        <div className="stat-card">
          <span className="stat-label">🟡 Needs Work</span>
          <span className="stat-value yellow">{yellowCount}</span>
        </div>
        <div className="stat-card">
          <span className="stat-label">🔴 Not Ready</span>
          <span className="stat-value red">{redCount}</span>
        </div>
      </div>

      {/* Filter + Sort bar */}
      <div className="filter-bar">
        {["all", "green", "yellow", "red"].map((t) => (
          <button
            key={t}
            id={`filter-${t}`}
            className={`filter-chip ${tierFilter === t ? `active-${t}` : ""}`}
            onClick={() => setTierFilter(t)}
          >
            {t === "all" ? "All Products" : t === "green" ? "🟢 Agent-Ready" : t === "yellow" ? "🟡 Needs Work" : "🔴 Not Ready"}
          </button>
        ))}
        <div style={{ marginLeft: "auto" }}>
          <select
            id="sort-select"
            className="input select"
            value={sort}
            onChange={(e) => setSort(e.target.value)}
            style={{ width: "auto", fontSize: "0.8rem", padding: "6px 36px 6px 12px" }}
          >
            {SORT_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
          </select>
        </div>
      </div>

      {/* Error */}
      {error && <div className="error-state" style={{ marginBottom: 20 }}>⚠️ {error}</div>}

      {/* Loading */}
      {loading && (
        <div className="loading-state">
          <div className="spinner" />
          <span>Loading products…</span>
        </div>
      )}

      {/* Table */}
      {!loading && !error && (
        <div className="card" style={{ padding: 0, overflow: "hidden" }}>
          {products.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">📦</div>
              <p>No products found. Try a different filter or run scoring first.</p>
            </div>
          ) : (
            <table className="data-table">
              <thead>
                <tr>
                  <th>Product</th>
                  <th>Category</th>
                  <th>Price</th>
                  <th style={{ minWidth: 180 }}>AEO Score</th>
                  <th>Tier</th>
                  <th>Weakest Axis</th>
                </tr>
              </thead>
              <tbody>
                {products.map((p) => (
                  <tr
                    key={p.id}
                    id={`product-row-${p.id}`}
                    onClick={() => navigate(`/products/${p.id}`)}
                  >
                    <td>
                      <div style={{ fontWeight: 600, fontSize: "0.875rem", marginBottom: 2 }}>
                        {p.name}
                      </div>
                      <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
                        {p.brand || "No brand"}
                      </div>
                    </td>
                    <td style={{ color: "var(--text-secondary)", fontSize: "0.8rem" }}>
                      {p.category}
                    </td>
                    <td style={{ fontFamily: "Space Grotesk, sans-serif", fontWeight: 600 }}>
                      {p.price != null ? `$${p.price.toLocaleString()}` : <span style={{ color: "var(--text-muted)" }}>—</span>}
                    </td>
                    <td>
                      <ScoreBar score={p.overall_score} />
                    </td>
                    <td><TierBadge tier={p.tier} /></td>
                    <td style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}>
                      <span style={{ marginRight: 4 }}>{AXIS_ICONS[p.weakest_axis]}</span>
                      <span style={{ textTransform: "capitalize" }}>
                        {p.weakest_axis?.replace(/_/g, " ")}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </div>
  );
}
