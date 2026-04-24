function PipelineDiagram() {
  return (
    <div className="panel pipeline-panel">
      <div className="panel-header">
        <span className="eyebrow">Inference Pipeline</span>
        <h3>From raw claim to machine verdict</h3>
      </div>

      <svg viewBox="0 0 900 220" className="pipeline-diagram" role="img" aria-label="Model inference pipeline">
        <defs>
          <linearGradient id="pipelineStroke" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#f5a623" />
            <stop offset="100%" stopColor="#ffd36b" />
          </linearGradient>
        </defs>
        <g>
          <rect x="20" y="48" width="180" height="110" rx="20" className="pipeline-box" />
          <rect x="250" y="48" width="180" height="110" rx="20" className="pipeline-box" />
          <rect x="480" y="48" width="180" height="110" rx="20" className="pipeline-box" />
          <rect x="710" y="48" width="170" height="110" rx="20" className="pipeline-box" />

          <path d="M200 103 L250 103" className="pipeline-line" />
          <path d="M430 103 L480 103" className="pipeline-line" />
          <path d="M660 103 L710 103" className="pipeline-line" />

          <text x="110" y="90" className="pipeline-title">Input Claim</text>
          <text x="110" y="118" className="pipeline-copy">Statement</text>
          <text x="110" y="138" className="pipeline-copy">Speaker</text>

          <text x="340" y="90" className="pipeline-title">Feature Stack</text>
          <text x="340" y="118" className="pipeline-copy">TF-IDF</text>
          <text x="340" y="138" className="pipeline-copy">Metadata + counts</text>

          <text x="570" y="90" className="pipeline-title">Model Layer</text>
          <text x="570" y="118" className="pipeline-copy">LR / NB / RF</text>
          <text x="570" y="138" className="pipeline-copy">Binary inference</text>

          <text x="795" y="90" className="pipeline-title">Output</text>
          <text x="795" y="118" className="pipeline-copy">REAL or FAKE</text>
          <text x="795" y="138" className="pipeline-copy">Confidence + keywords</text>
        </g>
      </svg>
    </div>
  );
}

export default PipelineDiagram;

