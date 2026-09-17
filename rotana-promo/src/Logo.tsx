import React from 'react';
import {Img, staticFile, interpolate} from 'remotion';
import {C} from './theme';
import {HAS_LOGO_FILE} from './logoFlag';

/**
 * The swoosh, traced from the supplied mark: the band enters at the left edge
 * around 46% height, dips through the lower half, then tapers as it sweeps up
 * and exits high on the right. Green stays visible below it.
 */
const SWOOSH =
  'M -4,46 C 12,58 28,63 47,58 C 66,53 79,36 100,25 ' +
  'L 100,41 C 80,50 67,71 47,79 C 26,86 6,75 -4,65 Z';

/**
 * The Rotana orb: a shaded green sphere crossed by a cream swoosh that enters
 * at the left edge, dips through the lower half and exits high on the right.
 *
 * `draw` (0..1) paints the swoosh on left-to-right — used for the reveal.
 * If `public/logo.png` exists it wins and this vector is bypassed entirely.
 */
export const Logo: React.FC<{size: number; draw?: number}> = ({size, draw = 1}) => {
  if (HAS_LOGO_FILE) {
    return (
      <Img
        src={staticFile('logo.png')}
        style={{width: size, height: size, objectFit: 'contain'}}
      />
    );
  }

  const uid = React.useId().replace(/:/g, '');
  // The paint-on wipe travels a little past the right edge so it fully clears.
  const wipeW = interpolate(draw, [0, 1], [0, 125], {extrapolateRight: 'clamp'});

  return (
    <svg width={size} height={size} viewBox="0 0 100 100" overflow="visible">
      <defs>
        <radialGradient id={`orb${uid}`} cx="33%" cy="26%" r="84%">
          <stop offset="0%" stopColor="#2BBF6E" />
          <stop offset="38%" stopColor={C.greenMid} />
          <stop offset="78%" stopColor={C.green} />
          <stop offset="100%" stopColor="#03301C" />
        </radialGradient>

        <linearGradient id={`band${uid}`} x1="0%" y1="100%" x2="100%" y2="0%">
          <stop offset="0%" stopColor="#E4E0D2" />
          <stop offset="45%" stopColor={C.white} />
          <stop offset="100%" stopColor="#EFEBDD" />
        </linearGradient>

        <clipPath id={`circ${uid}`}>
          <circle cx="50" cy="50" r="50" />
        </clipPath>

        <clipPath id={`wipe${uid}`}>
          <rect x="-12" y="-12" width={wipeW} height="124" />
        </clipPath>
      </defs>

      <circle cx="50" cy="50" r="50" fill={`url(#orb${uid})`} />

      <g clipPath={`url(#circ${uid})`}>
        <g clipPath={`url(#wipe${uid})`}>
          {/* Soft contact shadow so the band sits on the sphere. */}
          <path d={SWOOSH} fill="rgba(2,41,26,0.32)" transform="translate(-1,3.5)" />
          <path d={SWOOSH} fill={`url(#band${uid})`} />
        </g>
      </g>

      {/* Rim light along the upper-left, as on the original mark. */}
      <circle
        cx="50"
        cy="50"
        r="49.4"
        fill="none"
        stroke="rgba(255,255,255,0.16)"
        strokeWidth="1.2"
      />
    </svg>
  );
};
