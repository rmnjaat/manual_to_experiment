import { useState, useEffect } from "react";
import InputForm from "./components/InputForm";
import ProgressTracker from "./components/ProgressTracker";
import ScriptResults from "./components/ScriptResults";
import OutputView from "./components/OutputView";
import "./App.css";

const API_URL = "http://localhost:8000";
const STORAGE_KEY = "pipeline_last_run";

function App() {
  const [activeTab, setActiveTab] = useState("generate");
  const [running, setRunning] = useState(false);
  const [progress, setProgress] = useState({});
  const [scenes, setScenes] = useState(null);
  const [changelog, setChangelog] = useState([]);
  const [metadata, setMetadata] = useState(null);
  const [videoReady, setVideoReady] = useState(false);
  const [error, setError] = useState(null);

  // Load last run from localStorage on mount
  useEffect(() => {
    try {
      const saved = JSON.parse(localStorage.getItem(STORAGE_KEY));
      if (saved) {
        setScenes(saved.scenes || null);
        setChangelog(saved.changelog || []);
        setMetadata(saved.metadata || null);
        setProgress(saved.progress || {});
        setVideoReady(saved.videoReady || false);
      }
    } catch {}
  }, []);

  // Save to localStorage whenever results change
  useEffect(() => {
    if (scenes || Object.keys(progress).length > 0) {
      localStorage.setItem(
        STORAGE_KEY,
        JSON.stringify({ scenes, changelog, metadata, progress, videoReady })
      );
    }
  }, [scenes, changelog, metadata, progress, videoReady]);

  const handleSubmit = async (formData) => {
    setRunning(true);
    setProgress({});
    setScenes(null);
    setChangelog([]);
    setMetadata(null);
    setVideoReady(false);
    setError(null);

    try {
      const response = await fetch(`${API_URL}/api/generate`, {
        method: "POST",
        body: formData,
      });

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          const jsonStr = line.slice(6).trim();
          if (!jsonStr) continue;

          try {
            const msg = JSON.parse(jsonStr);

            if (msg.stage === "done" && msg.result) {
              setScenes(msg.result.scenes || []);
              setChangelog(msg.result.changelog || []);
              setMetadata(msg.result.metadata || null);
              if (msg.result.video_path) setVideoReady(true);
              setActiveTab("output");
            } else if (msg.stage === "error") {
              setError(msg.detail);
            } else {
              setProgress((prev) => ({
                ...prev,
                [msg.stage]: msg.detail || "working...",
              }));
            }
          } catch {
            // skip malformed JSON
          }
        }
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setRunning(false);
    }
  };

  return (
    <>
      <div className="app-header">
        <h1>Manual to Video Generator</h1>
        <p>Upload a product manual, get an instruction video</p>
      </div>

      <div className="tab-bar">
        <button
          className={`tab-btn ${activeTab === "generate" ? "active" : ""}`}
          onClick={() => setActiveTab("generate")}
        >
          Generate
        </button>
        <button
          className={`tab-btn ${activeTab === "output" ? "active" : ""}`}
          onClick={() => setActiveTab("output")}
          disabled={!scenes && Object.keys(progress).length === 0}
        >
          Output
        </button>
      </div>

      {activeTab === "generate" && (
        <>
          <InputForm onSubmit={handleSubmit} disabled={running} />

          {(running || Object.keys(progress).length > 0) && (
            <ProgressTracker progress={progress} />
          )}

          {error && (
            <div className="error-card">
              <strong>Error:</strong> {error}
            </div>
          )}
        </>
      )}

      {activeTab === "output" && (
        <OutputView
          progress={progress}
          scenes={scenes}
          changelog={changelog}
          metadata={metadata}
          videoReady={videoReady}
          apiUrl={API_URL}
        />
      )}
    </>
  );
}

export default App;
