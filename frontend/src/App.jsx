import { useState } from "react";
import GridLayout from "react-grid-layout";
import "react-grid-layout/css/styles.css";
import "react-grid-layout/css/resizable.css";
import PromptBar from "./components/PromptBar";
import Widget from "./components/Widget";
import "./App.css";

const COLS = 12;
const ROW_HEIGHT = 80;

export default function App() {
  const [widgets, setWidgets] = useState([]);
  const [layout, setLayout] = useState([]);
  const [loading, setLoading] = useState(false);

  const addWidget = (config) => {
    const id = `widget-${Date.now()}`;
    const col = (widgets.length * 4) % COLS;
    setWidgets((prev) => [...prev, { id, ...config }]);
    setLayout((prev) => [
      ...prev,
      { i: id, x: col, y: Infinity, w: 4, h: 4, minW: 3, minH: 3 },
    ]);
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

      <PromptBar onAdd={addWidget} setLoading={setLoading} loading={loading} />

      {widgets.length === 0 && !loading && (
        <div className="empty-state">
          <p>Ask anything about Portland — e.g.<br />
            <em>"Show me Oregon unemployment over the last two years"</em>
          </p>
        </div>
      )}

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
