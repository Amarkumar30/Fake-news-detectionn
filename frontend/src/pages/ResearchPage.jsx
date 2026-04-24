import PageTransition from "../components/PageTransition";
import { researchPapers } from "../data/researchPapers";

function ResearchPage() {
  return (
    <PageTransition className="page-stack">
      <section className="page-hero compact-hero">
        <span className="eyebrow">Research Basis</span>
        <h1>Evidence trail behind the detector.</h1>
        <p>
          The product draws on benchmark fake-claim research and keeps the interface focused on auditable signals rather
          than opaque generative rhetoric.
        </p>
      </section>

      <section className="research-grid">
        {researchPapers.map((paper) => (
          <article key={paper.href} className="panel research-card">
            <span className="section-label">Paper</span>
            <h2>{paper.title}</h2>
            <p>{paper.summary}</p>
            <a className="research-link" href={paper.href} target="_blank" rel="noreferrer">
              Open paper
            </a>
          </article>
        ))}
      </section>

      <section className="literature-strip">
        <article className="panel literature-card">
          <span className="section-label">Literature Summary</span>
          <h3>Why classical models still matter here</h3>
          <p>
            Short-form political claims are sparse, noisy, and metadata-rich. That makes TF-IDF baselines and engineered
            feature ensembles defensible choices when interpretability and latency are operational constraints.
          </p>
        </article>

        <article className="panel literature-card">
          <span className="section-label">Operational Takeaway</span>
          <h3>Context is a force multiplier</h3>
          <p>
            Speaker history, party affiliation, and subject category improve detection because misinformation patterns
            are not purely lexical. The frontend surfaces those signals so analysts can inspect them directly.
          </p>
        </article>
      </section>
    </PageTransition>
  );
}

export default ResearchPage;

