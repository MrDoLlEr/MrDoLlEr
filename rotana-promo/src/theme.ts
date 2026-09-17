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
  open: { from: 0, durationInFrames: 104 },
  hiring: { from: 104, durationInFrames: 72 },
  role: { from: 176, durationInFrames: 112 },
  line: { from: 288, durationInFrames: 64 },
  cta: { from: 352, durationInFrames: 68 },
} as const;

// A swoosh curtain straddles every cut so the change happens behind it.
// 26 frames (~0.87s) — slow enough that the swoosh silhouette reads as the
// brand mark on its way past, rather than flicking by.
const WIPE_LEN = 26;
export const WIPES = [
  { from: 104 - WIPE_LEN / 2, durationInFrames: WIPE_LEN, color: C.cream },
  { from: 176 - WIPE_LEN / 2, durationInFrames: WIPE_LEN, color: C.greenBright },
  { from: 288 - WIPE_LEN / 2, durationInFrames: WIPE_LEN, color: C.cream },
  { from: 352 - WIPE_LEN / 2, durationInFrames: WIPE_LEN, color: C.greenBright },
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
