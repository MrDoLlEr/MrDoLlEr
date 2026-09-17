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
  hook: { from: 0, durationInFrames: 78 },
  hiring: { from: 78, durationInFrames: 72 },
  role: { from: 150, durationInFrames: 108 },
  line: { from: 258, durationInFrames: 78 },
  cta: { from: 336, durationInFrames: 84 },
} as const;

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
