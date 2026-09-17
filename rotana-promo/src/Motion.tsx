import React from 'react';
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
  Easing,
} from 'remotion';
import {C} from './theme';
import {Logo} from './Logo';
import {fontFamily} from './Type';

const sans = `${fontFamily}, Helvetica, Arial, sans-serif`;

/**
 * A full-frame curtain whose leading edge is the logo's swoosh curve.
 * Deliberately unhurried: the curve has to read as the brand mark on its
 * way past, so it eases in and out rather than snapping across.
 */
export const SwooshWipe: React.FC<{color?: string; duration?: number}> = ({
  color = C.cream,
  duration = 26,
}) => {
  const frame = useCurrentFrame();
  const {width, height} = useVideoConfig();

  const p = interpolate(frame, [0, duration], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    // Slow through the middle so the swoosh silhouette is legible.
    easing: Easing.bezier(0.5, 0.02, 0.5, 0.98),
  });

  const travel = interpolate(p, [0, 1], [-1.3, 1.3]) * width;

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
 * Background orbs on fixed, organised positions — a deliberate arrangement
 * around the edges rather than a random scatter, so the centre stays clear
 * for type. Each drifts on its own slow sine; nothing crosses the middle.
 */
type OrbSpec = {x: number; y: number; r: number; speed: number; phase: number};

// Normalised positions, kept outside the central safe area.
const ORBS: OrbSpec[] = [
  {x: 0.07, y: 0.16, r: 0.075, speed: 0.55, phase: 0.0},
  {x: 0.93, y: 0.24, r: 0.052, speed: 0.72, phase: 1.3},
  {x: 0.15, y: 0.78, r: 0.062, speed: 0.61, phase: 2.5},
  {x: 0.88, y: 0.72, r: 0.085, speed: 0.48, phase: 3.9},
  {x: 0.04, y: 0.48, r: 0.038, speed: 0.86, phase: 5.1},
  {x: 0.96, y: 0.52, r: 0.044, speed: 0.79, phase: 0.7},
  {x: 0.26, y: 0.06, r: 0.034, speed: 0.93, phase: 4.4},
  {x: 0.74, y: 0.94, r: 0.048, speed: 0.67, phase: 2.0},
];

export const OrbField: React.FC<{count?: number; opacity?: number}> = ({
  count = 6,
  opacity = 1,
}) => {
  const frame = useCurrentFrame();
  const {width, height} = useVideoConfig();
  const specs = ORBS.slice(0, count);

  return (
    <AbsoluteFill style={{overflow: 'hidden'}}>
      {specs.map((o, i) => {
        const size = o.r * width;
        // Gentle figure-of-eight drift — smooth, never abrupt.
        const t = frame * 0.01 * o.speed + o.phase;
        const dx = Math.sin(t) * width * 0.018;
        const dy = Math.cos(t * 0.8) * height * 0.022;
        return (
          <div
            key={i}
            style={{
              position: 'absolute',
              left: o.x * width - size / 2 + dx,
              top: o.y * height - size / 2 + dy,
              width: size,
              height: size,
              // Classic bokeh: the larger an orb reads, the nearer it is to
              // the lens, so the more defocused and the fainter it gets.
              opacity: (0.20 - o.r * 0.85) * opacity,
              filter: `blur(${5 + o.r * 165}px)`,
            }}
          >
            <Logo size={size} />
          </div>
        );
      })}
    </AbsoluteFill>
  );
};

/** Scrolling marquee strip. */
export const Ticker: React.FC<{
  text: string;
  y: number;
  size: number;
  speed?: number;
  bg?: string;
  fg?: string;
  angle?: number;
}> = ({text, y, size, speed = 3, bg = C.greenBright, fg = C.greenDeep, angle = -2.5}) => {
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
          fontFamily: sans,
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

/** Text revealed behind a moving edge. */
export const MaskReveal: React.FC<{
  children: React.ReactNode;
  delay?: number;
  duration?: number;
  from?: 'left' | 'bottom';
}> = ({children, delay = 0, duration = 18, from = 'left'}) => {
  const frame = useCurrentFrame();
  const p = interpolate(frame - delay, [0, duration], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.bezier(0.6, 0, 0.2, 1),
  });
  const inset =
    from === 'left'
      ? `inset(0 ${(1 - p) * 100}% 0 0)`
      : `inset(${(1 - p) * 100}% 0 0 0)`;
  return <div style={{clipPath: inset, WebkitClipPath: inset}}>{children}</div>;
};

/**
 * Typewriter: characters land one at a time behind a blinking caret.
 * `cps` is characters per second.
 */
