import { useState } from "react";
import GridLayout from "react-grid-layout";
import "react-grid-layout/css/styles.css";
import PromptBar from "./components/PromptBar";
import Widget from "./components/Widget";
import "./App.css";

const COLS = 12;
const ROW_HEIGHT = 80;
const WIDGET_W = 4;
const WIDGET_H = 4;

export default function App() {
  const [widgets, setWidgets] = useState([]);
  const [layout, setLayout] = useState([]);
  const [loading, setLoading] = useState(false);

  const addMany = (configs) => {
    const now = Date.now();
    const newWidgets = configs.map((config, i) => ({
      id: `widget-${now}-${i}`,
      ...config,
    }));
    const newLayout = newWidgets.map((w, i) => ({
      i: w.id,
      x: (i * WIDGET_W) % COLS,
      y: Infinity,
      w: WIDGET_W,
      h: WIDGET_H,
      minW: 3,
      minH: 3,
    }));
    setWidgets((prev) => [...prev, ...newWidgets]);
    setLayout((prev) => [...prev, ...newLayout]);
  };

  const removeWidget = (id) => {
    setWidgets((prev) => prev.filter((w) => w.id !== id));
    setLayout((prev) => prev.filter((l) => l.i !== id));
  };

  return (
    <div className="app">
      <header className="app-header">
        <div className="logo">happy</div>
        <div className="subtitle">Portland Policy Dashboard</div>
      </header>

      <PromptBar onAddMany={addMany} setLoading={setLoading} loading={loading} />

      {widgets.length === 0 && !loading && (
        <div className="empty-state">
          <p>Ask about any Portland policy topic and get a set of relevant data widgets.<br />
            <em>"Show me data about vacant lots in downtown Portland"</em>
          </p>
        </div>
      )}

      {loading && <div className="loading-bar">Selecting relevant datasets...</div>}

      <GridLayout
        className="grid"
        layout={layout}
        cols={COLS}
        rowHeight={ROW_HEIGHT}
        width={window.innerWidth - 48}
        onLayoutChange={setLayout}
        draggableHandle=".widget-drag-handle"
      >
        {widgets.map((w) => (
          <div key={w.id}>
            <Widget config={w} onRemove={() => removeWidget(w.id)} />
          </div>
        ))}
      </GridLayout>
    </div>
  );
}
