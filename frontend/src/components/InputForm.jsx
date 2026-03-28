import { useState, useEffect } from "react";

const SOURCE_TYPES = ["pdf", "url", "text"];
const API_URL = "http://localhost:8000";

export default function InputForm({ onSubmit, disabled }) {
  const [sourceType, setSourceType] = useState("pdf");
  const [pdfFile, setPdfFile] = useState(null);
  const [url, setUrl] = useState("");
  const [rawText, setRawText] = useState("");
  const [showSettings, setShowSettings] = useState(false);
  const [expandedSection, setExpandedSection] = useState(null);

  // Defaults from server
  const [defaults, setDefaults] = useState(null);

  // Provider selection
  const [providers, setProviders] = useState({ tts: [], image: [], video: [] });
  const [selectedTts, setSelectedTts] = useState("");
  const [selectedImage, setSelectedImage] = useState("");
  const [selectedVideo, setSelectedVideo] = useState("");

  // Quality mode
  const [qualityMode, setQualityMode] = useState("standard");
  const [qualityModes, setQualityModes] = useState([]);

  // Settings
  const [geminiModel, setGeminiModel] = useState("gemini-2.5-flash");
  const [imagenModel, setImagenModel] = useState("imagen-4.0-fast-generate-001");
  const [ttsSpeed, setTtsSpeed] = useState(1.5);
  const [ttsLanguage, setTtsLanguage] = useState("en");
  const [imageStylePrefix, setImageStylePrefix] = useState("");
  const [imageStyleSuffix, setImageStyleSuffix] = useState("");

  // ElevenLabs
  const [elVoices, setElVoices] = useState([]);
  const [elModels, setElModels] = useState([]);
  const [elVoiceId, setElVoiceId] = useState("JBFqnCBsd6RMkjVDRZzb");
  const [elModelId, setElModelId] = useState("eleven_multilingual_v2");
  const [elSpeed, setElSpeed] = useState(1.0);
  const [elStability, setElStability] = useState(0.5);
  const [elSimilarity, setElSimilarity] = useState(0.75);

  // Prompts
  const [prompts, setPrompts] = useState({});

  // Fetch defaults + providers on mount
  useEffect(() => {
    fetch(`${API_URL}/api/defaults`)
      .then((r) => r.json())
      .then((data) => {
        setDefaults(data);
        setQualityMode(data.settings.quality_mode || "standard");
        if (data.quality_modes) setQualityModes(data.quality_modes);
        setGeminiModel(data.settings.gemini_model);
        setImagenModel(data.settings.imagen_model);
        setTtsSpeed(data.settings.tts_speed);
        setTtsLanguage(data.settings.tts_language);
        setImageStylePrefix(data.settings.image_style_prefix);
        setImageStyleSuffix(data.settings.image_style_suffix);
        setPrompts(data.prompts);
      })
      .catch(() => {});

    // Fetch ElevenLabs voices and models
    fetch(`${API_URL}/api/elevenlabs/voices`)
      .then((r) => r.json())
      .then((data) => { if (data.voices?.length) { setElVoices(data.voices); setElVoiceId(data.voices[0].voice_id); } })
      .catch(() => {});
    fetch(`${API_URL}/api/elevenlabs/models`)
      .then((r) => r.json())
      .then((data) => { if (data.models?.length) setElModels(data.models); })
      .catch(() => {});

    fetch(`${API_URL}/api/providers`)
      .then((r) => r.json())
      .then((data) => {
        setProviders(data);
        if (data.tts.length) setSelectedTts(data.tts[0]);
        if (data.image.length) setSelectedImage(data.image[0]);
        if (data.video.length) setSelectedVideo(data.video[0]);
      })
      .catch(() => {});
  }, []);

  const handleSubmit = (e) => {
    e.preventDefault();
    const fd = new FormData();

    if (sourceType === "pdf" && pdfFile) fd.append("pdf", pdfFile);
    else if (sourceType === "url") fd.append("url", url);
    else if (sourceType === "text") fd.append("raw_text", rawText);

    fd.append("quality_mode", qualityMode);
    fd.append("tts_provider", selectedTts);
    fd.append("image_provider", selectedImage);
    fd.append("video_provider", selectedVideo);
    fd.append("gemini_model", geminiModel);
    fd.append("imagen_model", imagenModel);
    fd.append("tts_speed", ttsSpeed);
    fd.append("tts_language", ttsLanguage);
    fd.append("image_style_prefix", imageStylePrefix);
    fd.append("image_style_suffix", imageStyleSuffix);
    fd.append("elevenlabs_voice_id", elVoiceId);
    fd.append("elevenlabs_model_id", elModelId);
    fd.append("elevenlabs_speed", elSpeed);
    fd.append("elevenlabs_stability", elStability);
    fd.append("elevenlabs_similarity", elSimilarity);

    // Send prompts
    Object.entries(prompts).forEach(([key, val]) => {
      fd.append(key, val);
    });

    onSubmit(fd);
  };

  const canSubmit =
    (sourceType === "pdf" && pdfFile) ||
    (sourceType === "url" && url.trim()) ||
    (sourceType === "text" && rawText.trim());

  const toggleSection = (name) =>
    setExpandedSection(expandedSection === name ? null : name);

  const updatePrompt = (key, val) =>
    setPrompts((prev) => ({ ...prev, [key]: val }));

  return (
    <form className="form-card" onSubmit={handleSubmit}>
      {/* Source type toggle */}
      <div className="source-toggle">
        {SOURCE_TYPES.map((t) => (
          <button
            key={t}
            type="button"
            className={sourceType === t ? "active" : ""}
            onClick={() => setSourceType(t)}
          >
            {t === "pdf" ? "Upload PDF" : t === "url" ? "Paste URL" : "Raw Text"}
          </button>
        ))}
      </div>

      {/* Source input */}
      {sourceType === "pdf" && (
        <div className="input-group">
          <label>PDF Manual</label>
          <div className="file-input-wrapper">
            <input type="file" accept=".pdf" onChange={(e) => setPdfFile(e.target.files[0])} />
          </div>
          {pdfFile && <div className="file-name">{pdfFile.name}</div>}
        </div>
      )}
      {sourceType === "url" && (
        <div className="input-group">
          <label>Manual URL</label>
          <input type="url" placeholder="https://example.com/product" value={url} onChange={(e) => setUrl(e.target.value)} />
        </div>
      )}
      {sourceType === "text" && (
        <div className="input-group">
          <label>Product Description / Manual Text</label>
          <textarea placeholder="Paste text here..." value={rawText} onChange={(e) => setRawText(e.target.value)} />
        </div>
      )}

      {/* Quality Mode Selector */}
      {qualityModes.length > 0 && (
        <div className="quality-mode-section">
          <label className="quality-mode-label">Video Quality Mode</label>
          <div className="quality-mode-cards">
            {qualityModes.map((mode) => (
              <div
                key={mode.value}
                className={`quality-mode-card ${qualityMode === mode.value ? "active" : ""}`}
                onClick={() => setQualityMode(mode.value)}
              >
                <div className="qm-icon">
                  {mode.value === "standard" ? "\u{1F4F7}" : mode.value === "enhanced" ? "\u{1F3AC}" : "\u{1F3A5}"}
                </div>
                <div className="qm-label">{mode.label}</div>
                <div className="qm-desc">{mode.description}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Settings toggle */}
      <div className="settings-toggle" onClick={() => setShowSettings(!showSettings)}>
        <span className={`settings-chevron ${showSettings ? "open" : ""}`}>&#9654;</span>
        <span>Pipeline Settings</span>
      </div>

      {showSettings && !defaults && (
        <div className="settings-panel" style={{color:"#666",padding:"1rem",textAlign:"center"}}>
          Loading settings...
        </div>
      )}
      {showSettings && defaults && (
        <div className="settings-panel">

          {/* ── General ── */}
          <div className="settings-section">
            <div className="settings-section-header" onClick={() => toggleSection("general")}>
              <span className={`output-chevron ${expandedSection === "general" ? "open" : ""}`}>&#9654;</span>
              <span>General Settings</span>
            </div>
            {expandedSection === "general" && (
              <div className="settings-section-body">
                <div className="settings-row">
                  <div className="input-group">
                    <label>Gemini Model (LLM for all stages)</label>
                    <select value={geminiModel} onChange={(e) => setGeminiModel(e.target.value)}>
                      {defaults.gemini_models.map((m) => (
                        <option key={m.value} value={m.value}>{m.label}</option>
                      ))}
                    </select>
                  </div>
                  <div className="input-group">
                    <label>Imagen Model (Image generation)</label>
                    <select value={imagenModel} onChange={(e) => setImagenModel(e.target.value)}>
                      {defaults.imagen_models.map((m) => (
                        <option key={m.value} value={m.value}>{m.label}</option>
                      ))}
                    </select>
                  </div>
                </div>
                <div className="settings-row">
                  <div className="input-group">
                    <label>TTS Speed: {ttsSpeed}x</label>
                    <input type="range" min="0.8" max="2.0" step="0.1" value={ttsSpeed}
                      onChange={(e) => setTtsSpeed(parseFloat(e.target.value))} />
                    <div className="slider-labels"><span>0.8x</span><span>1.0x</span><span>1.5x</span><span>2.0x</span></div>
                  </div>
                  <div className="input-group">
                    <label>TTS Language</label>
                    <select value={ttsLanguage} onChange={(e) => setTtsLanguage(e.target.value)}>
                      {defaults.languages.map((l) => (
                        <option key={l.value} value={l.value}>{l.label}</option>
                      ))}
                    </select>
                  </div>
                </div>
                {/* Provider selection */}
                <div className="settings-row">
                  {providers.image.length > 0 && (
                    <div className="input-group">
                      <label>Image Provider</label>
                      <select value={selectedImage} onChange={(e) => setSelectedImage(e.target.value)}>
                        {providers.image.map((p) => (<option key={p} value={p}>{p}</option>))}
                      </select>
                    </div>
                  )}
                  {providers.tts.length > 0 && (
                    <div className="input-group">
                      <label>TTS Provider</label>
                      <select value={selectedTts} onChange={(e) => setSelectedTts(e.target.value)}>
                        {providers.tts.map((p) => (<option key={p} value={p}>{p}</option>))}
                      </select>
                    </div>
                  )}
                  {providers.video.length > 0 && (
                    <div className="input-group">
                      <label>Video Provider</label>
                      <select value={selectedVideo} onChange={(e) => setSelectedVideo(e.target.value)}>
                        {providers.video.map((p) => (<option key={p} value={p}>{p}</option>))}
                      </select>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* ── ElevenLabs ── */}
          {elVoices.length > 0 && (
            <div className="settings-section">
              <div className="settings-section-header" onClick={() => toggleSection("elevenlabs")}>
                <span className={`output-chevron ${expandedSection === "elevenlabs" ? "open" : ""}`}>&#9654;</span>
                <span>Stage 5 — ElevenLabs Voice Settings</span>
              </div>
              {expandedSection === "elevenlabs" && (
                <div className="settings-section-body">
                  <div className="settings-row">
                    <div className="input-group">
                      <label>Voice</label>
                      <select value={elVoiceId} onChange={(e) => setElVoiceId(e.target.value)}>
                        {elVoices.map((v) => (
                          <option key={v.voice_id} value={v.voice_id}>
                            {v.name} {v.category ? `(${v.category})` : ""}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div className="input-group">
                      <label>Model</label>
                      <select value={elModelId} onChange={(e) => setElModelId(e.target.value)}>
                        {elModels.map((m) => (
                          <option key={m.model_id} value={m.model_id}>{m.name}</option>
                        ))}
                      </select>
                    </div>
                  </div>
                  <div className="settings-row">
                    <div className="input-group">
                      <label>Speed: {elSpeed}x</label>
                      <input type="range" min="0.7" max="1.2" step="0.05" value={elSpeed}
                        onChange={(e) => setElSpeed(parseFloat(e.target.value))} />
                      <div className="slider-labels"><span>0.7x</span><span>1.0x</span><span>1.2x</span></div>
                    </div>
                    <div className="input-group">
                      <label>Stability: {elStability}</label>
                      <input type="range" min="0" max="1" step="0.05" value={elStability}
                        onChange={(e) => setElStability(parseFloat(e.target.value))} />
                      <div className="slider-labels"><span>Variable</span><span>Stable</span></div>
                    </div>
                  </div>
                  <div className="settings-row">
                    <div className="input-group">
                      <label>Similarity Boost: {elSimilarity}</label>
                      <input type="range" min="0" max="1" step="0.05" value={elSimilarity}
                        onChange={(e) => setElSimilarity(parseFloat(e.target.value))} />
                      <div className="slider-labels"><span>Low</span><span>High</span></div>
                    </div>
                  </div>
                  <p style={{fontSize:"0.7rem",color:"#555",marginTop:"0.5rem"}}>
                    Select "elevenlabs" as TTS Provider in General Settings to use these.
                  </p>
                </div>
              )}
            </div>
          )}

          {/* ── Image Style ── */}
          <div className="settings-section">
            <div className="settings-section-header" onClick={() => toggleSection("image")}>
              <span className={`output-chevron ${expandedSection === "image" ? "open" : ""}`}>&#9654;</span>
              <span>Stage 4 — Image Generation Style</span>
            </div>
            {expandedSection === "image" && (
              <div className="settings-section-body">
                <div className="input-group">
                  <label>Style Prefix (prepended to every image prompt)</label>
                  <textarea className="prompt-textarea" value={imageStylePrefix}
                    onChange={(e) => setImageStylePrefix(e.target.value)} />
                </div>
                <div className="input-group">
                  <label>Style Suffix (appended to every image prompt)</label>
                  <textarea className="prompt-textarea" value={imageStyleSuffix}
                    onChange={(e) => setImageStyleSuffix(e.target.value)} />
                </div>
              </div>
            )}
          </div>

          {/* ── Stage 2: Extraction ── */}
          <div className="settings-section">
            <div className="settings-section-header" onClick={() => toggleSection("s2")}>
              <span className={`output-chevron ${expandedSection === "s2" ? "open" : ""}`}>&#9654;</span>
              <span>Stage 2 — Extraction Prompts</span>
            </div>
            {expandedSection === "s2" && (
              <div className="settings-section-body">
                <div className="input-group">
                  <label>Call 1: Extraction Prompt</label>
                  <textarea className="prompt-textarea tall" value={prompts.extraction_prompt || ""}
                    onChange={(e) => updatePrompt("extraction_prompt", e.target.value)} />
                </div>
                <div className="input-group">
                  <label>Call 2: Verification — System Prompt</label>
                  <textarea className="prompt-textarea" value={prompts.verification_system || ""}
                    onChange={(e) => updatePrompt("verification_system", e.target.value)} />
                </div>
                <div className="input-group">
                  <label>Call 2: Verification — User Prompt Template</label>
                  <textarea className="prompt-textarea tall" value={prompts.verification_user || ""}
                    onChange={(e) => updatePrompt("verification_user", e.target.value)} />
                </div>
                <div className="input-group">
                  <label>Call 3: Enrichment — System Prompt</label>
                  <textarea className="prompt-textarea" value={prompts.enrichment_system || ""}
                    onChange={(e) => updatePrompt("enrichment_system", e.target.value)} />
                </div>
                <div className="input-group">
                  <label>Call 3: Enrichment — User Prompt Template</label>
                  <textarea className="prompt-textarea tall" value={prompts.enrichment_user || ""}
                    onChange={(e) => updatePrompt("enrichment_user", e.target.value)} />
                </div>
              </div>
            )}
          </div>

          {/* ── Stage 3: Script ── */}
          <div className="settings-section">
            <div className="settings-section-header" onClick={() => toggleSection("s3")}>
              <span className={`output-chevron ${expandedSection === "s3" ? "open" : ""}`}>&#9654;</span>
              <span>Stage 3 — Script Generation Prompts</span>
            </div>
            {expandedSection === "s3" && (
              <div className="settings-section-body">
                <div className="input-group">
                  <label>Call 4: Script — System Prompt</label>
                  <textarea className="prompt-textarea" value={prompts.script_system || ""}
                    onChange={(e) => updatePrompt("script_system", e.target.value)} />
                </div>
                <div className="input-group">
                  <label>Call 4: Script — User Prompt Template</label>
                  <textarea className="prompt-textarea tall" value={prompts.script_prompt || ""}
                    onChange={(e) => updatePrompt("script_prompt", e.target.value)} />
                </div>
                <div className="input-group">
                  <label>Call 5: Review — System Prompt</label>
                  <textarea className="prompt-textarea" value={prompts.review_system || ""}
                    onChange={(e) => updatePrompt("review_system", e.target.value)} />
                </div>
                <div className="input-group">
                  <label>Call 5: Review — User Prompt Template</label>
                  <textarea className="prompt-textarea tall" value={prompts.review_user || ""}
                    onChange={(e) => updatePrompt("review_user", e.target.value)} />
                </div>
              </div>
            )}
          </div>

        </div>
      )}

      <button type="submit" className="submit-btn" disabled={disabled || !canSubmit}>
        {disabled ? "Generating..." : "Generate Video"}
      </button>
    </form>
  );
}
