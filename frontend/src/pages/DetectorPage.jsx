import { motion } from "framer-motion";
import { useState } from "react";
import { predictNews, extractErrorMessage } from "../api/client";
import PageTransition from "../components/PageTransition";
import ResultPanel from "../components/ResultPanel";
import StatusMessage from "../components/StatusMessage";
import { exampleSnippets, partyOptions } from "../data/exampleSnippets";

const initialForm = {
  text: "",
  speaker: "",
  party: "unknown",
};

const MIN_TEXT_LENGTH = 10;
const MAX_TEXT_LENGTH = 5000;

function DetectorPage() {
  const [form, setForm] = useState(initialForm);
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [lastPayload, setLastPayload] = useState(null);

  const trimmedLength = form.text.trim().length;
  const recommendedState =
    trimmedLength === 0 ? "empty" : trimmedLength < 50 ? "short" : trimmedLength > MAX_TEXT_LENGTH ? "long" : "good";
  const submitDisabled = isLoading || trimmedLength === 0;

  function validateForm() {
    if (trimmedLength === 0) {
      return "Text cannot be empty";
    }
    if (trimmedLength < MIN_TEXT_LENGTH) {
      return "Please enter a longer statement";
    }
    return "";
  }

  async function submitPayload(payload) {
    setError("");
    setIsLoading(true);
    setLastPayload(payload);

    try {
      const data = await predictNews(payload);
      setResult(data);
    } catch (requestError) {
      setError(extractErrorMessage(requestError));
    } finally {
      setIsLoading(false);
    }
  }

  async function handleSubmit(event) {
    event.preventDefault();
    const validationMessage = validateForm();
    if (validationMessage) {
      setError(validationMessage);
      setResult(null);
      return;
    }

    const payload = {
      text: form.text,
      speaker: form.speaker || undefined,
      party: form.party || undefined,
    };
    await submitPayload(payload);
  }

  function applyExample(example) {
    setForm({
      text: example.text,
      speaker: example.speaker,
      party: example.party,
    });
    setResult(null);
    setError("");
  }

  function updateText(nextText) {
    setForm((current) => ({ ...current, text: nextText }));
    setError("");
    setLastPayload(null);
    setResult(null);
  }

  function updateField(fieldName, value) {
    setForm((current) => ({ ...current, [fieldName]: value }));
    setError("");
    setLastPayload(null);
    setResult(null);
  }

  return (
    <PageTransition className="detector-page">
      <section className="hero-grid">
        <div className="hero-copy">
          <span className="eyebrow">Forensic Claim Analysis</span>
          <h1>IS IT REAL?</h1>
          <p className="hero-text">
            Run a political claim through a newsroom-style investigation surface. The detector combines linguistic
            signals, speaker credibility, and metadata from the LIAR benchmark to issue a binary verdict.
          </p>
        </div>

        <div className="hero-aside panel">
          <span className="section-label">System Focus</span>
          <ul className="metric-list">
            <li>
              <strong>Dataset</strong>
              <span>LIAR, 12,836 labeled statements</span>
            </li>
            <li>
              <strong>Deployment</strong>
              <span>Flask API at localhost:5000</span>
            </li>
            <li>
              <strong>Decisioning</strong>
              <span>Binary REAL / FAKE confidence output</span>
            </li>
          </ul>
        </div>
      </section>

      <section className="detector-grid">
        <motion.form
          className="panel detector-form"
          onSubmit={handleSubmit}
          initial={{ opacity: 0, x: -24 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5 }}
        >
          <div className="panel-header">
            <span className="eyebrow">Detector Console</span>
            <h2>Submit a claim for review</h2>
          </div>

          <label className="form-field">
            <span>Claim or news excerpt</span>
            <textarea
              value={form.text}
              onChange={(event) => updateText(event.target.value)}
              placeholder="Paste the statement, quote, or article excerpt you want analyzed..."
              rows={5}
              required
            />
            <div className={`character-count count-${recommendedState}`}>
              <span>{trimmedLength} characters</span>
              <span>Recommended: 50-5000</span>
            </div>
          </label>

          <div className="form-row">
            <label className="form-field">
              <span>Speaker name</span>
              <input
                type="text"
                value={form.speaker}
                onChange={(event) => updateField("speaker", event.target.value)}
                placeholder="Optional"
              />
            </label>

            <label className="form-field">
              <span>Political party</span>
              <select
                value={form.party}
                onChange={(event) => updateField("party", event.target.value)}
              >
                {partyOptions.map((party) => (
                  <option key={party} value={party}>
                    {party}
                  </option>
                ))}
              </select>
            </label>
          </div>

          <div className="form-actions">
            <button type="submit" className="analyze-button" disabled={submitDisabled}>
              {isLoading ? (
                <>
                  <span className="button-spinner" aria-hidden="true" />
                  Analyzing...
                </>
              ) : (
                "Analyze"
              )}
            </button>
            <button
              type="button"
              className="ghost-button"
              onClick={() => {
                setForm(initialForm);
                setResult(null);
                setError("");
                setLastPayload(null);
              }}
            >
              Reset
            </button>
          </div>

          <StatusMessage
            type="error"
            message={error}
            action={
              error && lastPayload && !isLoading ? (
                <button type="button" className="ghost-button" onClick={() => submitPayload(lastPayload)}>
                  Retry
                </button>
              ) : null
            }
          />
        </motion.form>

        <motion.div
          initial={{ opacity: 0, x: 24 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.55 }}
        >
          <ResultPanel result={result} />
        </motion.div>
      </section>

      <section className="examples-section">
        <div className="section-heading">
          <span className="eyebrow">Examples</span>
          <h2>Try a sample statement</h2>
        </div>

        <div className="example-grid">
          {exampleSnippets.map((example) => (
            <button
              key={example.title}
              type="button"
              className="example-card"
              onClick={() => applyExample(example)}
            >
              <span className="mono-meta">{example.party}</span>
              <h3>{example.title}</h3>
              <p>{example.text}</p>
            </button>
          ))}
        </div>
      </section>
    </PageTransition>
  );
}

export default DetectorPage;
