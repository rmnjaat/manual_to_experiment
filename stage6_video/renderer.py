"""Stage 6: Render final video using Remotion.

Copies scene data, images, and audio into the Remotion project's
public/ and src/data/ directories, then calls `npx remotion render`.
"""
import json
import os
import shutil
import subprocess
from pathlib import Path


REMOTION_DIR = Path(__file__).resolve().parent.parent / "remotion-video"


def _copy_assets(scenes: list[dict], images_dir: str, audio_dir: str, videos_dir: str = ""):
    """Copy generated images, audio, and video clips into Remotion's public/ folder."""
    pub_images = REMOTION_DIR / "public" / "images"
    pub_audio = REMOTION_DIR / "public" / "audio"
    pub_videos = REMOTION_DIR / "public" / "videos"
    pub_images.mkdir(parents=True, exist_ok=True)
    pub_audio.mkdir(parents=True, exist_ok=True)
    pub_videos.mkdir(parents=True, exist_ok=True)

    for scene in scenes:
        sid = scene["scene_id"]

        # Copy base image
        img_src = os.path.join(images_dir, f"scene_{sid}.png")
        if os.path.exists(img_src):
            shutil.copy2(img_src, pub_images / f"scene_{sid}.png")

        # Copy multi-frame images (enhanced mode)
        frame_count = scene.get("frame_count", 1)
        if frame_count > 1:
            for fi in range(frame_count):
                frame_src = os.path.join(images_dir, f"scene_{sid}_frame_{fi}.png")
                if os.path.exists(frame_src):
                    shutil.copy2(frame_src, pub_images / f"scene_{sid}_frame_{fi}.png")

        # Copy video clips (cinematic mode)
        if scene.get("has_video_clip") and videos_dir:
            vid_src = os.path.join(videos_dir, f"scene_{sid}.mp4")
            if os.path.exists(vid_src):
                shutil.copy2(vid_src, pub_videos / f"scene_{sid}.mp4")

        # Copy audio
        audio_src = os.path.join(audio_dir, f"scene_{sid}.wav")
        if os.path.exists(audio_src):
            shutil.copy2(audio_src, pub_audio / f"scene_{sid}.wav")


def _write_scene_data(scenes: list[dict]):
    """Write the scene script JSON into Remotion's src/data/ folder."""
    data_dir = REMOTION_DIR / "src" / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    with open(data_dir / "scene_script_final.json", "w") as f:
        json.dump(scenes, f, indent=2, ensure_ascii=False)


def render_video(
    scenes: list[dict],
    images_dir: str,
    audio_dir: str,
    output_path: str,
    quality_mode: str = "standard",
    videos_dir: str = "",
) -> str:
    """Render the final video using Remotion.

    Steps:
    1. Copy images, audio, and video clips into remotion-video/public/
    2. Write scene_script_final.json into remotion-video/src/data/
    3. Run `npx remotion render ManualVideo <output_path>`

    Args:
        scenes: Final scene list with real_duration_sec.
        images_dir: Directory with scene_N.png files.
        audio_dir: Directory with scene_N.wav files.
        output_path: Where to save the final MP4.
        quality_mode: "standard", "enhanced", or "cinematic".
        videos_dir: Directory with scene_N.mp4 video clips (cinematic mode).

    Returns:
        Path to the rendered MP4.
    """
    # 1. Copy assets
    _copy_assets(scenes, images_dir, audio_dir, videos_dir=videos_dir)

    # 2. Write scene data
    _write_scene_data(scenes)

    # 3. Render
    abs_output = os.path.abspath(output_path)
    os.makedirs(os.path.dirname(abs_output) or ".", exist_ok=True)

    result = subprocess.run(
        [
            "npx", "remotion", "render",
            "ManualVideo",
            abs_output,
        ],
        cwd=str(REMOTION_DIR),
        capture_output=True,
        text=True,
        timeout=600,  # 10 min max
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"Remotion render failed (exit {result.returncode}):\n"
            f"stdout: {result.stdout[-500:]}\n"
            f"stderr: {result.stderr[-500:]}"
        )

    return abs_output
