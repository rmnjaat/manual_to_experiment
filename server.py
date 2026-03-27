"""FastAPI backend — serves the pipeline with SSE progress and provider selection."""

import json
import os
import tempfile
import asyncio
from pathlib import Path
from queue import Queue

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from dotenv import load_dotenv

from pipeline import run_pipeline
from providers import get_registry

load_dotenv(Path(__file__).resolve().parent / ".env")

app = FastAPI(title="Manual → Video Generator")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

OUTPUTS_DIR = Path(__file__).resolve().parent / "outputs"


@app.get("/api/providers")
async def list_providers():
    """List all available providers for TTS, Image, and Video."""
    from google import genai
    api_key = os.getenv("GEMINI_API_KEY", "")
    if api_key:
        client = genai.Client(api_key=api_key)
        from pipeline import _setup_providers
        _setup_providers(client)

    registry = get_registry()
    return {
        "tts": registry.list_tts(),
        "image": registry.list_image(),
        "video": registry.list_video(),
    }


@app.get("/api/runs")
async def list_runs():
    """List all pipeline runs, sorted by newest first."""
    runs = []
    if not OUTPUTS_DIR.exists():
        return runs

    for entry in sorted(OUTPUTS_DIR.iterdir(), reverse=True):
        if not entry.is_dir() or not entry.name.startswith("run_"):
            continue
        meta_path = entry / "run_meta.json"
        if meta_path.exists():
            with open(meta_path) as f:
                meta = json.load(f)
        else:
            meta = {"run_id": entry.name, "created_at": "", "product": "Unknown"}
        # Check what files exist
        files = [f.name for f in entry.iterdir() if f.is_file() and f.suffix == ".json" and f.name != "run_meta.json"]
        has_video = (entry / "final_video.mp4").exists()
        meta["files"] = sorted(files)
        meta["has_video"] = has_video
        runs.append(meta)

    return runs


@app.get("/api/runs/{run_id}/files/{filename}")
async def get_run_file(run_id: str, filename: str):
    """Serve a file from a specific run."""
    file_path = OUTPUTS_DIR / run_id / filename

    if not file_path.exists():
        raise HTTPException(404, f"File not found: {run_id}/{filename}")

    if filename.endswith(".mp4"):
        return FileResponse(file_path, media_type="video/mp4", filename=filename)

    if filename.endswith(".json"):
        with open(file_path) as f:
            return json.load(f)

    return FileResponse(file_path)


@app.get("/api/runs/{run_id}/video")
async def download_run_video(run_id: str):
    """Download video from a specific run."""
    video_path = OUTPUTS_DIR / run_id / "final_video.mp4"
    if not video_path.exists():
        raise HTTPException(404, "No video in this run.")
    return FileResponse(video_path, media_type="video/mp4", filename=f"{run_id}_video.mp4")


@app.get("/api/elevenlabs/voices")
async def get_elevenlabs_voices():
    """List available ElevenLabs voices."""
    api_key = os.getenv("ELEVENLABS_API_KEY", "")
    if not api_key:
        return {"voices": [], "error": "ELEVENLABS_API_KEY not set"}
    try:
        from stage5_audio.tts_elevenlabs import list_voices
        return {"voices": list_voices(api_key)}
    except Exception as e:
        return {"voices": [], "error": str(e)}


@app.get("/api/elevenlabs/models")
async def get_elevenlabs_models():
    """List available ElevenLabs models."""
    api_key = os.getenv("ELEVENLABS_API_KEY", "")
    if not api_key:
        return {"models": [], "error": "ELEVENLABS_API_KEY not set"}
    try:
        from stage5_audio.tts_elevenlabs import list_models
        return {"models": list_models(api_key)}
    except Exception as e:
        return {"models": [], "error": str(e)}


