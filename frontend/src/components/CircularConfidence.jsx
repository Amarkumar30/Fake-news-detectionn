import { motion } from "framer-motion";

const RADIUS = 52;
const CIRCUMFERENCE = 2 * Math.PI * RADIUS;

function CircularConfidence({ value, verdict }) {
  const normalizedValue = Math.max(0, Math.min(100, value));
  const progress = normalizedValue / 100;

  return (
    <div className={`confidence-ring verdict-${verdict?.toLowerCase()}`}>
      <svg viewBox="0 0 140 140" className="confidence-svg" aria-hidden="true">
        <circle cx="70" cy="70" r={RADIUS} className="confidence-track" />
        <motion.circle
          cx="70"
          cy="70"
          r={RADIUS}
          className="confidence-progress"
          strokeDasharray={CIRCUMFERENCE}
          initial={{ strokeDashoffset: CIRCUMFERENCE }}
          animate={{ strokeDashoffset: CIRCUMFERENCE * (1 - progress) }}
          transition={{ duration: 1.15, ease: "easeOut" }}
        />
      </svg>

      <div className="confidence-copy">
        <span className="eyebrow">Confidence</span>
        <strong>{normalizedValue.toFixed(0)}%</strong>
      </div>
    </div>
  );
}

export default CircularConfidence;