export const Typewriter: React.FC<{
  text: string;
  delay?: number;
  cps?: number;
  caret?: boolean;
  style?: React.CSSProperties;
}> = ({text, delay = 0, cps = 26, caret = true, style}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  const started = frame >= delay;
  const elapsed = Math.max(0, frame - delay) / fps;
  const shown = Math.min(text.length, Math.floor(elapsed * cps));
  const done = shown >= text.length;
  // Caret appears only once typing begins; it blinks after the last character.
  const blink = Math.floor((frame / fps) * 2.6) % 2 === 0;
  const caretOn =
    caret && started && (done ? blink && frame - delay < fps * 2.4 : true);

  return (
    <div style={{...style, whiteSpace: 'pre-wrap'}}>
      {text.slice(0, shown)}
      <span
        style={{
          opacity: caretOn ? 1 : 0,
          color: C.greenBright,
        }}
      >
        |
      </span>
    </div>
  );
};

/** Big word that lands with overshoot. */
export const Slam: React.FC<{children: React.ReactNode; delay?: number}> = ({
  children,
  delay = 0,
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const p = spring({
    frame: frame - delay,
    fps,
    config: {damping: 15, mass: 0.8, stiffness: 170},
    durationInFrames: 30,
  });
  return (
    <div
      style={{
        transform: `scale(${interpolate(p, [0, 1], [1.45, 1])})`,
        opacity: interpolate(frame - delay, [0, 4], [0, 1], {
          extrapolateLeft: 'clamp',
          extrapolateRight: 'clamp',
        }),
      }}
    >
      {children}
    </div>
  );
};

/** Thin corner brackets — frames the composition without adding noise. */
export const CornerFrame: React.FC<{inset: number; color?: string; delay?: number}> = ({
  inset,
  color = C.greenBright,
  delay = 0,
}) => {
  const frame = useCurrentFrame();
  const len = interpolate(frame - delay, [0, 20], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.bezier(0.6, 0, 0.2, 1),
  });
  const arm = 78 * len;
  const t = 3;
  const corners = [
    {top: inset, left: inset, bt: true, bl: true},
    {top: inset, right: inset, bt: true, br: true},
    {bottom: inset, left: inset, bb: true, bl: true},
    {bottom: inset, right: inset, bb: true, br: true},
  ] as const;

  return (
    <AbsoluteFill style={{pointerEvents: 'none'}}>
      {corners.map((c, i) => (
        <div
          key={i}
          style={{
            position: 'absolute',
            top: 'top' in c ? c.top : undefined,
            bottom: 'bottom' in c ? c.bottom : undefined,
            left: 'left' in c ? c.left : undefined,
            right: 'right' in c ? c.right : undefined,
            width: arm,
            height: arm,
            borderTop: 'bt' in c ? `${t}px solid ${color}` : undefined,
            borderBottom: 'bb' in c ? `${t}px solid ${color}` : undefined,
            borderLeft: 'bl' in c ? `${t}px solid ${color}` : undefined,
            borderRight: 'br' in c ? `${t}px solid ${color}` : undefined,
            opacity: 0.5,
          }}
        />
      ))}
    </AbsoluteFill>
  );
};

/** Pill chips that pop in on a stagger — adds content density. */
export const Chips: React.FC<{items: string[]; size: number; delay?: number}> = ({
  items,
  size,
  delay = 0,
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  return (
    <div style={{display: 'flex', flexWrap: 'wrap', gap: size * 0.6, justifyContent: 'center'}}>
      {items.map((it, i) => {
        const p = spring({
          frame: frame - delay - i * 5,
          fps,
          config: {damping: 16, mass: 0.6},
          durationInFrames: 20,
        });
        return (
          <div
            key={it}
            style={{
              transform: `scale(${p})`,
              opacity: p,
              border: `2px solid rgba(244,241,230,0.34)`,
              borderRadius: 999,
              padding: `${size * 0.46}px ${size * 1.1}px`,
              fontFamily: sans,
              fontWeight: 800,
              fontSize: size,
              letterSpacing: '0.16em',
              color: C.cream,
              textTransform: 'uppercase',
            }}
          >
            {it}
          </div>
        );
      })}
    </div>
  );
};

/** Slim progress rail showing how far through the promo we are. */
export const ProgressRail: React.FC<{y: number; inset: number}> = ({y, inset}) => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();
  const p = interpolate(frame, [0, durationInFrames], [0, 1]);
  return (
    <div
      style={{
        position: 'absolute',
        left: inset,
        right: inset,
        top: y,
        height: 4,
        borderRadius: 4,
        backgroundColor: 'rgba(244,241,230,0.16)',
        overflow: 'hidden',
      }}
    >
      <div
        style={{
          width: `${p * 100}%`,
          height: '100%',
          backgroundColor: C.greenBright,
          borderRadius: 4,
        }}
      />
    </div>
  );
};