@app.get("/api/defaults")
async def get_defaults():
    """Return all configurable parameters with their defaults."""
    from stage2_extraction.prompts import EXTRACTION_PROMPT, VERIFICATION_SYSTEM, VERIFICATION_USER, ENRICHMENT_SYSTEM, ENRICHMENT_USER
    from stage3_script.prompts import SCRIPT_SYSTEM, SCRIPT_PROMPT, REVIEW_SYSTEM, REVIEW_USER
    from stage4_images.imagen import STYLE_PREFIX, STYLE_SUFFIX

    return {
        "quality_modes": [
            {"value": "standard", "label": "Standard", "description": "1 image per scene with Ken Burns effect"},
            {"value": "enhanced", "label": "Enhanced", "description": "3 frames per scene with crossfade (3x more images)"},
            {"value": "cinematic", "label": "Cinematic", "description": "AI-generated video clips per scene (requires Veo API)"},
        ],
        "gemini_models": [
            {"value": "gemini-2.5-flash", "label": "Gemini 2.5 Flash (fast)"},
            {"value": "gemini-2.5-pro", "label": "Gemini 2.5 Pro (best)"},
        ],
        "imagen_models": [
            {"value": "imagen-4.0-fast-generate-001", "label": "Imagen 4.0 Fast"},
            {"value": "imagen-4.0-generate-001", "label": "Imagen 4.0 Standard"},
            {"value": "imagen-4.0-ultra-generate-001", "label": "Imagen 4.0 Ultra (best)"},
        ],
        "languages": [
            {"value": "en", "label": "English"}, {"value": "hi", "label": "Hindi"},
            {"value": "es", "label": "Spanish"}, {"value": "fr", "label": "French"},
            {"value": "de", "label": "German"}, {"value": "ja", "label": "Japanese"},
            {"value": "ko", "label": "Korean"}, {"value": "zh-CN", "label": "Chinese"},
        ],
        "settings": {
            "quality_mode": "standard",
            "gemini_model": "gemini-2.5-flash",
            "imagen_model": "imagen-4.0-fast-generate-001",
            "tts_speed": 1.5,
            "tts_language": "en",
            "image_style_prefix": STYLE_PREFIX,
            "image_style_suffix": STYLE_SUFFIX,
            "video_fps": 30,
        },
        "prompts": {
            "extraction_prompt": EXTRACTION_PROMPT,
            "verification_system": VERIFICATION_SYSTEM,
            "verification_user": VERIFICATION_USER,
            "enrichment_system": ENRICHMENT_SYSTEM,
            "enrichment_user": ENRICHMENT_USER,
            "script_system": SCRIPT_SYSTEM,
            "script_prompt": SCRIPT_PROMPT,
            "review_system": REVIEW_SYSTEM,
            "review_user": REVIEW_USER,
        },
    }


