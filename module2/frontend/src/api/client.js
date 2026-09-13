const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function apiFetch(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      "X-API-Key": "demo",
      ...options.headers,
    },
    ...options,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `API error ${res.status}`);
  }

  return res.json();
}

export const api = {
  getProducts: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return apiFetch(`/products${qs ? `?${qs}` : ""}`);
  },

  getProduct: (id) => apiFetch(`/products/${id}`),

  simulateQuery: (question) =>
    apiFetch("/simulate-query", {
      method: "POST",
      body: JSON.stringify({ question }),
    }),

  runScoring: () =>
    apiFetch("/run-scoring", { method: "POST" }),
};
