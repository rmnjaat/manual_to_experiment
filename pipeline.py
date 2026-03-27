"""Pipeline orchestrator — runs all 6 stages in sequence.

Stage 1:     Input preparation (PDF upload / URL fetch / raw text)
Stage 2:     Raw extraction (Gemini — auto-detects metadata)    [Call 1]
Stage 2.5:   Verification + grounding                           [Call 2]
Stage 2.7:   Enrichment (prerequisites, complexity, splitting)  [Call 3]
Stage 3:     Script generation                                  [Call 4]
Stage 3.5:   Script review + polish                             [Call 5]
Stage 4:     Image generation (pluggable provider)
Stage 5:     Audio / TTS generation (pluggable provider)
Stage 6:     Video assembly (pluggable provider)
"""
import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Callable

from dotenv import load_dotenv
from google import genai

from stage1_ingestion.detector import detect_input_type
from stage1_ingestion.pdf_uploader import upload_pdf_to_gemini
from stage1_ingestion.url_fetcher import fetch_url_html
from stage1_ingestion.image_scraper import scrape_product_images
from stage2_extraction.extractor import extract_structure
from stage2_extraction.validator import validate_structure
from stage2_extraction.verifier import verify_extraction, apply_verification
from stage2_extraction.enricher import enrich_structure
from stage3_script.generator import generate_script
from stage3_script.reviewer import review_script
from providers import get_registry
from providers.tts_google import GoogleTTSProvider
from providers.tts_elevenlabs import ElevenLabsProvider
from providers.image_imagen import ImagenProvider
from providers.image_product import ProductImageProvider
from providers.image_fallback import FallbackSlideProvider
from providers.video_remotion import RemotionProvider
from stage4_images.multi_frame import generate_multi_frame
from stage4_images.veo_video import generate_video_clip, generate_motion_hint

load_dotenv(Path(__file__).resolve().parent / ".env")

ProgressCallback = Callable[[str, str], None] | None


def _get_client() -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not found. Add it to .env")
    return genai.Client(api_key=api_key)


