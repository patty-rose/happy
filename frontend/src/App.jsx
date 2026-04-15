import { useState } from "react";
import PromptBar from "./components/PromptBar";
import Widget from "./components/Widget";
import "./App.css";

export default function App() {
  const [sections, setSections] = useState([]);
  const [loading, setLoading] = useState(false);

  const addSection = ({ query, reasoning, widgets }) => {
    const id = `section-${Date.now()}`;
    setSections((prev) => [...prev, { id, query, reasoning, widgets }]);
  };

  const removeWidget = (sectionId, widgetId) => {
    setSections((prev) =>
      prev
        .map((s) =>
          s.id === sectionId
            ? { ...s, widgets: s.widgets.filter((w) => w.id !== widgetId) }
            : s
        )
        .filter((s) => s.widgets.length > 0)
    );
  };

  return (
    <div className="app">
      <header className="app-header">
        <div className="logo">happy</div>
        <div className="subtitle">Portland Policy Dashboard</div>
      </header>

      <PromptBar onAdd={addSection} setLoading={setLoading} loading={loading} />

      {sections.length === 0 && !loading && (
        <div className="empty-state">
          <p>Ask about any Portland policy topic and get a curated set of relevant data.<br />
            <em>"Show me data about vacant spaces in downtown Portland"</em>
          </p>
        </div>
      )}

      {loading && <div className="loading-bar">Selecting relevant datasets...</div>}

      <div className="sections">
        {sections.map((section) => (
          <div key={section.id} className="section">
            <div className="section-header">
              <div className="section-query">"{section.query}"</div>
              {section.reasoning && (
                <div className="section-reasoning">{section.reasoning}</div>
              )}
            </div>
            <div className="widget-grid">
              {section.widgets.map((w) => (
                <Widget
                  key={w.id}
                  config={w}
                  onRemove={() => removeWidget(section.id, w.id)}
                />
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
