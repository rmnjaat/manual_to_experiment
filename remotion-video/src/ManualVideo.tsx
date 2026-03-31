import { AbsoluteFill, Audio, Sequence, staticFile, interpolate, useCurrentFrame } from "remotion";
import { IntroScene } from "./scenes/IntroScene";
import { StepScene } from "./scenes/StepScene";
import { TransitionScene } from "./scenes/TransitionScene";
import { OutroScene } from "./scenes/OutroScene";

interface SceneData {
  scene_id: number;
  type: string;
  narration: string;
  visual_hint: string;
  motion_hint?: string;
  section?: string;
  step_number?: number;
  estimated_duration_sec: number;
  real_duration_sec?: number;
  visual_type?: "image" | "multiframe" | "video";
  frame_count?: number;
  has_video_clip?: boolean;
}

interface ManualVideoProps {
  scenes: SceneData[];
}

const FPS = 30;
const CROSSFADE_FRAMES = 15; // 0.5s crossfade between scenes

export const ManualVideo: React.FC<ManualVideoProps> = ({ scenes }) => {
  let currentFrame = 0;
  const totalSteps = scenes.filter((s) => s.type === "step").length;

  return (
    <AbsoluteFill style={{ backgroundColor: "#1a1a2e" }}>
      {scenes.map((scene, index) => {
        const duration = scene.real_duration_sec || scene.estimated_duration_sec || 8;
        const durationFrames = Math.ceil(duration * FPS);
        const startFrame = currentFrame;

        // Advance frame counter
        currentFrame += durationFrames;

        // Count which step this is (for progress bar)
        const stepIndex = scenes
          .slice(0, index + 1)
          .filter((s) => s.type === "step").length;

        // Determine visual assets based on quality mode
        const visualType = scene.visual_type || "image";
        const frameCount = scene.frame_count || 1;

        // Build frame file paths for multi-frame mode
        const frameFiles = visualType === "multiframe" && frameCount > 1
          ? Array.from({ length: frameCount }, (_, i) =>
              staticFile(`images/scene_${scene.scene_id}_frame_${i}.png`)
            )
          : [];

        // Video clip path for cinematic mode
        const videoFile = visualType === "video" && scene.has_video_clip
          ? staticFile(`videos/scene_${scene.scene_id}.mp4`)
          : undefined;

        const imageFile = staticFile(`images/scene_${scene.scene_id}.png`);
        const audioFile = `audio/scene_${scene.scene_id}.wav`;

        const sceneProps = {
          narration: scene.narration,
          visualHint: scene.visual_hint,
          section: scene.section || "",
          durationFrames,
          visualType,
          frameFiles,
          videoFile,
          sceneVariant: index, // for varied Ken Burns directions
        };

        return (
          <Sequence
            key={scene.scene_id}
            from={startFrame}
            durationInFrames={durationFrames}
            name={`Scene ${scene.scene_id}: ${scene.type}`}
          >
            {/* Audio track */}
            <Audio src={staticFile(audioFile)} />

            {/* Crossfade overlay from previous scene */}
            {index > 0 && (
              <SceneCrossfade durationFrames={durationFrames} />
            )}

            {/* Visual based on scene type */}
            {scene.type === "intro" && (
              <IntroScene {...sceneProps} imageFile={imageFile} />
            )}
            {scene.type === "step" && (
              <StepScene
                {...sceneProps}
                imageFile={imageFile}
                stepNumber={scene.step_number || stepIndex}
                totalSteps={totalSteps}
                stepIndex={stepIndex}
              />
            )}
            {scene.type === "transition" && (
              <TransitionScene
                narration={scene.narration}
                visualHint={scene.visual_hint}
                section={scene.section || ""}
                durationFrames={durationFrames}
              />
            )}
            {scene.type === "prerequisites" && (
              <StepScene
                {...sceneProps}
                imageFile={imageFile}
                stepNumber={0}
                totalSteps={totalSteps}
                stepIndex={0}
              />
            )}
            {scene.type === "outro" && (
              <OutroScene {...sceneProps} imageFile={imageFile} />
            )}
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};

/** Adds a fade-in from black at the start of each scene (crossfade effect) */
const SceneCrossfade: React.FC<{ durationFrames: number }> = ({ durationFrames }) => {
  const frame = useCurrentFrame();
  const fadeIn = interpolate(frame, [0, CROSSFADE_FRAMES], [1, 0], {
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill
      style={{
        backgroundColor: "rgba(26, 26, 46, 1)",
        opacity: fadeIn,
        zIndex: 100,
      }}
    />
  );
};
