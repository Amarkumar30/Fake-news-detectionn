import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

const MODEL_ORDER = [
  { key: "LogisticRegression", label: "Logistic Regression" },
  { key: "NaiveBayes", label: "Naive Bayes" },
  { key: "RandomForest", label: "Random Forest" },
];

const CONFUSION_KEYS = [
  { key: "trueFake", label: "True Fake", color: "#401515" },
  { key: "falseReal", label: "False Real", color: "#7a2e26" },
  { key: "falseFake", label: "False Fake", color: "#8e631a" },
  { key: "trueReal", label: "True Real", color: "#f5a623" },
];

function buildRocData(stats) {
  return MODEL_ORDER.map((model) => ({
    model: model.label,
    rocAuc: stats?.models?.[model.key]?.test?.roc_auc ?? 0,
  }));
}

function buildConfusionData(stats) {
  return MODEL_ORDER.map((model) => {
    const matrix = stats?.models?.[model.key]?.test?.confusion_matrix || [
      [0, 0],
      [0, 0],
    ];
    return {
      model: model.label,
      trueFake: matrix[0][0] ?? 0,
      falseReal: matrix[0][1] ?? 0,
      falseFake: matrix[1][0] ?? 0,
      trueReal: matrix[1][1] ?? 0,
    };
  });
}

function MetricsCharts({ stats }) {
  const rocData = buildRocData(stats);
  const confusionData = buildConfusionData(stats);

  return (
    <div className="chart-grid">
      <div className="panel chart-panel">
        <div className="panel-header">
          <span className="eyebrow">ROC-AUC</span>
          <h3>Test-set discrimination by model</h3>
        </div>

        <div className="chart-box">
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={rocData}>
              <CartesianGrid stroke="#24303c" vertical={false} />
              <XAxis dataKey="model" stroke="#97a6b5" tickLine={false} axisLine={false} />
              <YAxis domain={[0, 1]} stroke="#97a6b5" tickLine={false} axisLine={false} />
              <Tooltip
                cursor={{ fill: "rgba(245, 166, 35, 0.08)" }}
                contentStyle={{ background: "#111821", border: "1px solid #293847", color: "#f3f5f7" }}
                formatter={(value) => [value, "ROC-AUC"]}
              />
              <Bar dataKey="rocAuc" radius={[8, 8, 0, 0]} fill="#f5a623" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="panel chart-panel">
        <div className="panel-header">
          <span className="eyebrow">Confusion Matrix</span>
          <h3>Test-set class outcomes across models</h3>
        </div>

        <div className="chart-box">
          <ResponsiveContainer width="100%" height={320}>
            <BarChart data={confusionData} layout="vertical" margin={{ left: 24, right: 12 }}>
              <CartesianGrid stroke="#24303c" horizontal={false} />
              <XAxis type="number" stroke="#97a6b5" tickLine={false} axisLine={false} />
              <YAxis
                type="category"
                dataKey="model"
                stroke="#97a6b5"
                tickLine={false}
                axisLine={false}
                width={120}
              />
              <Tooltip
                cursor={{ fill: "rgba(245, 166, 35, 0.08)" }}
                contentStyle={{ background: "#111821", border: "1px solid #293847", color: "#f3f5f7" }}
                formatter={(value, name) => [value, name]}
              />
              <Legend />
              {CONFUSION_KEYS.map((entry) => (
                <Bar
                  key={entry.key}
                  dataKey={entry.key}
                  name={entry.label}
                  stackId="confusion"
                  fill={entry.color}
                  radius={entry.key === "trueReal" ? [0, 8, 8, 0] : [0, 0, 0, 0]}
                />
              ))}
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}

export default MetricsCharts;
