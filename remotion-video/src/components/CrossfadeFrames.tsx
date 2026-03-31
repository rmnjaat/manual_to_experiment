import { AbsoluteFill, Img, useCurrentFrame, interpolate } from "remotion";

interface CrossfadeFramesProps {
  /** Array of image file paths (e.g., 3 frames for enhanced mode) */
  frames: string[];
  /** Total scene duration in frames */
  durationFrames: number;
  /** Which Ken Burns variant to use (0-3) */
  variant?: number;
}

/**
 * CrossfadeFrames — smoothly crossfades between multiple images within a scene.
 *
 * For "enhanced" quality mode: shows 3 progressive frames of an action
 * with smooth dissolve transitions between them, plus Ken Burns effect on each.
 *
 * Timing for 3 frames over N total frames:
 *   Frame 0: visible 0% - 45% of duration (fade out at 35%-45%)
 *   Frame 1: visible 30% - 75% of duration (fade in 30%-40%, fade out 65%-75%)
 *   Frame 2: visible 60% - 100% of duration (fade in 60%-70%)
 */
export const CrossfadeFrames: React.FC<CrossfadeFramesProps> = ({
  frames,
  durationFrames,
  variant = 0,
}) => {
  const frame = useCurrentFrame();
  const count = frames.length;

  if (count === 0) return null;
  if (count === 1) {
    // Single frame fallback — just Ken Burns
    return <SingleKenBurns src={frames[0]} frame={frame} durationFrames={durationFrames} variant={variant} />;
  }

  // Calculate timing for each frame
  const segmentLength = durationFrames / count;
  const overlapFrames = Math.min(segmentLength * 0.35, 30); // 35% overlap, max 1 second

  return (
    <AbsoluteFill style={{ overflow: "hidden" }}>
      {frames.map((src, index) => {
        // Each frame's visibility window
        const fadeInStart = index === 0 ? 0 : index * segmentLength - overlapFrames;
        const fadeInEnd = index === 0 ? 0 : index * segmentLength + overlapFrames * 0.5;
        const fadeOutStart = index === count - 1 ? durationFrames : (index + 1) * segmentLength - overlapFrames;
        const fadeOutEnd = index === count - 1 ? durationFrames : (index + 1) * segmentLength + overlapFrames * 0.5;

        // Opacity: fade in → hold → fade out
        let opacity = 1;
        if (index > 0) {
          opacity = interpolate(frame, [fadeInStart, fadeInEnd], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          });
        }
        if (index < count - 1) {
          const fadeOut = interpolate(frame, [fadeOutStart, fadeOutEnd], [1, 0], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          });
          opacity = Math.min(opacity, fadeOut);
        }

        // Skip rendering if not visible
        if (opacity <= 0) return null;

        // Ken Burns: each frame gets a slightly different direction
        const kbVariant = (variant + index) % 4;

        return (
          <AbsoluteFill key={index} style={{ opacity }}>
            <SingleKenBurns
              src={src}
              frame={frame}
              durationFrames={durationFrames}
              variant={kbVariant}
            />
          </AbsoluteFill>
        );
      })}
    </AbsoluteFill>
  );
};

/** Single image with Ken Burns effect — varied direction per variant */
const SingleKenBurns: React.FC<{
  src: string;
  frame: number;
  durationFrames: number;
  variant: number;
}> = ({ src, frame, durationFrames, variant }) => {
  // Different Ken Burns directions based on variant
  const directions = [
    { scaleFrom: 1.0, scaleTo: 1.12, xFrom: 0, xTo: -20, yFrom: 0, yTo: -10 },   // zoom in, pan right+down
    { scaleFrom: 1.1, scaleTo: 1.0, xFrom: -15, xTo: 15, yFrom: 0, yTo: 0 },      // zoom out, pan left to right
    { scaleFrom: 1.0, scaleTo: 1.08, xFrom: 10, xTo: -10, yFrom: -5, yTo: 5 },    // zoom in, pan right to left
    { scaleFrom: 1.05, scaleTo: 1.0, xFrom: 0, xTo: 0, yFrom: 10, yTo: -10 },     // zoom out, pan up
  ];

  const dir = directions[variant % directions.length];

  const scale = interpolate(frame, [0, durationFrames], [dir.scaleFrom, dir.scaleTo], {
    extrapolateRight: "clamp",
  });
  const translateX = interpolate(frame, [0, durationFrames], [dir.xFrom, dir.xTo], {
    extrapolateRight: "clamp",
  });
  const translateY = interpolate(frame, [0, durationFrames], [dir.yFrom, dir.yTo], {
    extrapolateRight: "clamp",
  });

  // Fade in at start
  const opacity = interpolate(frame, [0, 15], [0, 1], {
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{ overflow: "hidden", opacity }}>
      <Img
        src={src}
        style={{
          width: "100%",
          height: "100%",
          objectFit: "cover",
          transform: `scale(${scale}) translate(${translateX}px, ${translateY}px)`,
        }}
      />
    </AbsoluteFill>
  );
};
