import React from 'react';
import {useCurrentFrame, interpolate, spring, useVideoConfig} from 'remotion';
import {continueRender, delayRender, staticFile} from 'remotion';
import {C} from './theme';

export const fontFamily = 'Montserrat';

// Montserrat is vendored under public/fonts so renders never depend on the
// network (and never trip over the sandbox proxy's CA).
const handle = delayRender('Loading Montserrat');
const face = new FontFace(
  fontFamily,
  `url(${staticFile('fonts/montserrat-latin.woff2')}) format('woff2')`,
  {weight: '100 900', style: 'normal'}
);
face
  .load()
  .then((loaded) => {
    document.fonts.add(loaded);
    continueRender(handle);
  })
  .catch((err) => {
    // Fall back to a system stack rather than failing the whole render.
    console.error('Montserrat failed to load', err);
    continueRender(handle);
  });

type WordsProps = {
  text: string;
  size: number;
  color?: string;
  weight?: number;
  delay?: number;
  stagger?: number;
  letterSpacing?: number;
  lineHeight?: number;
  align?: 'left' | 'center';
  maxWidth?: number;
};

/**
 * Word-by-word reveal: each word rises out of a clipped band.
 * This is the workhorse for every headline in the promo.
 */
export const Words: React.FC<WordsProps> = ({
  text,
  size,
  color = C.cream,
  weight = 900,
  delay = 0,
  stagger = 3,
  letterSpacing = -0.02,
  lineHeight = 1.02,
  align = 'center',
  maxWidth,
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const words = text.split(' ');

  return (
    <div
      style={{
        display: 'flex',
        flexWrap: 'wrap',
        justifyContent: align === 'center' ? 'center' : 'flex-start',
        gap: `0 ${size * 0.26}px`,
        maxWidth,
        fontFamily: `${fontFamily}, Helvetica, Arial, sans-serif`,
        fontWeight: weight,
        fontSize: size,
        lineHeight,
        letterSpacing: `${letterSpacing}em`,
        color,
        textTransform: 'uppercase',
        textAlign: align,
      }}
    >
      {words.map((w, i) => {
        const local = frame - delay - i * stagger;
        const p = spring({
          frame: local,
          fps,
          config: {damping: 200, mass: 0.5},
          durationInFrames: 18,
        });
        return (
          <span
            key={`${w}-${i}`}
            style={{overflow: 'hidden', display: 'inline-block', paddingBottom: size * 0.1}}
          >
            <span
              style={{
                display: 'inline-block',
                transform: `translateY(${(1 - p) * size * 1.15}px)`,
                opacity: interpolate(local, [0, 4], [0, 1], {
                  extrapolateLeft: 'clamp',
                  extrapolateRight: 'clamp',
                }),
              }}
            >
              {w}
            </span>
          </span>
        );
      })}
    </div>
  );
};

/** Accent rule that wipes open from the centre. */
export const Rule: React.FC<{width: number; delay?: number; thickness?: number}> = ({
  width,
  delay = 0,
  thickness = 8,
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const p = spring({
    frame: frame - delay,
    fps,
    config: {damping: 200},
    durationInFrames: 16,
  });
  return (
    <div
      style={{
        width: width * p,
        height: thickness,
        backgroundColor: C.greenBright,
        borderRadius: thickness,
      }}
    />
  );
};
