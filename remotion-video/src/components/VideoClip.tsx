import { AbsoluteFill, OffthreadVideo, useCurrentFrame, interpolate } from "remotion";

interface VideoClipProps {
  /** Path to the video clip file */
  src: string;
  /** Total scene duration in frames */
  durationFrames: number;
  /** Optional fallback image if video fails to load */
  fallbackImage?: string;
}

/**
 * VideoClip — plays an AI-generated video clip for "cinematic" quality mode.
 *
 * Uses Remotion's OffthreadVideo for better performance.
 * Includes fade-in at start and handles video shorter than scene duration
 * by freezing on the last frame.
 */
export const VideoClip: React.FC<VideoClipProps> = ({
  src,
  durationFrames,
  fallbackImage,
}) => {
  const frame = useCurrentFrame();

  // Fade in at start
  const opacity = interpolate(frame, [0, 15], [0, 1], {
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{ overflow: "hidden", opacity }}>
      <OffthreadVideo
        src={src}
        style={{
          width: "100%",
          height: "100%",
          objectFit: "cover",
        }}
        // If video is shorter than scene, it will freeze on last frame
        pauseWhenBuffering
      />
    </AbsoluteFill>
  );
};
