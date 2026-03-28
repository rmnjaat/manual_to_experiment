import { useState, useEffect, useRef } from "react";
import InputForm from "./components/InputForm";
import ProgressTracker from "./components/ProgressTracker";
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
  const [lastRunId, setLastRunId] = useState(null);
  const formRef = useRef(null);

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
        setLastRunId(saved.lastRunId || null);
      }
    } catch {}
  }, []);

  // Save to localStorage whenever results change
  useEffect(() => {
    if (scenes || Object.keys(progress).length > 0) {
      localStorage.setItem(
        STORAGE_KEY,
        JSON.stringify({ scenes, changelog, metadata, progress, videoReady, lastRunId })
      );
    }
  }, [scenes, changelog, metadata, progress, videoReady, lastRunId]);

  const runPipeline = async (formData) => {
    setRunning(true);
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
              if (msg.result.run_id) setLastRunId(msg.result.run_id);
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

  const handleSubmit = async (formData) => {
    setProgress({});
    setScenes(null);
    setChangelog([]);
    setMetadata(null);
    setVideoReady(false);
    formRef.current = formData;
    await runPipeline(formData);
  };

  const handleResume = async (stageKey) => {
    if (!lastRunId || !formRef.current) {
      setError("Cannot resume — no previous run data. Submit a new run first.");
      return;
    }
    const fd = new FormData();
    for (const [key, value] of formRef.current.entries()) {
      fd.append(key, value);
    }
    fd.set("resume_run_id", lastRunId);
    fd.set("resume_from", stageKey);
    setError(null);
    await runPipeline(fd);
  };

  const handleResumeRun = async (runId, stageKey, source) => {
    setActiveTab("generate");
    setProgress({});
    setError(null);

    const fd = formRef.current ? new FormData() : new FormData();
    // If we have previous form data, copy it
    if (formRef.current) {
      for (const [key, value] of formRef.current.entries()) {
        fd.append(key, value);
      }
    }
    // Set the source from the run if available
    if (source && !fd.has("url") && !fd.has("pdf") && !fd.has("raw_text")) {
      if (source.startsWith("http")) {
        fd.set("url", source);
      } else {
        fd.set("raw_text", source);
      }
    }
    fd.set("resume_run_id", runId);
    fd.set("resume_from", stageKey);
    setLastRunId(runId);
    await runPipeline(fd);
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
        >
          Output
        </button>
      </div>

      {activeTab === "generate" && (
        <>
          <InputForm onSubmit={handleSubmit} disabled={running} />

          {(running || Object.keys(progress).length > 0) && (
            <ProgressTracker
              progress={progress}
              running={running}
              onResume={lastRunId ? handleResume : null}
            />
          )}

          {error && (
            <div className="error-card">
              <strong>Error:</strong> {error}
            </div>
          )}
        </>
      )}

      {activeTab === "output" && (
        <OutputView onResumeRun={handleResumeRun} />
      )}
    </>
  );
}

export default App;
