import PageTransition from "../components/PageTransition";

function HealthPage({ backendStatus, backendError }) {
  return (
    <PageTransition className="page-stack">
      <section className="page-hero compact-hero">
        <span className="eyebrow">Application Health</span>
        <h1>TruthLens status console.</h1>
        <p>Frontend build metadata and current backend connectivity status.</p>
      </section>

      <section className="summary-strip">
        <div className="panel summary-card">
          <span className="section-label">App Name</span>
          <strong>{import.meta.env.VITE_APP_NAME || "TruthLens"}</strong>
          <p>Client-side label exposed through Vite environment configuration.</p>
        </div>
        <div className="panel summary-card">
          <span className="section-label">Version</span>
          <strong>{__APP_VERSION__}</strong>
          <p>Injected from the frontend package metadata at build time.</p>
        </div>
        <div className="panel summary-card">
          <span className="section-label">Backend</span>
          <strong>{backendStatus}</strong>
          <p>{backendError || "Backend reachable."}</p>
        </div>
      </section>
    </PageTransition>
  );
}

export default HealthPage;
