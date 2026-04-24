import { NavLink } from "react-router-dom";

const navItems = [
  { label: "Detector", to: "/" },
  { label: "How It Works", to: "/about" },
  { label: "Research", to: "/research" },
];

function Layout({ children, banner = null }) {
  return (
    <div className="site-shell">
      <div className="site-noise" />
      <header className="site-header">
        <NavLink to="/" className="brand-mark">
          <span className="brand-kicker">Signal Desk</span>
          <span className="brand-title">Fake News Detector</span>
        </NavLink>

        <nav className="site-nav" aria-label="Primary">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) => `nav-link${isActive ? " is-active" : ""}`}
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
      </header>

      {banner ? <div className="site-banner-wrap">{banner}</div> : null}
      <main className="site-main">{children}</main>
    </div>
  );
}

export default Layout;
