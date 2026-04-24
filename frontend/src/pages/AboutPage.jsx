import { useCallback, useEffect, useState } from "react";
import { extractErrorMessage, fetchModelStats } from "../api/client";
import MetricsCharts from "../components/MetricsCharts";
import ModelComparisonTable from "../components/ModelComparisonTable";
import PageTransition from "../components/PageTransition";
import PipelineDiagram from "../components/PipelineDiagram";
import StatusMessage from "../components/StatusMessage";

function AboutPage() {
  const [stats, setStats] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  const loadStats = useCallback(async () => {
    setIsLoading(true);
    setError("");

    try {
      const data = await fetchModelStats();
      setStats(data);
    } catch (requestError) {
      setError(extractErrorMessage(requestError));
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    let isMounted = true;

    if (isMounted) {
      loadStats();
    }

    return () => {
      isMounted = false;
    };
  }, [loadStats]);

  return (
    <PageTransition className="page-stack">
      <section className="page-hero compact-hero">
        <span className="eyebrow">How It Works</span>
        <h1>Structured features, classical models, auditable outputs.</h1>
        <p>
          The backend evaluates the LIAR dataset with three model families, then deploys the engineered-feature model
          for production inference and lightweight explanations.
        </p>
      </section>

      <StatusMessage
        type="error"
        message={error}
        action={
          error ? (
            <button type="button" className="ghost-button" onClick={loadStats}>
              Retry
            </button>
          ) : null
        }
      />

      <section className="summary-strip">
        <div className="panel summary-card">
          <span className="section-label">Dataset</span>
          <strong>LIAR</strong>
          <p>12,836 labeled political statements with metadata about speaker, subject, and historical credibility.</p>
        </div>
        <div className="panel summary-card">
          <span className="section-label">Binary Mapping</span>
          <strong>REAL vs FAKE</strong>
          <p>Six original truthfulness labels are collapsed into a production binary classification target.</p>
        </div>
        <div className="panel summary-card">
          <span className="section-label">Deployed Model</span>
          <strong>{stats?.deployed_model || "Loading..."}</strong>
          <p>Selected from persisted training artifacts and exposed through the Flask API.</p>
        </div>
      </section>

      {isLoading ? (
        <section className="panel loading-panel">
          <div className="loading-spinner-wrap">
            <span className="button-spinner loading-spinner" aria-hidden="true" />
          </div>
          <p>Loading model statistics from the backend...</p>
        </section>
      ) : (
        <>
          <ModelComparisonTable stats={stats} />
          <MetricsCharts stats={stats} />
        </>
      )}

      <PipelineDiagram />
    </PageTransition>
  );
}

export default AboutPage;