@app.post("/api/generate")
async def generate_video_endpoint(
    pdf: UploadFile | None = File(None),
    url: str = Form(""),
    raw_text: str = Form(""),
    tts_provider: str = Form(""),
    image_provider: str = Form(""),
    video_provider: str = Form(""),
    gemini_model: str = Form("gemini-2.5-flash"),
    imagen_model: str = Form("imagen-4.0-fast-generate-001"),
    tts_speed: float = Form(1.5),
    tts_language: str = Form("en"),
    image_style_prefix: str = Form(""),
    image_style_suffix: str = Form(""),
    extraction_prompt: str = Form(""),
    verification_system: str = Form(""),
    verification_user: str = Form(""),
    enrichment_system: str = Form(""),
    enrichment_user: str = Form(""),
    script_system: str = Form(""),
    script_prompt: str = Form(""),
    review_system: str = Form(""),
    review_user: str = Form(""),
    resume_run_id: str = Form(""),
    resume_from: str = Form(""),
    elevenlabs_voice_id: str = Form("JBFqnCBsd6RMkjVDRZzb"),
    elevenlabs_model_id: str = Form("eleven_multilingual_v2"),
    elevenlabs_speed: float = Form(1.0),
    elevenlabs_stability: float = Form(0.5),
    elevenlabs_similarity: float = Form(0.75),
    quality_mode: str = Form("standard"),
):
    """Run the full pipeline with SSE progress streaming."""
    source = None
    temp_path = None
    is_resume = bool(resume_run_id.strip() and resume_from.strip())

    if pdf and pdf.filename:
        suffix = Path(pdf.filename).suffix or ".pdf"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = await pdf.read()
            tmp.write(content)
            temp_path = tmp.name
        source = temp_path
    elif url.strip():
        source = url.strip()
    elif raw_text.strip():
        source = raw_text.strip()
    elif is_resume:
        # Resuming from middle — source not needed, pipeline loads from saved files
        source = "resume"
    else:
        raise HTTPException(400, "Provide a PDF file, URL, or raw text.")

    # Build provider config from form
    provider_config = {}
    if tts_provider.strip():
        provider_config["tts"] = tts_provider.strip()
    if image_provider.strip():
        provider_config["image"] = image_provider.strip()
    if video_provider.strip():
        provider_config["video"] = video_provider.strip()

    progress_queue: Queue = Queue()

    def on_progress(stage: str, detail: str = ""):
        progress_queue.put({"stage": stage, "detail": detail})

    async def event_stream():
        loop = asyncio.get_event_loop()

        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            pipeline_settings = {
                "gemini_model": gemini_model,
                "imagen_model": imagen_model,
                "tts_speed": tts_speed,
                "tts_language": tts_language,
                "quality_mode": quality_mode,
                "elevenlabs_voice_id": elevenlabs_voice_id,
                "elevenlabs_model_id": elevenlabs_model_id,
                "elevenlabs_speed": elevenlabs_speed,
                "elevenlabs_stability": elevenlabs_stability,
                "elevenlabs_similarity": elevenlabs_similarity,
                "image_style_prefix": image_style_prefix or None,
                "image_style_suffix": image_style_suffix or None,
                "extraction_prompt": extraction_prompt or None,
                "verification_system": verification_system or None,
                "verification_user": verification_user or None,
                "enrichment_system": enrichment_system or None,
                "enrichment_user": enrichment_user or None,
                "script_system": script_system or None,
                "script_prompt": script_prompt or None,
                "review_system": review_system or None,
                "review_user": review_user or None,
            }
            future = loop.run_in_executor(
                pool, lambda: run_pipeline(
                    source,
                    output_dir="outputs",
                    on_progress=on_progress,
                    provider_config=provider_config or None,
                    settings=pipeline_settings,
                    resume_run_id=resume_run_id.strip() or None,
                    resume_from=resume_from.strip() or None,
                )
            )

            # Stream progress while pipeline runs
            while not future.done():
                await asyncio.sleep(0.3)
                while not progress_queue.empty():
                    msg = progress_queue.get()
                    yield f"data: {json.dumps(msg)}\n\n"

            # Drain remaining
            while not progress_queue.empty():
                msg = progress_queue.get()
                yield f"data: {json.dumps(msg)}\n\n"

            try:
                result = future.result()
                done_msg = {
                    "stage": "done",
                    "result": {
                        "video_path": result.get("video_path", ""),
                        "scenes": result.get("scenes", []),
                        "changelog": result.get("changelog", []),
                        "metadata": result.get("metadata", {}),
                        "run_id": result.get("run_id", ""),
                    }
                }
                yield f"data: {json.dumps(done_msg)}\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'stage': 'error', 'detail': str(e)})}\n\n"
            finally:
                if temp_path and os.path.exists(temp_path):
                    os.unlink(temp_path)

    return StreamingResponse(event_stream(), media_type="text/event-stream")


# Legacy endpoints for backward compat
@app.get("/api/download-video")
async def download_video():
    """Download the most recent video."""
    # Find newest run with a video
    if OUTPUTS_DIR.exists():
        for entry in sorted(OUTPUTS_DIR.iterdir(), reverse=True):
            if entry.is_dir() and (entry / "final_video.mp4").exists():
                return FileResponse(entry / "final_video.mp4", media_type="video/mp4", filename="instruction_video.mp4")
    raise HTTPException(404, "No video generated yet.")


@app.get("/api/outputs/{filename}")
async def get_output_file(filename: str):
    """Serve from the most recent run (legacy)."""
    if OUTPUTS_DIR.exists():
        for entry in sorted(OUTPUTS_DIR.iterdir(), reverse=True):
            if entry.is_dir():
                fp = entry / filename
                if fp.exists():
                    if filename.endswith(".mp4"):
                        return FileResponse(fp, media_type="video/mp4", filename=filename)
                    with open(fp) as f:
                        return json.load(f)
    raise HTTPException(404, f"File not found: {filename}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
