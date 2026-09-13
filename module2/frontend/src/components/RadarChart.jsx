import {
  Chart as ChartJS,
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend,
} from "chart.js";
import { Radar } from "react-chartjs-2";

ChartJS.register(RadialLinearScale, PointElement, LineElement, Filler, Tooltip, Legend);

const AXIS_LABELS = {
  completeness: "Completeness",
  machine_readability: "Machine\nReadability",
  retrievability: "Retrievability",
  answerability: "Answerability",
  transactability: "Transactability",
};

export default function RadarChart({ axes }) {
  const keys = Object.keys(AXIS_LABELS);
  const values = keys.map((k) => axes?.[k] ?? 0);

  const data = {
    labels: keys.map((k) => AXIS_LABELS[k]),
    datasets: [
      {
        label: "AEO Score",
        data: values,
        backgroundColor: "rgba(99, 102, 241, 0.18)",
        borderColor: "rgba(99, 102, 241, 0.9)",
        pointBackgroundColor: "rgba(129, 140, 248, 1)",
        pointBorderColor: "#fff",
        pointBorderWidth: 2,
        pointRadius: 5,
        borderWidth: 2,
        fill: true,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: true,
    scales: {
      r: {
        min: 0,
        max: 100,
        ticks: {
          stepSize: 25,
          color: "rgba(139, 144, 176, 0.6)",
          backdropColor: "transparent",
          font: { size: 10 },
        },
        grid: { color: "rgba(255,255,255,0.06)" },
        angleLines: { color: "rgba(255,255,255,0.06)" },
        pointLabels: {
          color: "#8b90b0",
          font: { size: 11, family: "Inter, sans-serif", weight: "500" },
        },
      },
    },
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: "rgba(20, 22, 32, 0.95)",
        borderColor: "rgba(99,102,241,0.4)",
        borderWidth: 1,
        titleColor: "#f0f2ff",
        bodyColor: "#8b90b0",
        padding: 10,
        callbacks: {
          label: (ctx) => ` ${ctx.parsed.r.toFixed(1)} / 100`,
        },
      },
    },
  };

  return (
    <div style={{ maxWidth: 380, margin: "0 auto" }}>
      <Radar data={data} options={options} />
    </div>
  );
}