def _save_json(data, output_dir: str, filename: str) -> str:
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, filename)
    with open(path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return path


def _setup_providers(client: genai.Client, provider_config: dict | None = None, product_images: list[str] | None = None, imagen_model: str = "imagen-4.0-fast-generate-001", settings: dict | None = None):
    """Register default providers and apply overrides from config."""
    registry = get_registry()
    config = provider_config or {}
    cfg = settings or {}

    # TTS providers
    if "google_tts" not in registry.list_tts():
        registry.register_tts("google_tts", GoogleTTSProvider())
    # Register ElevenLabs if API key is available
    elevenlabs_key = os.getenv("ELEVENLABS_API_KEY", "")
    if elevenlabs_key and "elevenlabs" not in registry.list_tts():
        registry.register_tts("elevenlabs", ElevenLabsProvider(
            api_key=elevenlabs_key,
            voice_id=cfg.get("elevenlabs_voice_id", "JBFqnCBsd6RMkjVDRZzb"),
            model_id=cfg.get("elevenlabs_model_id", "eleven_multilingual_v2"),
            speed=cfg.get("elevenlabs_speed", 1.0),
            stability=cfg.get("elevenlabs_stability", 0.5),
            similarity_boost=cfg.get("elevenlabs_similarity", 0.75),
        ))
    if "tts" in config:
        registry.set_active_tts(config["tts"])

    # Image providers — Imagen 4.0 primary, product images fallback
    registry.register_image("imagen4", ImagenProvider(client, model=imagen_model, product_context=cfg.get("product_context", "")))
    registry.set_active_image("imagen4")
    if product_images:
        registry.register_image("product_images", ProductImageProvider(product_images))
    if "fallback_slide" not in registry.list_image():
        registry.register_image("fallback_slide", FallbackSlideProvider())

    # Optional: DALL-E 3 (requires OPENAI_API_KEY)
    openai_key = os.getenv("OPENAI_API_KEY", "")
    if openai_key and "dalle3" not in registry.list_image():
        try:
            from providers.image_dalle import DalleProvider
            registry.register_image("dalle3", DalleProvider(api_key=openai_key))
        except Exception:
            pass  # openai package not installed or key invalid

    # Optional: Flux Pro (requires FLUX_API_KEY)
    flux_key = os.getenv("FLUX_API_KEY", "")
    if flux_key and "flux_pro" not in registry.list_image():
        try:
            from providers.image_flux import FluxProvider
            registry.register_image("flux_pro", FluxProvider(api_key=flux_key))
        except Exception:
            pass

    if "image" in config:
        registry.set_active_image(config["image"])

    # Video providers
    if not registry.list_video():
        registry.register_video("remotion", RemotionProvider())
    if "video" in config:
        registry.set_active_video(config["video"])


STAGE_ORDER = ["stage1", "stage2", "stage2_5", "stage2_7", "stage3", "stage3_5", "stage4", "stage5", "stage6"]


def run_pipeline(
    source: str,
    output_dir: str = "outputs",
    on_progress: ProgressCallback = None,
    provider_config: dict | None = None,
    settings: dict | None = None,
    resume_run_id: str | None = None,
    resume_from: str | None = None,
):
    """Run the full manual-to-video pipeline (6 stages, 5 Gemini calls).

    Args:
        source: Path to PDF, URL, or plain text.
        output_dir: Where to save outputs.
        on_progress: Callback(stage_key, detail) for UI progress updates.
        provider_config: Optional dict to override active providers.
        settings: Optional dict with configurable parameters.
        resume_run_id: If resuming, the run_id to continue from.
        resume_from: Stage key to resume from (e.g. "stage4", "stage5").
            Stages before this are skipped and loaded from existing files.

    Returns:
        Dict with structure, scenes, video_path, and metadata.
    """
    def progress(stage: str, detail: str = ""):
        print(f"[{stage}] {detail}")
        if on_progress:
            on_progress(stage, detail)

    cfg = settings or {}
    gemini_model = cfg.get("gemini_model", "gemini-2.5-flash")
    imagen_model = cfg.get("imagen_model", "imagen-4.0-fast-generate-001")
    tts_speed = cfg.get("tts_speed", 1.5)
    tts_language = cfg.get("tts_language", "en")
    quality_mode = cfg.get("quality_mode", "standard")  # standard | enhanced | cinematic

    # Override prompts if provided
    if cfg.get("extraction_prompt"):
        import stage2_extraction.prompts as s2p
        s2p.EXTRACTION_PROMPT = cfg["extraction_prompt"]
    if cfg.get("verification_system"):
        import stage2_extraction.prompts as s2p
        s2p.VERIFICATION_SYSTEM = cfg["verification_system"]
    if cfg.get("verification_user"):
        import stage2_extraction.prompts as s2p
        s2p.VERIFICATION_USER = cfg["verification_user"]
    if cfg.get("enrichment_system"):
        import stage2_extraction.prompts as s2p
        s2p.ENRICHMENT_SYSTEM = cfg["enrichment_system"]
    if cfg.get("enrichment_user"):
        import stage2_extraction.prompts as s2p
        s2p.ENRICHMENT_USER = cfg["enrichment_user"]
    if cfg.get("script_system"):
        import stage3_script.prompts as s3p
        s3p.SCRIPT_SYSTEM = cfg["script_system"]
    if cfg.get("script_prompt"):
        import stage3_script.prompts as s3p
        s3p.SCRIPT_PROMPT = cfg["script_prompt"]
    if cfg.get("review_system"):
        import stage3_script.prompts as s3p
        s3p.REVIEW_SYSTEM = cfg["review_system"]
    if cfg.get("review_user"):
        import stage3_script.prompts as s3p
        s3p.REVIEW_USER = cfg["review_user"]
    if cfg.get("image_style_prefix"):
        import stage4_images.imagen as s4i
        s4i.STYLE_PREFIX = cfg["image_style_prefix"]
    if cfg.get("image_style_suffix"):
        import stage4_images.imagen as s4i
        s4i.STYLE_SUFFIX = cfg["image_style_suffix"]

    client = _get_client()
    registry = get_registry()

    # Determine skip threshold
    skip_before = STAGE_ORDER.index(resume_from) if resume_from and resume_from in STAGE_ORDER else 0
    def should_run(stage_key: str) -> bool:
        return STAGE_ORDER.index(stage_key) >= skip_before if stage_key in STAGE_ORDER else True

    # Reuse existing run folder if resuming, else create new
    if resume_run_id:
        run_id = resume_run_id
        run_dir = os.path.join(output_dir, run_id)
    else:
        run_ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_id = f"run_{run_ts}"
        run_dir = os.path.join(output_dir, run_id)
    os.makedirs(run_dir, exist_ok=True)

    images_dir = os.path.join(run_dir, "images")
    audio_dir = os.path.join(run_dir, "audio")
    os.makedirs(images_dir, exist_ok=True)
    os.makedirs(audio_dir, exist_ok=True)

    def _load_json(filename: str) -> dict | list | None:
        path = os.path.join(run_dir, filename)
        if os.path.exists(path):
            with open(path) as f:
                return json.load(f)
        return None

    # ── Stage 1: Ingestion ──────────────────────────────────────────
    product_images: list[str] = []
    product_images_dir = os.path.join("temp", "product_images")
    content = None

    if should_run("stage1"):
        input_type = detect_input_type(source)
        progress("stage1", f"Detected input type: {input_type}")

        if input_type == "pdf":
            content = upload_pdf_to_gemini(client, source)
        elif input_type == "url":
            content = fetch_url_html(source)
            progress("stage1", "Scraping product images from URL...")
            try:
                product_images = scrape_product_images(source, product_images_dir)
                progress("stage1", f"Found {len(product_images)} product images")
            except Exception as e:
                progress("stage1", f"Image scraping failed: {e}")
        else:
            content = source
        progress("stage1_done", "Input ready")
    else:
        progress("stage1_done", "Skipped (resuming)")
        # Check for existing scraped images
        if os.path.isdir(product_images_dir):
            product_images = [os.path.join(product_images_dir, f) for f in os.listdir(product_images_dir) if not f.startswith(".")]

    # Set up providers
    _setup_providers(client, provider_config, product_images=product_images, imagen_model=imagen_model, settings=cfg)

    # ── Stage 2: Raw Extraction [Call 1] ────────────────────────────
    if should_run("stage2"):
        progress("stage2", "Extracting structure from document...")
        structure = extract_structure(client, content, model_name=gemini_model)
        errors = validate_structure(structure)
        if errors:
            progress("stage2", f"Validation warnings: {errors}")
        _save_json(structure, run_dir, "structured_data_raw.json")
    else:
        structure = _load_json("structured_data_raw.json") or _load_json("structured_data_verified.json") or {}
        progress("stage2_done", "Skipped (resuming)")

    metadata = structure.get("metadata", {})
    product_label = f"{metadata.get('brand', '?')} {metadata.get('product_name', '?')}"
    section_count = len(structure.get("sections", []))
    step_count = sum(len(s.get("steps", [])) for s in structure.get("sections", []))
    progress("stage2_done", f"{product_label}: {section_count} sections, {step_count} steps")

    # ── Stage 2.5: Verification [Call 2] ────────────────────────────
    if should_run("stage2_5"):
        progress("stage2_5", "Verifying extraction against original document...")
        verification = verify_extraction(client, content, structure, model_name=gemini_model)
        _save_json(verification, run_dir, "verification_result.json")
        hallucinated = sum(1 for v in verification.get("verified_steps", []) if v.get("status") == "hallucinated")
        missing = len(verification.get("missing_steps", []))
        structure = apply_verification(structure, verification)
        _save_json(structure, run_dir, "structured_data_verified.json")
        progress("stage2_5_done", f"{hallucinated} hallucinated removed, {missing} missing added")
    else:
        structure = _load_json("structured_data_verified.json") or structure
        metadata = structure.get("metadata", metadata)
        product_label = f"{metadata.get('brand', '?')} {metadata.get('product_name', '?')}"
        progress("stage2_5_done", "Skipped (resuming)")

    # ── Stage 2.7: Enrichment [Call 3] ──────────────────────────────
    if should_run("stage2_7"):
        progress("stage2_7", "Enriching with prerequisites and complexity...")
        enriched = enrich_structure(client, structure, model_name=gemini_model)
        enriched["metadata"] = metadata
        _save_json(enriched, run_dir, "structured_data_final.json")
        prereq_count = len(enriched.get("prerequisites", []))
        progress("stage2_7_done", f"{prereq_count} prerequisites found")
    else:
        enriched = _load_json("structured_data_final.json") or structure
        metadata = enriched.get("metadata", metadata)
        product_label = f"{metadata.get('brand', '?')} {metadata.get('product_name', '?')}"
        progress("stage2_7_done", "Skipped (resuming)")

    # ── Stage 3: Script Generation [Call 4] ─────────────────────────
    if should_run("stage3"):
        progress("stage3", "Generating video script...")
        scenes = generate_script(client, enriched, metadata, model_name=gemini_model)
        _save_json(scenes, run_dir, "scene_script_draft.json")
        progress("stage3_done", f"{len(scenes)} scenes generated")
    else:
        scenes = _load_json("scene_script_draft.json") or []
        progress("stage3_done", f"Skipped (resuming, {len(scenes)} scenes)")

    # ── Stage 3.5: Script Review [Call 5] ───────────────────────────
    changelog = []
    if should_run("stage3_5"):
        progress("stage3_5", "Reviewing and polishing script...")
        review_result = review_script(client, scenes, enriched, model_name=gemini_model)
        scenes = review_result["scenes"]
        changelog = review_result.get("changelog", [])
        _save_json(review_result, run_dir, "scene_script_final.json")
        progress("stage3_5_done", f"{len(changelog)} fixes applied")
    else:
        review_result = _load_json("scene_script_final.json")
        if review_result:
            scenes = review_result.get("scenes", review_result) if isinstance(review_result, dict) else review_result
            changelog = review_result.get("changelog", []) if isinstance(review_result, dict) else []
        progress("stage3_5_done", f"Skipped (resuming, {len(scenes)} scenes)")

    # ── Stage 4: Image Generation (provider-based, quality-mode-aware) ──
    videos_dir = os.path.join(run_dir, "videos")
    os.makedirs(videos_dir, exist_ok=True)

    if should_run("stage4"):
        image_provider = registry.get_image()
        mode_label = {"standard": "Standard", "enhanced": "Enhanced (multi-frame)", "cinematic": "Cinematic (AI video)"}
        progress("stage4", f"Mode: {mode_label.get(quality_mode, quality_mode)} via {image_provider.get_name()}")

        for i, scene in enumerate(scenes):
            sid = scene["scene_id"]
            img_path = os.path.join(images_dir, f"scene_{sid}.png")
            visual_hint = scene.get("visual_hint", "")

            # --- Generate base image (all modes need at least one) ---
            try:
                image_provider.generate(
                    visual_hint, img_path,
                    scene_index=i,
                    scene_type=scene.get("type", ""),
                    section_name=scene.get("section", ""),
                    step_text=visual_hint or scene.get("narration", "")[:80],
                    product_context=product_label,
                )
            except Exception as e:
                progress("stage4", f"Primary failed ({e}), trying fallback...")
                try:
                    if product_images:
                        ProductImageProvider(product_images).generate(
                            visual_hint, img_path,
                            scene_index=i,
                            scene_type=scene.get("type", ""),
                            step_text=visual_hint or scene.get("narration", "")[:80],
                        )
                    else:
                        raise RuntimeError("No product images")
                except Exception:
                    FallbackSlideProvider().generate(
                        scene.get("narration", "")[:80], img_path,
                        section=scene.get("section", ""),
                        step_number=f"Scene {sid}",
                    )

            # --- Enhanced mode: generate multi-frame sequence ---
            if quality_mode == "enhanced":
                try:
                    progress("stage4", f"Generating multi-frame for scene {sid}...")
                    frame_paths = generate_multi_frame(
                        client, image_provider,
                        visual_hint, images_dir, sid,
                        product_context=product_label,
                        model_name=gemini_model,
                        num_frames=3,
                    )
                    scene["frame_count"] = len(frame_paths)
                    scene["visual_type"] = "multiframe"
                except Exception as e:
                    progress("stage4", f"Multi-frame failed ({e}), using single image")
                    scene["frame_count"] = 1
                    scene["visual_type"] = "image"

            # --- Cinematic mode: generate video clip via Veo ---
            elif quality_mode == "cinematic":
                video_clip_path = os.path.join(videos_dir, f"scene_{sid}.mp4")
                motion = scene.get("motion_hint") or generate_motion_hint(
                    visual_hint, scene.get("narration", "")
                )
                try:
                    progress("stage4", f"Generating video clip for scene {sid} via Veo...")
                    generate_video_clip(
                        client, img_path, motion, video_clip_path,
                    )
                    scene["has_video_clip"] = True
                    scene["visual_type"] = "video"
                except Exception as e:
                    progress("stage4", f"Veo failed ({e}), falling back to image")
                    scene["has_video_clip"] = False
                    scene["visual_type"] = "image"

            else:
                scene["visual_type"] = "image"

            progress("stage4", f"Scene {i+1}/{len(scenes)} done")

        progress("stage4_done", f"{len(scenes)} visuals ready ({quality_mode} mode)")
    else:
        progress("stage4_done", "Skipped (resuming)")

    # ── Stage 5: Audio / TTS (provider-based) ───────────────────────
    if should_run("stage5"):
        tts_provider = registry.get_tts()
        progress("stage5", f"Generating audio via {tts_provider.get_name()}...")
        for i, scene in enumerate(scenes):
            audio_path = os.path.join(audio_dir, f"scene_{scene['scene_id']}.wav")
            _, dur = tts_provider.generate(scene["narration"], audio_path, speed=tts_speed, language=tts_language)
            scene["real_duration_sec"] = dur
            progress("stage5", f"Audio {i+1}/{len(scenes)} ({dur:.1f}s)")
        _save_json(scenes, run_dir, "scene_script_with_durations.json")
        total_dur = sum(s.get("real_duration_sec", 0) for s in scenes)
        progress("stage5_done", f"Total audio: {total_dur:.0f}s")
    else:
        loaded = _load_json("scene_script_with_durations.json")
        if loaded:
            scenes = loaded
        total_dur = sum(s.get("real_duration_sec", 0) for s in scenes)
        progress("stage5_done", f"Skipped (resuming, {total_dur:.0f}s audio)")

    # ── Stage 6: Video Assembly (provider-based) ────────────────────
    if should_run("stage6"):
        video_provider = registry.get_video()
        progress("stage6", f"Rendering video via {video_provider.get_name()}...")
        video_path = os.path.join(run_dir, "final_video.mp4")
        video_provider.render(
            scenes, images_dir, audio_dir, video_path,
            quality_mode=quality_mode,
            videos_dir=videos_dir,
        )
        progress("stage6_done", video_path)
    else:
        video_path = os.path.join(run_dir, "final_video.mp4")
        progress("stage6_done", "Skipped (resuming)")

    # Save run metadata
    run_meta = {
        "run_id": run_id,
        "created_at": datetime.now().isoformat(),
        "source": source if not os.path.isfile(source) else os.path.basename(source),
        "product": product_label,
        "quality_mode": quality_mode,
        "image_provider": registry.get_image().get_name(),
        "tts_provider": registry.get_tts().get_name(),
        "gemini_model": gemini_model,
        "imagen_model": imagen_model,
        "settings": cfg,
        "total_scenes": len(scenes),
        "total_audio_sec": round(total_dur, 1),
    }
    _save_json(run_meta, run_dir, "run_meta.json")

    return {
        "metadata": metadata,
        "structure": enriched,
        "scenes": scenes,
        "changelog": changelog,
        "video_path": video_path,
        "run_id": run_id,
    }


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python pipeline.py <pdf_path_or_url_or_text>")
        sys.exit(1)

    run_pipeline(sys.argv[1])
