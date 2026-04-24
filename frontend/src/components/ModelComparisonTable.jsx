function formatMetric(value) {
  if (value === null || value === undefined) {
    return "N/A";
  }
  return Number(value).toFixed(3);
}

function ModelComparisonTable({ stats }) {
  const models = stats?.models || {};
  const comparisonRows = [
    {
      name: "Logistic Regression",
      artifactKey: "LogisticRegression",
      strengths: "Fast linear baseline with interpretable token weights.",
    },
    {
      name: "Naive Bayes",
      artifactKey: "NaiveBayes",
      strengths: "Cheap probabilistic baseline for sparse text signals.",
    },
    {
      name: "Random Forest",
      artifactKey: "RandomForest",
      strengths: "Best production candidate with engineered metadata features.",
    },
  ];

  return (
    <div className="panel comparison-panel">
      <div className="panel-header">
        <span className="eyebrow">Model Comparison</span>
        <h3>Baseline models versus engineered feature ensemble</h3>
      </div>

      <div className="table-wrap">
        <table className="comparison-table">
          <thead>
            <tr>
              <th>Model</th>
              <th>Validation Accuracy</th>
              <th>Validation F1</th>
              <th>Test Accuracy</th>
              <th>Test F1</th>
              <th>Notes</th>
            </tr>
          </thead>
          <tbody>
            {comparisonRows.map((row) => (
              <tr key={row.artifactKey}>
                <td>{row.name}</td>
                <td>{formatMetric(models[row.artifactKey]?.validation?.accuracy)}</td>
                <td>{formatMetric(models[row.artifactKey]?.validation?.f1_score)}</td>
                <td>{formatMetric(models[row.artifactKey]?.test?.accuracy)}</td>
                <td>{formatMetric(models[row.artifactKey]?.test?.f1_score)}</td>
                <td>{row.strengths}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default ModelComparisonTable;

