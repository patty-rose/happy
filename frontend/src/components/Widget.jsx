import { useEffect, useRef, useState } from "react";
import axios from "axios";
import {
  LineChart, Line, BarChart, Bar,
  XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
} from "recharts";
import "./Widget.css";

const API = "/api";

function fetchData(config) {
  const { source, series_id, dataset_id, year_field } = config;
  if (source === "bls" && series_id)
    return axios.get(`${API}/data/bls/${series_id}`);
  if (source === "worldbank" && series_id)
    return axios.get(`${API}/data/worldbank/${series_id}`);
  if (source === "portland" && dataset_id) {
    const yf = year_field || "YEAR_";
    return axios.get(`${API}/data/portland/${dataset_id}?year_field=${yf}`);
  }
  if (source === "portland_count" && dataset_id)
    return axios.get(`${API}/data/portland_count/${dataset_id}`);
  return null;
}

export default function Widget({ config, onRemove }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const bodyRef = useRef(null);
  const [bodyH, setBodyH] = useState(0);

  useEffect(() => {
    if (!bodyRef.current) return;
    const obs = new ResizeObserver(([e]) => {
      const h = e.contentRect.height;
      if (h > 0) setBodyH(h);
    });
    obs.observe(bodyRef.current);
    return () => obs.disconnect();
  }, []);

  useEffect(() => {
    const req = fetchData(config);
    if (!req) return;
    req.then((r) => setData(r.data.data)).catch(() => setError("Failed to load data"));
  }, [config.source, config.series_id, config.dataset_id, config.year_field]);

  const renderChart = () => {
    if (error) return <div className="widget-error">{error}</div>;
    if (!data || bodyH === 0) return <div className="widget-loading">Loading...</div>;
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
          <div className="stat-date">{latest.date.slice(0, 7)}</div>
        </div>
      );
    }

    const tickFormatter = (v) => {
      const n = parseFloat(v);
      return n >= 1000 ? `${(n / 1000).toFixed(0)}k` : String(n);
    };

    const commonProps = { data, margin: { top: 4, right: 8, left: -16, bottom: 0 } };

    const xAxis = (
      <XAxis dataKey="date" tickFormatter={(d) => new Date(d).getFullYear()}
        tick={{ fontSize: 11, fill: "#64748b" }} axisLine={false} tickLine={false}
        interval="preserveStartEnd" />
    );
    const yAxis = (
      <YAxis tickFormatter={tickFormatter}
        tick={{ fontSize: 11, fill: "#64748b" }} axisLine={false} tickLine={false} width={48} />
    );
    const tooltip = (
      <Tooltip
        contentStyle={{ background: "#1e2130", border: "1px solid #2e3347", borderRadius: 6, fontSize: 12 }}
        labelStyle={{ color: "#94a3b8" }} itemStyle={{ color: "#a78bfa" }}
        labelFormatter={(d) => d} />
    );

    if (config.type === "bar") {
      return (
        <ResponsiveContainer width="100%" height={bodyH}>
          <BarChart {...commonProps}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e2130" />
            {xAxis}{yAxis}{tooltip}
            <Bar dataKey="value" fill="#7c3aed" radius={[2, 2, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      );
    }

    return (
      <ResponsiveContainer width="100%" height={bodyH}>
        <LineChart {...commonProps}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e2130" />
          {xAxis}{yAxis}{tooltip}
          <Line type="monotone" dataKey="value" stroke="#7c3aed"
            strokeWidth={2} dot={false} activeDot={{ r: 4 }} />
        </LineChart>
      </ResponsiveContainer>
    );
  };

  const sourceLabel = {
    bls: "BLS",
    worldbank: "World Bank",
    portland: "Portland ArcGIS",
    portland_count: "Portland ArcGIS",
  }[config.source] || config.source;

  return (
    <div className="widget">
      <div className="widget-header">
        <div className="widget-title">{config.title}</div>
        <button className="widget-remove" onClick={onRemove}>✕</button>
      </div>
      {config.description && (
        <div className="widget-description">{config.description}</div>
      )}
      <div className="widget-body" ref={bodyRef}>{renderChart()}</div>
      <div className="widget-source">{sourceLabel}</div>
    </div>
  );
}
