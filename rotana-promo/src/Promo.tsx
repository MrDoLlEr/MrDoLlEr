import React from 'react';
import {
  AbsoluteFill,
  Sequence,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
  Audio,
  staticFile,
  Easing,
} from 'remotion';
import {C, SCENES, WIPES, layout, Format} from './theme';
import {Backdrop} from './Backdrop';
import {Words, fontFamily} from './Type';
import {Logo} from './Logo';
import {SwooshWipe, OrbField, Ticker, MaskReveal, Slam} from './Motion';
import {HAS_MUSIC_FILE} from './logoFlag';

const sans = `${fontFamily}, Helvetica, Arial, sans-serif`;

const Centre: React.FC<{children: React.ReactNode; pad: number}> = ({children, pad}) => (
  <AbsoluteFill
    style={{
      justifyContent: 'center',
      alignItems: 'center',
      textAlign: 'center',
      paddingLeft: pad,
      paddingRight: pad,
    }}
  >
    {children}
  </AbsoluteFill>
);

export const Promo: React.FC<{format: Format}> = ({format}) => {
  const {k, pad, maxTextWidth, portrait} = layout(format);

  return (
    <AbsoluteFill style={{backgroundColor: C.greenDeep}}>
      {HAS_MUSIC_FILE ? <Audio src={staticFile('music.mp3')} volume={0.9} /> : null}

      <Sequence {...SCENES.open}>
        <SceneOpen k={k} pad={pad} />
      </Sequence>

      <Sequence {...SCENES.hiring}>
        <SceneHiring k={k} pad={pad} portrait={portrait} />
      </Sequence>

      <Sequence {...SCENES.role}>
        <SceneRole k={k} pad={pad} maxTextWidth={maxTextWidth} portrait={portrait} />
      </Sequence>

      <Sequence {...SCENES.line}>
        <SceneLine k={k} pad={pad} maxTextWidth={maxTextWidth} />
      </Sequence>

      <Sequence {...SCENES.cta}>
        <SceneCta k={k} pad={pad} portrait={portrait} />
      </Sequence>

      {/* Swoosh curtains ride on top and hide every cut. */}
      {WIPES.map((w) => (
        <Sequence key={w.from} from={w.from} durationInFrames={w.durationInFrames}>
          <SwooshWipe color={w.color} duration={w.durationInFrames} />
        </Sequence>
      ))}
    </AbsoluteFill>
  );
};

/* ------------------------------------------------------------------ */
/* 1 — Logo reveal, then the hook                                      */
/* ------------------------------------------------------------------ */
const SceneOpen: React.FC<{k: number; pad: number}> = ({k, pad}) => {
  const frame = useCurrentFrame();
  const {fps, height} = useVideoConfig();

  const pop = spring({frame, fps, config: {damping: 12, mass: 0.7}, durationInFrames: 26});
  // The swoosh paints on after the sphere has landed.
  const draw = interpolate(frame, [14, 34], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.bezier(0.6, 0, 0.2, 1),
  });
  // Then the mark travels up and shrinks to make room for the headline.
  const travel = interpolate(frame, [40, 58], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.bezier(0.65, 0, 0.25, 1),
  });
  const orbSize = interpolate(travel, [0, 1], [330 * k, 112 * k]);
  const orbY = interpolate(travel, [0, 1], [0, -height * 0.2]);

  return (
    <AbsoluteFill>
      <Backdrop />
      <OrbField count={6} />

      <AbsoluteFill style={{justifyContent: 'center', alignItems: 'center'}}>
        <div style={{transform: `translateY(${orbY}px) scale(${pop})`}}>
          <Logo size={orbSize} draw={draw} />
        </div>
      </AbsoluteFill>

      <Centre pad={pad}>
        <div style={{marginTop: height * 0.08}}>
          <Words
            text="Ready for your next move?"
            size={112 * k}
            delay={52}
            stagger={3}
            maxWidth={1400}
          />
        </div>
      </Centre>
    </AbsoluteFill>
  );
};

