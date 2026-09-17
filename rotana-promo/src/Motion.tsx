import React from 'react';
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
  random,
  Easing,
} from 'remotion';
import {C} from './theme';
import {Logo} from './Logo';
import {fontFamily} from './Type';

/**
 * A full-frame curtain whose leading edge is the logo's swoosh curve.
 * It sweeps across the frame, covering and then uncovering — so the cut
 * underneath happens while the screen is hidden. This is the promo's
 * signature transition: the brand mark itself does the wiping.
 */
export const SwooshWipe: React.FC<{color?: string; duration?: number}> = ({
  color = C.cream,
  duration = 18,
}) => {
  const frame = useCurrentFrame();
  const {width, height} = useVideoConfig();

  // 0 -> fully off left, 1 -> fully off right. Covers the frame around 0.5.
  const p = interpolate(frame, [0, duration], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.bezier(0.76, 0, 0.24, 1),
  });

  const travel = interpolate(p, [0, 1], [-1.35, 1.35]) * width;

  return (
    <AbsoluteFill style={{overflow: 'hidden', pointerEvents: 'none'}}>
      <svg
        width={width * 1.3}
        height={height}
        viewBox="0 0 130 100"
        preserveAspectRatio="none"
        style={{position: 'absolute', left: travel, top: 0}}
      >
        {/* Leading edge mirrors the swoosh: dips low, then sweeps up. */}
        <path
          d="M 0,-5 L 92,-5 C 104,22 84,52 62,68 C 44,82 28,92 22,105 L 0,105 Z"
          fill={color}
        />
      </svg>
    </AbsoluteFill>
  );
};

/**
 * Parallax field of out-of-focus orbs. Gives the frame depth so type is
 * sitting inside a space rather than pasted on a flat fill.
 */
export const OrbField: React.FC<{count?: number}> = ({count = 7}) => {
  const frame = useCurrentFrame();
  const {width, height} = useVideoConfig();

  return (
    <AbsoluteFill style={{overflow: 'hidden'}}>
      {new Array(count).fill(0).map((_, i) => {
        const s = random(`orb-x-${i}`);
        const s2 = random(`orb-y-${i}`);
        const s3 = random(`orb-r-${i}`);
        const depth = 0.3 + s3 * 0.9; // nearer orbs move more
        const size = (0.045 + s3 * 0.085) * width;
        // Push them toward the edges so the centre stays clean for type.
        const edge = s < 0.5 ? s * 0.3 : 0.7 + (s - 0.5) * 0.6;
        const x = edge * width - size / 2 + Math.sin(frame * 0.012 + i) * 26 * depth;
        const y =
          s2 * height - size / 2 + Math.cos(frame * 0.015 + i * 1.7) * 22 * depth;
        return (
          <div
            key={i}
            style={{
              position: 'absolute',
              left: x,
              top: y,
              width: size,
              height: size,
              opacity: 0.16 + s3 * 0.16,
              filter: `blur(${2 + (1 - s3) * 7}px)`,
            }}
          >
            <Logo size={size} />
          </div>
        );
      })}
    </AbsoluteFill>
  );
};

/** Scrolling marquee strip — the "always-on" energy element. */
export const Ticker: React.FC<{
  text: string;
  y: number;
  size: number;
  speed?: number;
  bg?: string;
  fg?: string;
  angle?: number;
}> = ({text, y, size, speed = 3.4, bg = C.greenBright, fg = C.greenDeep, angle = -2.5}) => {
  const frame = useCurrentFrame();
  const {width} = useVideoConfig();
  const unit = `${text}   ●   `;
  const offset = -((frame * speed) % (size * unit.length * 0.62));

  return (
    <div
      style={{
        position: 'absolute',
        top: y,
        left: -width * 0.1,
        width: width * 1.2,
        backgroundColor: bg,
        transform: `rotate(${angle}deg)`,
        overflow: 'hidden',
        paddingTop: size * 0.3,
        paddingBottom: size * 0.34,
      }}
    >
      <div
        style={{
          whiteSpace: 'nowrap',
          transform: `translateX(${offset}px)`,
          fontFamily: `${fontFamily}, Helvetica, Arial, sans-serif`,
          fontWeight: 900,
          fontSize: size,
          letterSpacing: '0.04em',
          color: fg,
          textTransform: 'uppercase',
        }}
      >
        {unit.repeat(14)}
      </div>
    </div>
  );
};

/**
 * Text that reveals behind a moving edge rather than fading — reads as
 * designed motion instead of a dissolve.
 */
export const MaskReveal: React.FC<{
  children: React.ReactNode;
  delay?: number;
  duration?: number;
  from?: 'left' | 'bottom';
}> = ({children, delay = 0, duration = 16, from = 'left'}) => {
  const frame = useCurrentFrame();
  const p = interpolate(frame - delay, [0, duration], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.bezier(0.65, 0, 0.2, 1),
  });
  const inset =
    from === 'left'
      ? `inset(0 ${(1 - p) * 100}% 0 0)`
      : `inset(${(1 - p) * 100}% 0 0 0)`;
  return <div style={{clipPath: inset, WebkitClipPath: inset}}>{children}</div>;
};

/** Counts the frame into a subtle continuous push so nothing sits still. */
export const SlowPush: React.FC<{children: React.ReactNode; amount?: number}> = ({
  children,
  amount = 0.06,
}) => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();
  const scale = interpolate(frame, [0, durationInFrames], [1, 1 + amount]);
  return (
    <AbsoluteFill style={{transform: `scale(${scale})`}}>{children}</AbsoluteFill>
  );
};

/** Big number/word that slams in with overshoot. */
export const Slam: React.FC<{
  children: React.ReactNode;
  delay?: number;
}> = ({children, delay = 0}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const p = spring({
    frame: frame - delay,
    fps,
    config: {damping: 13, mass: 0.8, stiffness: 190},
    durationInFrames: 28,
  });
  return (
    <div
      style={{
        transform: `scale(${interpolate(p, [0, 1], [1.55, 1])})`,
        opacity: interpolate(frame - delay, [0, 3], [0, 1], {
          extrapolateLeft: 'clamp',
          extrapolateRight: 'clamp',
        }),
      }}
    >
      {children}
    </div>
  );
};
