import { useState, useEffect, useRef } from "react";
import axios from "axios";
import PromptBar from "./components/PromptBar";
import Widget from "./components/Widget";
import "./App.css";

const API = "/api";
const MAX_VISIBLE_TABS = 4;

export default function App() {
  const [tabs, setTabs] = useState([]);          // [{id, query, reasoning, widgets}]
  const [activeId, setActiveId] = useState(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saveMsg, setSaveMsg] = useState(null);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef(null);

  // Close dropdown on outside click
  useEffect(() => {
    const handler = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target))
        setDropdownOpen(false);
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  // Load saved dashboard on mount
  useEffect(() => {
    axios.get(`${API}/dashboard`).then(({ data }) => {
      if (data.sections?.length) {
        setTabs(data.sections);
        setActiveId(data.sections[0].id);
      }
    }).catch(() => {});
  }, []);

  const addTab = ({ query, reasoning, widgets }) => {
    const id = `tab-${Date.now()}`;
    const tab = { id, query, reasoning, widgets };
    setTabs((prev) => [...prev, tab]);
    setActiveId(id);
  };

  // Update a single widget inside a tab (used by heal)
  const updateWidget = (tabId, widgetId, newConfig) => {
    setTabs((prev) => prev.map((t) =>
      t.id !== tabId ? t : {
        ...t,
        widgets: t.widgets.map((w) => w.id === widgetId ? { ...w, ...newConfig } : w),
      }
    ));
  };

  const removeWidget = (tabId, widgetId) => {
    setTabs((prev) => prev.map((t) =>
      t.id !== tabId ? t : { ...t, widgets: t.widgets.filter((w) => w.id !== widgetId) }
    ));
  };

  const removeTab = (tabId) => {
    setTabs((prev) => {
      const next = prev.filter((t) => t.id !== tabId);
      if (activeId === tabId) setActiveId(next[next.length - 1]?.id ?? null);
      return next;
    });
  };

  // Self-heal: called when a widget's data fetch fails (max 2 attempts)
  const healWidget = async (tabId, widgetId, config, errorMsg) => {
    if ((config._healAttempts ?? 0) >= 2) {
      removeWidget(tabId, widgetId);
      return;
    }
    updateWidget(tabId, widgetId, { _healing: true, _error: null });
    try {
      const { data } = await axios.post(`${API}/heal`, { config, error: errorMsg });
      if (data.fixed_config) {
        updateWidget(tabId, widgetId, {
          ...data.fixed_config,
          _healing: false,
          _error: null,
          _healAttempts: (config._healAttempts ?? 0) + 1,
        });
      } else {
        removeWidget(tabId, widgetId);
      }
    } catch {
      removeWidget(tabId, widgetId);
    }
  };

  const saveDashboard = async () => {
    setSaving(true);
    try {
      await axios.post(`${API}/dashboard`, { sections: tabs });
      setSaveMsg("Saved");
    } catch {
      setSaveMsg("Error");
    } finally {
      setSaving(false);
      setTimeout(() => setSaveMsg(null), 2500);
    }
  };

  const activeTab = tabs.find((t) => t.id === activeId);
  const visibleTabs = tabs.slice(0, MAX_VISIBLE_TABS);
  const overflowTabs = tabs.slice(MAX_VISIBLE_TABS);

  return (
    <div className="app">
      <header className="app-header">
        <div className="logo">happy</div>
        <div className="subtitle">Portland Policy Dashboard</div>
        <div className="header-actions">
          {tabs.length > 0 && (
            <button className="action-btn primary" onClick={saveDashboard} disabled={saving}>
              {saving ? "Saving..." : saveMsg || "Save"}
            </button>
          )}
        </div>
      </header>

      <PromptBar onAdd={addTab} setLoading={setLoading} loading={loading} />

      {/* Tab bar */}
      {tabs.length > 0 && (
        <div className="tab-bar">
          {visibleTabs.map((t) => (
            <button
              key={t.id}
              className={`tab ${t.id === activeId ? "tab-active" : ""}`}
              onClick={() => setActiveId(t.id)}
            >
              <span className="tab-label">{t.query.length > 32 ? t.query.slice(0, 30) + "…" : t.query}</span>
              <span className="tab-close" onClick={(e) => { e.stopPropagation(); removeTab(t.id); }}>×</span>
            </button>
          ))}
          {overflowTabs.length > 0 && (
            <div className="tab-overflow" ref={dropdownRef}>
              <button className="tab tab-more" onClick={() => setDropdownOpen((v) => !v)}>
                +{overflowTabs.length} more ▾
              </button>
              {dropdownOpen && (
                <div className="tab-dropdown">
                  {overflowTabs.map((t) => (
                    <button key={t.id} className="tab-dropdown-item"
                      onClick={() => { setActiveId(t.id); setDropdownOpen(false); }}>
                      {t.query.length > 48 ? t.query.slice(0, 46) + "…" : t.query}
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Active tab content */}
      {tabs.length === 0 && !loading && (
        <div className="empty-state">
          <p>Ask about any Portland policy topic and get a curated set of relevant data.<br />
            <em>"Show me data about vacant spaces in downtown Portland"</em>
          </p>
        </div>
      )}

      {loading && <div className="loading-bar">Selecting relevant datasets...</div>}

      {activeTab && (
        <div className="tab-content">
          {activeTab.reasoning && (
            <div className="tab-reasoning">
              <span className="reasoning-label">Why these metrics</span>
              {activeTab.reasoning}
            </div>
          )}
          <div className="widget-grid">
            {activeTab.widgets.map((w) => (
              <Widget
                key={w.id}
                config={w}
                onRemove={() => removeWidget(activeTab.id, w.id)}
                onError={(msg) => healWidget(activeTab.id, w.id, w, msg)}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