/* ------------------------------------------------------------------ */
/* 2 — Contrast cut: cream frame, green type                           */
/* ------------------------------------------------------------------ */
const SceneHiring: React.FC<{k: number; pad: number; portrait: boolean}> = ({
  k,
  pad,
  portrait,
}) => {
  const frame = useCurrentFrame();
  const {width, height} = useVideoConfig();

  return (
    <AbsoluteFill style={{backgroundColor: C.cream, overflow: 'hidden'}}>
      {/* Ghosted orb for texture on the light frame. Sized off the SHORT edge
          so it stays contained in portrait as well as landscape. */}
      <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center'}}>
        <div style={{opacity: 0.075}}>
          <Logo size={Math.min(width, height) * 0.86} />
        </div>
      </AbsoluteFill>

      <Ticker
        text="WE'RE HIRING"
        y={height * (portrait ? 0.18 : 0.1)}
        size={46 * k}
        angle={-3}
        speed={4.2}
      />
      <Ticker
        text="APPLY NOW"
        y={height * (portrait ? 0.73 : 0.79)}
        size={46 * k}
        angle={2.6}
        speed={-3.6}
        bg={C.greenDeep}
        fg={C.cream}
      />

      <Centre pad={pad}>
        <div style={{display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
          <MaskReveal delay={4} duration={14}>
            <div
              style={{
                fontFamily: sans,
                fontWeight: 900,
                fontSize: 92 * k,
                letterSpacing: '0.02em',
                color: C.green,
                textTransform: 'uppercase',
                lineHeight: 1,
              }}
            >
              We're
            </div>
          </MaskReveal>

          <Slam delay={14}>
            <div
              style={{
                fontFamily: sans,
                fontWeight: 900,
                fontSize: (portrait ? 180 : 226) * k,
                lineHeight: 1,
                letterSpacing: '-0.045em',
                color: C.greenDeep,
                textTransform: 'uppercase',
              }}
            >
              Hiring!
            </div>
          </Slam>
        </div>
      </Centre>

      {/* Impact flash on the slam. */}
      <AbsoluteFill
        style={{
          backgroundColor: C.white,
          opacity: interpolate(frame, [14, 17, 24], [0, 0.5, 0], {
            extrapolateLeft: 'clamp',
            extrapolateRight: 'clamp',
          }),
        }}
      />
    </AbsoluteFill>
  );
};

/* ------------------------------------------------------------------ */
/* 3 — The role                                                        */
/* ------------------------------------------------------------------ */
const SceneRole: React.FC<{
  k: number;
  pad: number;
  maxTextWidth: number;
  portrait: boolean;
}> = ({k, pad, maxTextWidth, portrait}) => {
  const size = (portrait ? 78 : 92) * k;

  return (
    <AbsoluteFill>
      <Backdrop />
      <OrbField count={8} />

      <Centre pad={pad}>
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 26 * k,
            maxWidth: maxTextWidth,
          }}
        >
          <MaskReveal delay={2} duration={12}>
            <div
              style={{
                fontFamily: sans,
                fontWeight: 800,
                fontSize: 26 * k,
                letterSpacing: '0.42em',
                color: C.greenBright,
                textTransform: 'uppercase',
                border: `${2 * k}px solid ${C.greenBright}`,
                borderRadius: 999,
                padding: `${12 * k}px ${16 * k}px ${12 * k}px ${30 * k}px`,
              }}
            >
              Now open
            </div>
          </MaskReveal>

          <MaskReveal delay={14} duration={18}>
            <div
              style={{
                fontFamily: sans,
                fontWeight: 900,
                fontSize: size,
                lineHeight: 1.04,
                letterSpacing: '-0.025em',
                color: C.cream,
                textTransform: 'uppercase',
              }}
            >
              Senior Social Media
              <br />
              Specialist
            </div>
          </MaskReveal>

          <MaskReveal delay={40} duration={18}>
            <div
              style={{
                fontFamily: sans,
                fontWeight: 900,
                fontSize: size,
                lineHeight: 1.04,
                letterSpacing: '-0.025em',
                color: C.greenBright,
                textTransform: 'uppercase',
              }}
            >
              &amp; Creative
              <br />
              Content Writer
            </div>
          </MaskReveal>
        </div>
      </Centre>
    </AbsoluteFill>
  );
};

