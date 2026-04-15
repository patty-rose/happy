import { useState } from "react";
import axios from "axios";
import "./PromptBar.css";

const API = "/api";

export default function PromptBar({ onAdd, setLoading, loading }) {
  const [value, setValue] = useState("");
  const [error, setError] = useState(null);

  const submit = async (e) => {
    e.preventDefault();
    if (!value.trim()) return;
    setError(null);
    setLoading(true);
    const query = value;
    try {
      const { data } = await axios.post(`${API}/query`, { prompt: query });
      const now = Date.now();
      const widgets = (data.widgets || []).map((w, i) => ({
        id: `widget-${now}-${i}`,
        ...w,
      }));
      onAdd({ query, reasoning: data.reasoning || "", widgets });
      setValue("");
    } catch (err) {
      setError(err.response?.data?.detail ?? "Something went wrong");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="prompt-bar-wrap">
      <form className="prompt-bar" onSubmit={submit}>
        <input
          className="prompt-input"
          placeholder='e.g. "Show me data about vacant spaces in downtown Portland"'
          value={value}
          onChange={(e) => setValue(e.target.value)}
          disabled={loading}
        />
        <button className="prompt-btn" type="submit" disabled={loading || !value.trim()}>
          {loading ? "Thinking..." : "Show me"}
        </button>
      </form>
      {error && <div className="prompt-error">{error}</div>}
    </div>
  );
}
