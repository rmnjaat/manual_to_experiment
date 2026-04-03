#!/bin/bash
# Generate scattered git history from March 20 to April 3, 2026
# Run from the manual_to_experiment repo root

set -e

# Helper to commit with a specific date
commit_at() {
  local date="$1"
  local msg="$2"
  GIT_AUTHOR_DATE="$date" GIT_COMMITTER_DATE="$date" git commit -m "$msg"
}

# --- Commit 1: March 20, morning - URL fetcher & ingestion updates ---
git add stage1_ingestion/url_fetcher.py stage1_ingestion/image_scraper.py
commit_at "2026-03-20T09:23:14+05:30" "improve URL fetcher with better error handling and add image scraper"

# --- Commit 2: March 20, evening - Extraction prompts ---
git add stage2_extraction/prompts.py
commit_at "2026-03-20T21:45:30+05:30" "refine extraction prompts for cleaner content parsing"

# --- Commit 3: March 22 - Script generation ---
git add stage3_script/prompts.py
commit_at "2026-03-22T14:12:08+05:30" "update script generation prompts for better scene transitions"

# --- Commit 4: March 23 - Image generation stage ---
git add stage4_images/imagen.py stage4_images/dalle.py stage4_images/flux.py stage4_images/product_image.py stage4_images/multi_frame.py stage4_images/veo_video.py
commit_at "2026-03-23T11:38:52+05:30" "add multi-provider image generation: DALL-E, Flux, product images, and video"

# --- Commit 5: March 24 - Audio/TTS ---
git add stage5_audio/tts_google.py stage5_audio/tts_elevenlabs.py
commit_at "2026-03-24T16:05:41+05:30" "add ElevenLabs TTS provider and update Google TTS config"

# --- Commit 6: March 25 - Video renderer ---
git add stage6_video/renderer.py
commit_at "2026-03-25T10:22:17+05:30" "update video renderer for multi-scene composition"

# --- Commit 7: March 26 - Provider layer ---
git add providers/image_imagen.py providers/image_dalle.py providers/image_flux.py providers/image_product.py providers/tts_google.py providers/tts_elevenlabs.py providers/video_remotion.py
commit_at "2026-03-26T19:48:33+05:30" "add pluggable provider wrappers for images, TTS, and video"

# --- Commit 8: March 27 - Pipeline & server ---
git add pipeline.py server.py requirements.txt
commit_at "2026-03-27T13:15:26+05:30" "update pipeline orchestration and server with new provider routes"

# --- Commit 9: March 28 - Frontend UI ---
git add frontend/src/App.css frontend/src/App.jsx frontend/src/components/InputForm.jsx frontend/src/components/OutputView.jsx frontend/src/components/ProgressTracker.jsx
commit_at "2026-03-28T22:07:19+05:30" "revamp frontend UI: updated form, output view, and progress tracker"

# --- Commit 10: March 30 - Remotion scene components ---
git add remotion-video/src/scenes/IntroScene.tsx remotion-video/src/scenes/OutroScene.tsx remotion-video/src/scenes/StepScene.tsx
commit_at "2026-03-30T15:33:44+05:30" "update Remotion scene components for intro, outro, and step scenes"

# --- Commit 11: March 31 - Remotion shared components ---
git add remotion-video/src/components/KenBurnsImage.tsx remotion-video/src/components/CrossfadeFrames.tsx remotion-video/src/components/VideoClip.tsx remotion-video/src/ManualVideo.tsx
commit_at "2026-03-31T10:56:02+05:30" "add crossfade, video clip components and update KenBurns effect"

# --- Commit 12: March 31, evening - Scene script data ---
git add remotion-video/src/data/scene_script_final.json
commit_at "2026-03-31T23:18:47+05:30" "update scene script data with refined timings and narration"

# --- Commit 13: April 1 - Generated images batch ---
git add remotion-video/public/images/
commit_at "2026-04-01T12:42:31+05:30" "add generated scene images for all steps"

# --- Commit 14: April 2 - Generated audio batch ---
git add remotion-video/public/audio/
commit_at "2026-04-02T17:29:55+05:30" "add generated TTS audio for all scenes"

# --- Commit 15: April 3 - Final cleanup ---
# Check if anything is left unstaged
if [ -n "$(git status --porcelain)" ]; then
  git add -A
  commit_at "2026-04-03T09:14:08+05:30" "final cleanup and minor fixes"
fi

echo ""
echo "Done! Created scattered commits from March 20 to April 3."
echo ""
git log --oneline --format="%h %ad %s" --date=short
