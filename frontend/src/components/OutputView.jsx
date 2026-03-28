import { useState, useEffect } from "react";
import { STAGES } from "./ProgressTracker";

const API_URL = "http://localhost:8000";

const STAGE_FILES = [
  { stage: "Stage 2 — Raw Extraction", file: "structured_data_raw.json" },
  { stage: "Stage 2.5 — Verified Data", file: "structured_data_verified.json" },
  { stage: "Stage 2.5 — Verification Result", file: "verification_result.json" },
  { stage: "Stage 2.7 — Enriched Data", file: "structured_data_final.json" },
  { stage: "Stage 3 — Script Draft", file: "scene_script_draft.json" },
  { stage: "Stage 3.5 — Script Final", file: "scene_script_final.json" },
  { stage: "Stage 5 — Script with Durations", file: "scene_script_with_durations.json" },
];

export default function OutputView({ onResumeRun }) {
  const [runs, setRuns] = useState([]);
  const [expandedRun, setExpandedRun] = useState(null);
  const [expandedFile, setExpandedFile] = useState(null);
  const [fileData, setFileData] = useState({});
  const [loading, setLoading] = useState(true);
  const [resumeStage, setResumeStage] = useState({});

  useEffect(() => {
    fetchRuns();
  }, []);

  async function fetchRuns() {
    setLoading(true);
    try {
      const resp = await fetch(`${API_URL}/api/runs`);
      if (resp.ok) {
        const data = await resp.json();
        setRuns(data);
        if (data.length > 0) setExpandedRun(data[0].run_id);
      }
    } catch {}
    setLoading(false);
  }

  async function fetchFile(runId, filename) {
    const key = `${runId}/${filename}`;
    if (fileData[key]) return;
    try {
      const resp = await fetch(`${API_URL}/api/runs/${runId}/files/${filename}`);
      if (resp.ok) {
        const data = await resp.json();
        setFileData((prev) => ({ ...prev, [key]: data }));
      }
    } catch {}
  }

  function toggleRun(runId) {
    setExpandedRun(expandedRun === runId ? null : runId);
    setExpandedFile(null);
  }

  function toggleFile(runId, filename) {
    const key = `${runId}/${filename}`;
    if (expandedFile === key) {
      setExpandedFile(null);
    } else {
      setExpandedFile(key);
      fetchFile(runId, filename);
    }
  }

  if (loading) {
    return (
      <div className="output-empty">
        <p>Loading runs...</p>
      </div>
    );
  }

  if (runs.length === 0) {
    return (
      <div className="output-empty">
        <p>No pipeline runs yet. Run the pipeline first.</p>
      </div>
    );
  }

  return (
    <div className="output-view">
      <div className="output-stages">
        <div className="runs-header">
          <h2>Pipeline Runs ({runs.length})</h2>
          <button className="refresh-btn" onClick={fetchRuns}>Refresh</button>
        </div>

        {runs.map((run) => {
          const isExpanded = expandedRun === run.run_id;
          const created = run.created_at
            ? new Date(run.created_at).toLocaleString()
            : run.run_id;
          const selectedStage = resumeStage[run.run_id] || "stage5";

          return (
            <div className="run-card" key={run.run_id}>
              {/* Run header */}
              <div className="run-header" onClick={() => toggleRun(run.run_id)}>
                <div className="run-header-left">
                  <span className={`output-chevron ${isExpanded ? "open" : ""}`}>&#9654;</span>
                  <div className="run-info">
                    <span className="run-product">{run.product || "Unknown Product"}</span>
                    <span className="run-meta-line">
                      {created} &middot; {run.total_scenes || "?"} scenes &middot; {run.total_audio_sec || "?"}s audio
                    </span>
                    <span className="run-meta-line">
                      {run.quality_mode && <span className="run-badge mode">{run.quality_mode}</span>}
                      {run.image_provider && <span className="run-badge provider">{run.image_provider}</span>}
                      {run.tts_provider && <span className="run-badge provider">{run.tts_provider}</span>}
                      {run.gemini_model && <span className="run-badge model">{run.gemini_model}</span>}
                    </span>
                  </div>
                </div>
                <div className="run-header-right">
                  {run.has_video && (
                    <a
                      className="run-download-btn"
                      href={`${API_URL}/api/runs/${run.run_id}/video`}
                      download
                      onClick={(e) => e.stopPropagation()}
                    >
                      Download MP4
                    </a>
                  )}
                  <span className="run-id-badge">{run.run_id}</span>
                </div>
              </div>

              {/* Expanded content */}
              {isExpanded && (
                <div className="run-body">
                  {/* Resume controls */}
                  {onResumeRun && (
                    <div className="resume-controls">
                      <span className="resume-label">Resume from:</span>
                      <select
                        className="resume-select"
                        value={selectedStage}
                        onChange={(e) => {
                          e.stopPropagation();
                          setResumeStage((prev) => ({ ...prev, [run.run_id]: e.target.value }));
                        }}
                      >
                        {STAGES.map((s) => (
                          <option key={s.key} value={s.key}>{s.label}</option>
                        ))}
                      </select>
                      <button
                        className="resume-run-btn"
                        onClick={(e) => {
                          e.stopPropagation();
                          onResumeRun(run.run_id, selectedStage, run.source);
                        }}
                      >
                        Resume Run
                      </button>
                    </div>
                  )}

                  {/* Stage files */}
                  {STAGE_FILES.map(({ stage, file }) => {
                    const key = `${run.run_id}/${file}`;
                    const isFileExpanded = expandedFile === key;
                    const available = run.files && run.files.includes(file);
                    const data = fileData[key];

                    return (
                      <div className="output-stage-card" key={file}>
                        <div
                          className="output-stage-header"
                          onClick={() => available && toggleFile(run.run_id, file)}
                          style={{ cursor: available ? "pointer" : "default" }}
                        >
                          <div className="output-stage-left">
                            <span className={`output-chevron ${isFileExpanded ? "open" : ""}`}>&#9654;</span>
                            <span className="output-stage-name">{stage}</span>
                          </div>
                          <span className="output-file-name">{file}</span>
                          {available ? (
                            <span className="output-status available">available</span>
                          ) : (
                            <span className="output-status missing">not found</span>
                          )}
                        </div>
                        {isFileExpanded && data && (
                          <div className="output-stage-body">
                            <pre className="output-json">{JSON.stringify(data, null, 2)}</pre>
                          </div>
                        )}
                        {isFileExpanded && !data && available && (
                          <div className="output-stage-body">
                            <p className="output-loading">Loading...</p>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
