import { useState } from "react";
import axios from "axios";
import "./PromptBar.css";

const API = window.location.hostname === "localhost"
  ? "http://localhost:8000"
  : `${window.location.protocol}//${window.location.hostname}:8000`;

export default function PromptBar({ onAdd, setLoading, loading }) {
  const [value, setValue] = useState("");
  const [error, setError] = useState(null);

  const submit = async (e) => {
    e.preventDefault();
    if (!value.trim()) return;
    setError(null);
    setLoading(true);
    try {
      const { data } = await axios.post(`${API}/query`, { prompt: value });
      onAdd(data);
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
          placeholder="Ask about Portland data — unemployment, housing, transit..."
          value={value}
          onChange={(e) => setValue(e.target.value)}
          disabled={loading}
        />
        <button className="prompt-btn" type="submit" disabled={loading || !value.trim()}>
          {loading ? "..." : "Add widget"}
        </button>
      </form>
      {error && <div className="prompt-error">{error}</div>}
    </div>
  );
}