/* ------------------------------------------------------------------ */
/* 4 — The line                                                        */
/* ------------------------------------------------------------------ */
const SceneLine: React.FC<{k: number; pad: number; maxTextWidth: number}> = ({
  k,
  pad,
  maxTextWidth,
}) => (
  <AbsoluteFill>
    <Backdrop />
    <OrbField count={5} />
    <Centre pad={pad}>
      <div
        style={{display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 22 * k}}
      >
        <Words
          text="Turn ideas into impact."
          size={102 * k}
          delay={3}
          stagger={3}
          maxWidth={maxTextWidth}
        />
        <Words
          text="Join Rotana Music."
          size={102 * k}
          color={C.greenBright}
          delay={26}
          stagger={3}
          maxWidth={maxTextWidth}
        />
      </div>
    </Centre>
  </AbsoluteFill>
);

/* ------------------------------------------------------------------ */
/* 5 — CTA                                                             */
/* ------------------------------------------------------------------ */
const SceneCta: React.FC<{k: number; pad: number; portrait: boolean}> = ({
  k,
  pad,
  portrait,
}) => {
  const frame = useCurrentFrame();
  const {fps, height} = useVideoConfig();

  const orb = spring({frame, fps, config: {damping: 13, mass: 0.7}, durationInFrames: 26});
  const btn = spring({
    frame: frame - 24,
    fps,
    config: {damping: 12, mass: 0.6},
    durationInFrames: 24,
  });
  const pulse = 1 + Math.sin(Math.max(0, frame - 46) * 0.24) * 0.022;
  const draw = interpolate(frame, [4, 22], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill>
      <Backdrop />
      <OrbField count={5} />

      <Ticker
        text="APPLY NOW"
        y={height * (portrait ? 0.87 : 0.88)}
        size={38 * k}
        angle={-2}
        speed={4}
      />

      <Centre pad={pad}>
        <div
          style={{display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 32 * k}}
        >
          <div style={{transform: `scale(${orb})`}}>
            <Logo size={190 * k} draw={draw} />
          </div>

          <MaskReveal delay={18} duration={14}>
            <div
              style={{
                fontFamily: sans,
                fontWeight: 800,
                fontSize: 34 * k,
                letterSpacing: '0.34em',
                color: C.cream,
                textTransform: 'uppercase',
                paddingLeft: '0.34em',
              }}
            >
              Rotana Music
            </div>
          </MaskReveal>

          <div
            style={{
              transform: `scale(${btn * pulse})`,
              backgroundColor: C.greenBright,
              padding: `${20 * k}px ${62 * k}px`,
              borderRadius: 999,
              boxShadow: `0 ${18 * k}px ${44 * k}px rgba(25,168,92,0.34)`,
            }}
          >
            <div
              style={{
                fontFamily: sans,
                fontWeight: 900,
                fontSize: 56 * k,
                letterSpacing: '0.03em',
                color: C.greenDeep,
                textTransform: 'uppercase',
              }}
            >
              Apply now
            </div>
          </div>

          <MaskReveal delay={44} duration={14}>
            <div
              style={{
                fontFamily: sans,
                fontWeight: 700,
                fontSize: 34 * k,
                letterSpacing: '0.1em',
                color: C.cream,
                textTransform: 'uppercase',
              }}
            >
              rotanamusic.com/careers
            </div>
          </MaskReveal>
        </div>
      </Centre>
    </AbsoluteFill>
  );
};
