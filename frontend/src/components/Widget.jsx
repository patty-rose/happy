import { useEffect, useState } from "react";
import axios from "axios";
import {
  LineChart, Line, BarChart, Bar,
  XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
} from "recharts";
import "./Widget.css";

const API = "http://localhost:8000";

export default function Widget({ config, onRemove }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (config.source === "fred" && config.series_id) {
      axios.get(`${API}/data/fred/${config.series_id}`)
        .then((r) => setData(r.data.data))
        .catch(() => setError("Failed to load data"));
    }
  }, [config.series_id, config.source]);

  const formatDate = (d) => {
    const dt = new Date(d);
    return `${dt.getFullYear()} Q${Math.floor(dt.getMonth() / 3) + 1}`;
  };

  const renderChart = () => {
    if (error) return <div className="widget-error">{error}</div>;
    if (!data) return <div className="widget-loading">Loading...</div>;
    if (data.length === 0) return <div className="widget-error">No data</div>;

    if (config.type === "stat") {
      const latest = data[data.length - 1];
      const prev = data[data.length - 2];
      const delta = prev ? latest.value - prev.value : null;
      return (
        <div className="widget-stat">
          <div className="stat-value">{latest.value.toLocaleString()}</div>
          {delta !== null && (
            <div className={`stat-delta ${delta >= 0 ? "up" : "down"}`}>
              {delta >= 0 ? "▲" : "▼"} {Math.abs(delta).toFixed(2)}
            </div>
          )}
          <div className="stat-date">{latest.date}</div>
        </div>
      );
    }

    const tickFormatter = (v) => {
      const n = parseFloat(v);
      return n >= 1000 ? `${(n / 1000).toFixed(0)}k` : String(n);
    };

    const commonProps = {
      data,
      margin: { top: 4, right: 8, left: -16, bottom: 0 },
    };

    const xAxis = (
      <XAxis
        dataKey="date"
        tickFormatter={(d) => new Date(d).getFullYear()}
        tick={{ fontSize: 11, fill: "#64748b" }}
        axisLine={false}
        tickLine={false}
        interval="preserveStartEnd"
      />
    );
    const yAxis = (
      <YAxis
        tickFormatter={tickFormatter}
        tick={{ fontSize: 11, fill: "#64748b" }}
        axisLine={false}
        tickLine={false}
        width={48}
      />
    );
    const tooltip = (
      <Tooltip
        contentStyle={{ background: "#1e2130", border: "1px solid #2e3347", borderRadius: 6, fontSize: 12 }}
        labelStyle={{ color: "#94a3b8" }}
        itemStyle={{ color: "#a78bfa" }}
        labelFormatter={(d) => d}
      />
    );

    if (config.type === "bar") {
      return (
        <ResponsiveContainer width="100%" height="100%">
          <BarChart {...commonProps}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e2130" />
            {xAxis}{yAxis}{tooltip}
            <Bar dataKey="value" fill="#7c3aed" radius={[2, 2, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      );
    }

    return (
      <ResponsiveContainer width="100%" height="100%">
        <LineChart {...commonProps}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e2130" />
          {xAxis}{yAxis}{tooltip}
          <Line
            type="monotone"
            dataKey="value"
            stroke="#7c3aed"
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4 }}
          />
        </LineChart>
      </ResponsiveContainer>
    );
  };

  return (
    <div className="widget">
      <div className="widget-header widget-drag-handle">
        <div className="widget-title">{config.title}</div>
        <button className="widget-remove" onClick={onRemove}>✕</button>
      </div>
      {config.description && (
        <div className="widget-description">{config.description}</div>
      )}
      <div className="widget-body">{renderChart()}</div>
    </div>
  );
}
