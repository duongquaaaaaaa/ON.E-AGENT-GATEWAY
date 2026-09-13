import { NavLink } from "react-router-dom";

const NAV_ITEMS = [
  { to: "/", label: "Product List", icon: "📦", end: true },
  { to: "/simulator", label: "Query Simulator", icon: "🤖" },
  { to: "/compare", label: "Before / After", icon: "🔄" },
];

export default function Navbar() {
  return (
    <nav className="navbar">
      <div className="navbar-inner">
        <div className="navbar-brand">
          <div className="brand-logo">🛸</div>
          <span className="brand-name">AEO Dashboard</span>
          <span className="brand-badge">Module 2</span>
        </div>
        <div className="navbar-nav">
          {NAV_ITEMS.map(({ to, label, icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) => `nav-link${isActive ? " active" : ""}`}
            >
              <span>{icon}</span>
              {label}
            </NavLink>
          ))}
        </div>
      </div>
    </nav>
  );
}
