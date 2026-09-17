import React from 'react';
import {Img, staticFile} from 'remotion';
import {C} from './theme';
import {HAS_LOGO_FILE} from './logoFlag';

/**
 * The Rotana orb.
 *
 * If `public/logo.png` exists it is used verbatim — drop the official asset
 * there and it wins. Otherwise we draw a vector stand-in of the mark so the
 * cut is always reviewable end to end.
 */
export const Logo: React.FC<{size: number; spin?: number}> = ({size, spin = 0}) => {
  if (HAS_LOGO_FILE) {
    return (
      <Img
        src={staticFile('logo.png')}
        style={{width: size, height: size, objectFit: 'contain'}}
      />
    );
  }

  return (
    <svg width={size} height={size} viewBox="0 0 100 100">
      <defs>
        <radialGradient id="orb" cx="34%" cy="28%" r="82%">
          <stop offset="0%" stopColor={C.greenBright} />
          <stop offset="46%" stopColor={C.greenMid} />
          <stop offset="100%" stopColor={C.greenDark} />
        </radialGradient>
        <clipPath id="orbClip">
          <circle cx="50" cy="50" r="49.5" />
        </clipPath>
      </defs>

      <circle cx="50" cy="50" r="49.5" fill="url(#orb)" />

      <g clipPath="url(#orbClip)" transform={`rotate(${spin} 50 50)`}>
        {/* The cream swoosh sweeping low-left to high-right. */}
        <path
          d="M -4,40 C 10,74 36,86 57,70 C 75,56 84,30 104,20
             L 104,44 C 86,54 78,76 58,88 C 32,104 0,84 -4,60 Z"
          fill={C.cream}
        />
      </g>
    </svg>
  );
};
