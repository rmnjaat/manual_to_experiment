import { AbsoluteFill, useCurrentFrame, interpolate } from "remotion";
import { AnimatedSubtitle } from "../components/AnimatedSubtitle";
import { KenBurnsImage } from "../components/KenBurnsImage";
import { CrossfadeFrames } from "../components/CrossfadeFrames";
import { VideoClip } from "../components/VideoClip";

interface IntroSceneProps {
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

export const IntroScene: React.FC<IntroSceneProps> = ({
  narration,
  durationFrames,
  imageFile,
  visualType = "image",
  frameFiles = [],
  videoFile,
  sceneVariant = 0,
}) => {
  const frame = useCurrentFrame();

  return (
    <AbsoluteFill>
      {/* Visual layer */}
      {visualType === "video" && videoFile ? (
        <VideoClip src={videoFile} durationFrames={durationFrames} />
      ) : visualType === "multiframe" && frameFiles.length > 1 ? (
        <CrossfadeFrames frames={frameFiles} durationFrames={durationFrames} variant={sceneVariant} />
      ) : (
        <KenBurnsImage src={imageFile} durationFrames={durationFrames} variant={sceneVariant} />
      )}

      {/* Dark overlay for text readability */}
      <AbsoluteFill
        style={{
          background: "linear-gradient(transparent 40%, rgba(0,0,0,0.8) 100%)",
        }}
      />

      {/* Subtitle at bottom */}
      <AnimatedSubtitle text={narration} durationFrames={durationFrames} />
    </AbsoluteFill>
  );
};
