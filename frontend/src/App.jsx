import { useState, useEffect } from "react";
import axios from "axios";
import PromptBar from "./components/PromptBar";
import Widget from "./components/Widget";
import "./App.css";

const API = "/api";

export default function App() {
  const [sections, setSections] = useState([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saveMsg, setSaveMsg] = useState(null);

  // Load saved dashboard on mount
  useEffect(() => {
    axios.get(`${API}/dashboard`).then(({ data }) => {
      if (data.sections?.length) setSections(data.sections);
    }).catch(() => {});
  }, []);

  const addSection = ({ query, reasoning, widgets }) => {
    const id = `section-${Date.now()}`;
    setSections((prev) => [...prev, { id, query, reasoning, widgets }]);
  };

  const removeWidget = (sectionId, widgetId) => {
    setSections((prev) =>
      prev
        .map((s) => s.id === sectionId
          ? { ...s, widgets: s.widgets.filter((w) => w.id !== widgetId) }
          : s)
        .filter((s) => s.widgets.length > 0)
    );
  };

  const clearAll = () => setSections([]);

  const saveDashboard = async () => {
    setSaving(true);
    setSaveMsg(null);
    try {
      await axios.post(`${API}/dashboard`, { sections });
      setSaveMsg("Saved");
    } catch {
      setSaveMsg("Save failed");
    } finally {
      setSaving(false);
      setTimeout(() => setSaveMsg(null), 2500);
    }
  };

  return (
    <div className="app">
      <header className="app-header">
        <div className="logo">happy</div>
        <div className="subtitle">Portland Policy Dashboard</div>
        <div className="header-actions">
          {sections.length > 0 && (
            <>
              <button className="action-btn secondary" onClick={clearAll}>Clear</button>
              <button className="action-btn primary" onClick={saveDashboard} disabled={saving}>
                {saving ? "Saving..." : saveMsg || "Save dashboard"}
              </button>
            </>
          )}
        </div>
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
