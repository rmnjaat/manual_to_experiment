import { AbsoluteFill, Img, useCurrentFrame, interpolate } from "remotion";

interface KenBurnsImageProps {
  src: string;
  durationFrames: number;
  /** Variant 0-3 for different pan/zoom directions per scene */
  variant?: number;
}

const DIRECTIONS = [
  { scaleFrom: 1.0, scaleTo: 1.12, xFrom: 0, xTo: -20, yFrom: 0, yTo: -10 },   // zoom in, pan right+down
  { scaleFrom: 1.1, scaleTo: 1.0, xFrom: -15, xTo: 15, yFrom: 0, yTo: 0 },      // zoom out, pan left to right
  { scaleFrom: 1.0, scaleTo: 1.08, xFrom: 10, xTo: -10, yFrom: -5, yTo: 5 },    // zoom in, pan right to left
  { scaleFrom: 1.05, scaleTo: 1.0, xFrom: 0, xTo: 0, yFrom: 10, yTo: -10 },     // zoom out, pan up
];

export const KenBurnsImage: React.FC<KenBurnsImageProps> = ({
  src,
  durationFrames,
  variant = 0,
}) => {
  const frame = useCurrentFrame();
  const dir = DIRECTIONS[variant % DIRECTIONS.length];

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
