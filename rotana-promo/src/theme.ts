// Rotana Music promo — brand tokens.
// Greens sampled from the Rotana orb mark; cream is the swoosh / type colour.
export const C = {
  greenDeep: '#02291A',
  greenDark: '#064A2A',
  green: '#0B6B3A',
  greenMid: '#0E7A45',
  greenBright: '#19A85C',
  cream: '#F4F1E6',
  white: '#FFFFFF',
} as const;

export const FPS = 30;
export const DURATION_FRAMES = 420; // 14s

// Scene boundaries in frames. Kept here so both formats stay in lockstep.
export const SCENES = {
  open: { from: 0, durationInFrames: 100 },
  hiring: { from: 100, durationInFrames: 68 },
  role: { from: 168, durationInFrames: 110 },
  line: { from: 278, durationInFrames: 64 },
  cta: { from: 342, durationInFrames: 78 },
} as const;

// A swoosh curtain straddles every cut so the change happens behind it.
// `from` is set ~8 frames before the boundary; the curtain covers at midpoint.
export const WIPES = [
  { from: 92, durationInFrames: 17, color: C.cream },
  { from: 160, durationInFrames: 17, color: C.greenBright },
  { from: 270, durationInFrames: 17, color: C.cream },
  { from: 334, durationInFrames: 17, color: C.greenBright },
] as const;

export type Format = 'linkedin' | 'web';

// One layout knob per format instead of branching all over the scenes.
export const layout = (format: Format) => {
  const portrait = format === 'linkedin';
  return {
    portrait,
    // Type scale multiplier relative to the 1920x1080 design.
    k: portrait ? 0.92 : 1,
    // Safe horizontal inset.
    pad: portrait ? 96 : 200,
    maxTextWidth: portrait ? 900 : 1420,
  };
};
