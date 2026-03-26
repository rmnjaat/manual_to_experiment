import ProgressTracker from "./ProgressTracker";
import ScriptResults from "./ScriptResults";

export default function OutputView({
  progress,
  scenes,
  changelog,
  metadata,
  videoReady,
  apiUrl,
}) {
  const hasProgress = Object.keys(progress).length > 0;

  if (!hasProgress && !scenes) {
    return (
      <div className="output-empty">
        <p>No output yet. Run the pipeline first.</p>
      </div>
    );
  }

  return (
    <div className="output-view">
      {/* Video download */}
      {videoReady && (
        <div className="video-card">
          <h2>
            Video Ready
            {metadata &&
              ` — ${metadata.brand || ""} ${metadata.product_name || ""}`}
          </h2>
          <a
            href={`${apiUrl}/api/download-video`}
            className="download-btn"
            download
          >
            Download Video (MP4)
          </a>
        </div>
      )}

      {/* Pipeline progress — full details */}
      {hasProgress && <ProgressTracker progress={progress} />}

      {/* Full script results */}
      {scenes && <ScriptResults scenes={scenes} changelog={changelog} />}
    </div>
  );
}
