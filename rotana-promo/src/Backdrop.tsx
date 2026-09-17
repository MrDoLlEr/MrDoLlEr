import React from 'react';
import {AbsoluteFill, useCurrentFrame, useVideoConfig, interpolate} from 'remotion';
import {C} from './theme';

/**
 * Deep-green stage. Deliberately matte: no light sweeps, no specular glare —
 * just a slow gradient drift, a faint dot grid and a soft equaliser bed, so
 * type always sits on a calm surface.
 */
export const Backdrop: React.FC = () => {
  const frame = useCurrentFrame();
  const {width, height, durationInFrames} = useVideoConfig();

  const barCount = 30;
  const barWidth = width / barCount;
  const drift = interpolate(frame, [0, durationInFrames], [0, 10]);

  return (
    <AbsoluteFill style={{backgroundColor: C.greenDeep, overflow: 'hidden'}}>
      <AbsoluteFill
        style={{
          background: `radial-gradient(125% 95% at ${30 + drift}% ${20 + drift * 0.3}%, ${C.greenMid} 0%, ${C.greenDark} 45%, ${C.greenDeep} 100%)`,
        }}
      />

      {/* Fine dot grid — texture without noise. */}
      <AbsoluteFill
        style={{
          backgroundImage: `radial-gradient(rgba(244,241,230,0.10) 1.5px, transparent 1.5px)`,
          backgroundSize: `${width / 42}px ${width / 42}px`,
          opacity: 0.5,
        }}
      />

      {/* Equaliser bed along the bottom — the music cue, kept very low. */}
      <AbsoluteFill style={{justifyContent: 'flex-end'}}>
        <div style={{display: 'flex', alignItems: 'flex-end', height: height * 0.34}}>
          {new Array(barCount).fill(0).map((_, i) => {
            const seed = (i * 37) % 11 / 11;
            const speed = 0.10 + seed * 0.10;
            const h =
              (0.25 + 0.75 * Math.abs(Math.sin(frame * speed + seed * 9))) *
              height *
              (0.08 + seed * 0.2);
            return (
              <div
                key={i}
                style={{
                  width: barWidth,
                  height: h,
                  background: `linear-gradient(to top, ${C.greenBright}, transparent)`,
                  opacity: 0.12,
                }}
              />
            );
          })}
        </div>
      </AbsoluteFill>

      {/* Vignette keeps the centre readable. */}
      <AbsoluteFill
        style={{
          background: `radial-gradient(88% 74% at 50% 46%, transparent 0%, rgba(2,41,26,0.70) 100%)`,
        }}
      />
    </AbsoluteFill>
  );
};
