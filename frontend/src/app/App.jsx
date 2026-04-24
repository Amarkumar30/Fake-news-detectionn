import { AnimatePresence } from "framer-motion";
import { Suspense, lazy, useCallback, useEffect, useState } from "react";
import { Navigate, Route, Routes, useLocation } from "react-router-dom";
import { extractErrorMessage, fetchBackendHealth } from "../api/client";
import Layout from "../components/Layout";
import StatusMessage from "../components/StatusMessage";

const DetectorPage = lazy(() => import("../pages/DetectorPage"));
const AboutPage = lazy(() => import("../pages/AboutPage"));
const ResearchPage = lazy(() => import("../pages/ResearchPage"));
const HealthPage = lazy(() => import("../pages/HealthPage"));

function App() {
  const location = useLocation();
  const [backendStatus, setBackendStatus] = useState("checking");
  const [backendError, setBackendError] = useState("");

  const runBackendHealthCheck = useCallback(async () => {
    setBackendStatus("checking");
    setBackendError("");

    try {
      const health = await fetchBackendHealth();
      if (health.status === "ok") {
        setBackendStatus("online");
      } else {
        setBackendStatus("offline");
        setBackendError(health.startup_error || "Backend offline — start Flask server");
      }
    } catch (error) {
      setBackendStatus("offline");
      setBackendError(extractErrorMessage(error) || "Backend offline — start Flask server");
    }
  }, []);

  useEffect(() => {
    runBackendHealthCheck();
  }, [runBackendHealthCheck]);

  const banner =
    backendStatus === "offline" ? (
      <StatusMessage
        type="error"
        message="Backend offline — start Flask server"
        action={
          <button type="button" className="ghost-button" onClick={runBackendHealthCheck}>
            Retry
          </button>
        }
      />
    ) : backendStatus === "checking" ? (
      <StatusMessage type="info" message="Checking backend connection..." isLoading />
    ) : null;

  return (
    <Layout banner={banner}>
      <Suspense
        fallback={
          <section className="panel loading-panel route-loading">
            <div className="loading-bar" />
            <p>Loading page...</p>
          </section>
        }
      >
        <AnimatePresence mode="wait">
          <Routes location={location} key={location.pathname}>
            <Route path="/" element={<DetectorPage />} />
            <Route path="/about" element={<AboutPage />} />
            <Route path="/research" element={<ResearchPage />} />
            <Route path="/health" element={<HealthPage backendStatus={backendStatus} backendError={backendError} />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </AnimatePresence>
      </Suspense>
    </Layout>
  );
}

export default App;
