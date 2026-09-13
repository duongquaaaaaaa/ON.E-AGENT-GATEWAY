import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { api } from "../api/client";
import TierBadge from "../components/TierBadge";
import ScoreBar from "../components/ScoreBar";
import RadarChart from "../components/RadarChart";

const AXIS_META = {
  completeness: {
    icon: "📋",
    label: "Completeness",
    desc: "% of required fields filled",
  },
  machine_readability: {
    icon: "🤖",
    label: "Machine Readability",
    desc: "JSON-LD present + structured spec ratio",
  },
  retrievability: {
    icon: "🔍",
    label: "Retrievability",
    desc: "Appears in agent semantic searches",
  },
  answerability: {
    icon: "💬",
    label: "Answerability",
    desc: "Agent can answer buyer FAQs from data",
  },
  transactability: {
    icon: "💳",
    label: "Transactability",
    desc: "Price, SKU, stock, shipping complete",
  },
};

export default function ProductDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [product, setProduct] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    setLoading(true);
    api.getProduct(id)
      .then(setProduct)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) {
    return (
      <div className="loading-state">
        <div className="spinner" />
        <span>Loading product…</span>
      </div>
    );
  }

  if (error) {
    return (
      <div>
        <button className="btn btn-secondary" onClick={() => navigate(-1)} style={{ marginBottom: 20 }}>
          ← Back
        </button>
        <div className="error-state">⚠️ {error}</div>
      </div>
    );
  }

  if (!product) return null;

  const axes = product.axes || {};

  return (
    <div>
      {/* Header */}
      <div style={{ marginBottom: 24 }}>
        <button
          id="back-btn"
          className="btn btn-secondary"
          onClick={() => navigate(-1)}
          style={{ marginBottom: 16 }}
        >
          ← Back to Products
        </button>
        <div className="page-header" style={{ marginBottom: 0 }}>
          <div>
            <h1 className="page-title" style={{ fontSize: "1.5rem" }}>{product.name}</h1>
            <div style={{ display: "flex", gap: 10, alignItems: "center", marginTop: 8, flexWrap: "wrap" }}>
              {product.brand && (
                <span style={{ color: "var(--text-secondary)", fontSize: "0.875rem" }}>
                  {product.brand}
                </span>
              )}
              {product.category && (
                <span style={{
                  background: "rgba(255,255,255,0.06)",
                  border: "1px solid var(--border)",
                  borderRadius: 20,
                  padding: "2px 10px",
                  fontSize: "0.75rem",
                  color: "var(--text-secondary)",
                }}>
                  {product.category}
                </span>
              )}
            </div>
          </div>
          <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 8 }}>
            <TierBadge tier={product.tier} />
            <div style={{
              fontFamily: "Space Grotesk, sans-serif",
              fontWeight: 700,
              fontSize: "2.5rem",
              lineHeight: 1,
              color: product.overall_score >= 80 ? "var(--green)" : product.overall_score >= 50 ? "var(--yellow)" : "var(--red)",
            }}>
              {product.overall_score?.toFixed(0)}
              <span style={{ fontSize: "1rem", color: "var(--text-muted)", fontWeight: 400 }}>/100</span>
            </div>
          </div>
        </div>
      </div>

      {/* Main Grid */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20, marginBottom: 20 }}>

        {/* Radar Chart */}
        <div className="card" style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          <h3>AEO Radar</h3>
          <RadarChart axes={axes} />
        </div>

        {/* 5-Axis Breakdown */}
        <div className="card">
          <h3 style={{ marginBottom: 20 }}>Axis Breakdown</h3>
          <div className="axis-list">
            {Object.keys(AXIS_META).map((key) => {
              const meta = AXIS_META[key];
              const score = axes[key] ?? 0;
              const isWeakest = key === product.weakest_axis;
              const tier = score >= 80 ? "green" : score >= 50 ? "yellow" : "red";
              return (
                <div key={key} className="axis-item">
                  <div className="axis-header">
                    <span className="axis-name">
                      <span>{meta.icon}</span>
                      {meta.label}
                      {isWeakest && <span className="weakest-tag">Weakest</span>}
                    </span>
                    <span className={`score-value ${tier}`} style={{ fontFamily: "Space Grotesk" }}>
                      {score?.toFixed(0)}/100
                    </span>
                  </div>
                  <ScoreBar score={score} showLabel={false} />
                  <div style={{ fontSize: "0.72rem", color: "var(--text-muted)", marginTop: 4 }}>
                    {meta.desc}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Improvement Suggestion */}
      {product.improvement_suggestion && (
        <div className="suggestion-box" style={{ marginBottom: 20 }}>
          <div className="suggestion-icon">💡</div>
          <div className="suggestion-text">
            <strong>Improvement tip ({product.weakest_axis?.replace(/_/g, " ")}):</strong>{" "}
            {product.improvement_suggestion}
          </div>
        </div>
      )}

      {/* Product Info */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 16 }}>
        {[
          { label: "SKU", value: product.sku || "—" },
          { label: "Price", value: product.price != null ? `$${product.price.toLocaleString()} ${product.currency}` : "—" },
          { label: "Stock", value: product.stock != null ? product.stock : "—" },
          { label: "Shipping", value: product.shipping_fee != null ? (product.shipping_fee === 0 ? "Free" : `$${product.shipping_fee}`) : "—" },
          { label: "JSON-LD", value: product.jsonld_valid ? "✅ Valid" : "❌ Missing" },
          { label: "Images", value: product.images?.length > 0 ? `${product.images.length} image(s)` : "None" },
        ].map(({ label, value }) => (
          <div key={label} className="stat-card" style={{ padding: "14px 18px" }}>
            <span className="stat-label">{label}</span>
            <span style={{ fontWeight: 600, fontSize: "0.95rem", color: "var(--text-primary)" }}>
              {value}
            </span>
          </div>
        ))}
      </div>

      {/* Description */}
      {product.description && (
        <div className="card" style={{ marginTop: 16 }}>
          <h3 style={{ marginBottom: 10 }}>Description</h3>
          <p style={{ color: "var(--text-secondary)", fontSize: "0.875rem", lineHeight: 1.7 }}>
            {product.description}
          </p>
        </div>
      )}

      {/* Tags */}
      {product.tags?.length > 0 && (
        <div style={{ marginTop: 16, display: "flex", gap: 8, flexWrap: "wrap" }}>
          {product.tags.map((tag) => (
            <span key={tag} style={{
              background: "rgba(99,102,241,0.1)",
              border: "1px solid rgba(99,102,241,0.2)",
              borderRadius: 20,
              padding: "3px 10px",
              fontSize: "0.75rem",
              color: "var(--accent-light)",
            }}>
              #{tag}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
