import React from 'react';
import {AbsoluteFill, useCurrentFrame, useVideoConfig, interpolate, random} from 'remotion';
import {C} from './theme';

/**
 * Deep-green stage with a music-driven equaliser motif and a light sweep.
 * Runs for the whole piece so cuts feel like one continuous world.
 */
export const Backdrop: React.FC = () => {
  const frame = useCurrentFrame();
  const {width, height, durationInFrames} = useVideoConfig();

  const barCount = 34;
  const barWidth = width / barCount;

  // Slow ambient drift on the base gradient.
  const drift = interpolate(frame, [0, durationInFrames], [0, 14]);

  // Light sweep crossing the frame on every scene change.
  const sweepX = interpolate(
    frame % 78,
    [0, 26],
    [-width * 0.7, width * 1.4],
    {extrapolateRight: 'clamp'}
  );

  return (
    <AbsoluteFill style={{backgroundColor: C.greenDeep, overflow: 'hidden'}}>
      <AbsoluteFill
        style={{
          background: `radial-gradient(120% 90% at ${28 + drift}% ${18 + drift * 0.4}%, ${C.greenMid} 0%, ${C.greenDark} 42%, ${C.greenDeep} 100%)`,
        }}
      />

      {/* Equaliser bars along the bottom — the music cue. */}
      <AbsoluteFill style={{justifyContent: 'flex-end'}}>
        <div style={{display: 'flex', alignItems: 'flex-end', height: height * 0.42}}>
          {new Array(barCount).fill(0).map((_, i) => {
            const seed = random(`bar-${i}`);
            const speed = 0.16 + seed * 0.22;
            const h =
              (0.12 + 0.88 * Math.abs(Math.sin(frame * speed + seed * 12))) *
              height *
              (0.10 + seed * 0.30);
            return (
              <div
                key={i}
                style={{
                  width: barWidth,
                  height: h,
                  background: `linear-gradient(to top, ${C.greenBright}, transparent)`,
                  opacity: 0.16,
                }}
              />
            );
          })}
        </div>
      </AbsoluteFill>

      {/* Vignette keeps type legible over the bars. */}
      <AbsoluteFill
        style={{
          background: `radial-gradient(85% 70% at 50% 45%, transparent 0%, rgba(2,41,26,0.72) 100%)`,
        }}
      />

      {/* Fast light sweep. */}
      <AbsoluteFill style={{overflow: 'hidden'}}>
        <div
          style={{
            position: 'absolute',
            top: -height * 0.3,
            left: sweepX,
            width: width * 0.22,
            height: height * 1.6,
            transform: 'rotate(14deg)',
            background: `linear-gradient(90deg, transparent, rgba(244,241,230,0.10), transparent)`,
          }}
        />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
