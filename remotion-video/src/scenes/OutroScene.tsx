import { AbsoluteFill, useCurrentFrame, interpolate } from "remotion";
import { AnimatedSubtitle } from "../components/AnimatedSubtitle";
import { KenBurnsImage } from "../components/KenBurnsImage";
import { CrossfadeFrames } from "../components/CrossfadeFrames";
import { VideoClip } from "../components/VideoClip";

interface OutroSceneProps {
  narration: string;
  visualHint: string;
  section: string;
  durationFrames: number;
  imageFile: string;
  visualType?: "image" | "multiframe" | "video";
  frameFiles?: string[];
  videoFile?: string;
  sceneVariant?: number;
}

export const OutroScene: React.FC<OutroSceneProps> = ({
  narration,
  durationFrames,
  imageFile,
  visualType = "image",
  frameFiles = [],
  videoFile,
  sceneVariant = 0,
}) => {
  const frame = useCurrentFrame();

  const fadeOut = interpolate(
    frame,
    [durationFrames - 45, durationFrames],
    [1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  return (
    <AbsoluteFill style={{ opacity: fadeOut }}>
      {/* Visual layer */}
      {visualType === "video" && videoFile ? (
        <VideoClip src={videoFile} durationFrames={durationFrames} />
      ) : visualType === "multiframe" && frameFiles.length > 1 ? (
        <CrossfadeFrames frames={frameFiles} durationFrames={durationFrames} variant={sceneVariant} />
      ) : (
        <KenBurnsImage src={imageFile} durationFrames={durationFrames} variant={sceneVariant} />
      )}

      {/* Dark overlay */}
      <AbsoluteFill
        style={{
          background: "linear-gradient(transparent 30%, rgba(0,0,0,0.85) 100%)",
        }}
      />

      {/* Subtitle */}
      <AnimatedSubtitle text={narration} durationFrames={durationFrames} />
    </AbsoluteFill>
  );
};
