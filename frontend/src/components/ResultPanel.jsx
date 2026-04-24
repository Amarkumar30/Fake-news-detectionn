import { motion } from "framer-motion";
import CircularConfidence from "./CircularConfidence";
import CredibilityGauge from "./CredibilityGauge";
import KeywordChips from "./KeywordChips";

function buildNarrative(result) {
  const confidence = Math.round((result?.confidence || 0) * 100);
  const explanation = result?.explanation || {};
  const credibility = explanation.credibility_score;
  const topKeyword = explanation.top_tfidf_features?.[0]?.feature;

  if (!result) {
    return "";
  }

  const credibilityText =
    typeof credibility === "number"
      ? `Speaker history scored ${Math.round(credibility * 100)} out of 100 credibility.`
      : "No historical speaker credibility was supplied for this run.";

  const keywordText = topKeyword
    ? `The strongest textual signal in this pass was "${topKeyword}".`
    : "The model relied more on broad text structure than standout terms for this sample.";

  return `${result.prediction} at ${confidence}% confidence. ${credibilityText} ${keywordText}`;
}

function ResultPanel({ result }) {
  if (!result) {
    return (
      <section className="panel result-panel placeholder-panel">
        <div className="panel-header">
          <span className="eyebrow">Awaiting Analysis</span>
          <h2>Submit a claim to see the forensic breakdown.</h2>
        </div>
        <p className="muted-copy">
          The detector will return a binary verdict, confidence score, historical speaker credibility, and the top
          weighted keywords that informed the model.
        </p>
      </section>
    );
  }

  const verdictClass = result.prediction.toLowerCase();
  const confidencePercent = (result.confidence || 0) * 100;

  return (
    <motion.section
      className={`panel result-panel verdict-${verdictClass}`}
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.45, ease: [0.16, 1, 0.3, 1] }}
    >
      <motion.div
        className="verdict-flash"
        initial={{ opacity: 0 }}
        animate={{ opacity: [0, 0.28, 0] }}
        transition={{ duration: 0.75 }}
      />

      <div className="result-topline">
        <div>
          <span className="eyebrow">Verdict</span>
          <motion.h2
            className="verdict-title"
            initial={{ opacity: 0, y: 18 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            {result.prediction}
          </motion.h2>
          <p className="mono-meta">Primary model: {result.model}</p>
        </div>

        <CircularConfidence value={confidencePercent} verdict={result.prediction} />
      </div>

      <div className="result-grid">
        <div className="result-column">
          <CredibilityGauge value={result.explanation?.credibility_score} />
          <div className="result-copy">
            <span className="section-label">Analyst Note</span>
            <p>{buildNarrative(result)}</p>
          </div>
        </div>

        <div className="result-column">
          <div className="section-label-row">
            <span className="section-label">Top Influential Keywords</span>
            <span className="mono-meta">{result.explanation?.explanation_method || "weighted_tfidf"}</span>
          </div>
          <KeywordChips keywords={result.explanation?.top_tfidf_features || []} />
        </div>
      </div>
    </motion.section>
  );
}

export default ResultPanel;

