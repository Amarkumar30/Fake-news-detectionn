import { motion } from "framer-motion";

function CredibilityGauge({ value }) {
  const normalizedValue = typeof value === "number" ? Math.max(0, Math.min(1, value)) : null;
  const width = normalizedValue === null ? 0 : normalizedValue * 100;

  return (
    <div className="credibility-block">
      <div className="section-label-row">
        <span className="section-label">Speaker Credibility</span>
        <span className="mono-meta">
          {normalizedValue === null ? "Unavailable" : `${Math.round(width)} / 100`}
        </span>
      </div>

      <div className="credibility-track" aria-hidden="true">
        <motion.div
          className="credibility-fill"
          initial={{ width: 0 }}
          animate={{ width: `${width}%` }}
          transition={{ duration: 1, ease: "easeOut" }}
        />
      </div>
    </div>
  );
}

export default CredibilityGauge;

