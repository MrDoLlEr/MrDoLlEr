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
import {fontFamily} from './Type';
import {Logo} from './Logo';
import {
  SwooshWipe,
  OrbField,
  Ticker,
  MaskReveal,
  Typewriter,
  Slam,
  CornerFrame,
  Chips,
  ProgressRail,
} from './Motion';
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
  const {height} = useVideoConfig();

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

      {/* Runs the whole length, above the wipes. */}
      <ProgressRail y={height - 34 * k} inset={pad * 0.7} />
    </AbsoluteFill>
  );
};

/* ------------------------------------------------------------------ */
/* 1 — Logo reveal, then the hook (typed on)                           */
/* ------------------------------------------------------------------ */
const SceneOpen: React.FC<{k: number; pad: number}> = ({k, pad}) => {
  const frame = useCurrentFrame();
  const {fps, height} = useVideoConfig();

  const pop = spring({frame, fps, config: {damping: 14, mass: 0.8}, durationInFrames: 30});
  const draw = interpolate(frame, [16, 40], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.bezier(0.6, 0, 0.2, 1),
  });
  const travel = interpolate(frame, [44, 64], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.bezier(0.65, 0, 0.25, 1),
  });
  const orbSize = interpolate(travel, [0, 1], [320 * k, 118 * k]);
  const orbY = interpolate(travel, [0, 1], [0, -height * 0.21]);

  return (
    <AbsoluteFill>
      <Backdrop />
      <OrbField count={6} />
      <CornerFrame inset={pad * 0.55} delay={62} />

      <AbsoluteFill style={{justifyContent: 'center', alignItems: 'center'}}>
        <div style={{transform: `translateY(${orbY}px) scale(${pop})`}}>
          <Logo size={orbSize} draw={draw} />
        </div>
      </AbsoluteFill>

      <Centre pad={pad}>
        <div style={{marginTop: height * 0.09}}>
          <Typewriter
            text="Ready for your next move?"
            delay={58}
            cps={21}
            style={{
              fontFamily: sans,
              fontWeight: 900,
              fontSize: 104 * k,
              lineHeight: 1.06,
              letterSpacing: '-0.02em',
              color: C.cream,
              textTransform: 'uppercase',
              maxWidth: 1400,
            }}
          />
        </div>
      </Centre>
    </AbsoluteFill>
  );
};

/* ------------------------------------------------------------------ */
/* 2 — Contrast cut: cream frame, green type. No flash.                */
/* ------------------------------------------------------------------ */
const SceneHiring: React.FC<{k: number; pad: number; portrait: boolean}> = ({
  k,
  pad,
  portrait,
}) => {
  const {width, height} = useVideoConfig();

  return (
    <AbsoluteFill style={{backgroundColor: C.cream, overflow: 'hidden'}}>
      {/* Ghosted orb for texture, sized off the short edge. */}
      <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center'}}>
        <div style={{opacity: 0.075}}>
          <Logo size={Math.min(width, height) * 0.86} />
        </div>
      </AbsoluteFill>

      <Ticker
        text="WE'RE HIRING"
        y={height * (portrait ? 0.18 : 0.1)}
        size={44 * k}
        angle={-3}
        speed={3.4}
      />
      <Ticker
        text="APPLY NOW"
        y={height * (portrait ? 0.73 : 0.79)}
        size={44 * k}
        angle={2.6}
        speed={-3}
        bg={C.greenDeep}
        fg={C.cream}
      />

      <Centre pad={pad}>
        <div style={{display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
          <MaskReveal delay={6} duration={16}>
            <div
              style={{
                fontFamily: sans,
                fontWeight: 900,
                fontSize: 90 * k,
                letterSpacing: '0.02em',
                color: C.green,
                textTransform: 'uppercase',
                lineHeight: 1,
              }}
            >
              We're
            </div>
          </MaskReveal>

          <Slam delay={18}>
            <div
              style={{
                fontFamily: sans,
                fontWeight: 900,
                fontSize: (portrait ? 178 : 222) * k,
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
    </AbsoluteFill>
  );
};

/* ------------------------------------------------------------------ */
/* 3 — The role, typed on, with discipline chips                       */
/* ------------------------------------------------------------------ */
const SceneRole: React.FC<{
  k: number;
  pad: number;
  maxTextWidth: number;
  portrait: boolean;
}> = ({k, pad, maxTextWidth, portrait}) => {
  const size = (portrait ? 76 : 90) * k;

  return (
    <AbsoluteFill>
      <Backdrop />
      <OrbField count={8} />
      <CornerFrame inset={pad * 0.55} delay={4} />

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
          <MaskReveal delay={2} duration={14}>
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

          <Typewriter
            text={'Senior Social Media\nSpecialist'}
            delay={14}
            cps={30}
            caret={false}
            style={{
              fontFamily: sans,
              fontWeight: 900,
              fontSize: size,
              lineHeight: 1.06,
              letterSpacing: '-0.025em',
              color: C.cream,
              textTransform: 'uppercase',
            }}
          />

          <Typewriter
            text={'& Creative\nContent Writer'}
            delay={46}
            cps={30}
            style={{
              fontFamily: sans,
              fontWeight: 900,
              fontSize: size,
              lineHeight: 1.06,
              letterSpacing: '-0.025em',
              color: C.greenBright,
              textTransform: 'uppercase',
            }}
          />

          <div style={{marginTop: 10 * k}}>
            <Chips
              items={['Strategy', 'Copy', 'Campaigns']}
              size={22 * k}
              delay={76}
            />
          </div>
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
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 18 * k,
          maxWidth: maxTextWidth,
        }}
      >
        <MaskReveal delay={2} duration={20}>
          <div
            style={{
              fontFamily: sans,
              fontWeight: 900,
              fontSize: 98 * k,
              lineHeight: 1.06,
              letterSpacing: '-0.025em',
              color: C.cream,
              textTransform: 'uppercase',
            }}
          >
            Turn ideas
            <br />
            into impact.
          </div>
        </MaskReveal>

        <MaskReveal delay={26} duration={20}>
          <div
            style={{
              fontFamily: sans,
              fontWeight: 900,
              fontSize: 98 * k,
              lineHeight: 1.06,
              letterSpacing: '-0.025em',
              color: C.greenBright,
              textTransform: 'uppercase',
            }}
          >
            Join Rotana Music.
          </div>
        </MaskReveal>
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

  const orb = spring({frame, fps, config: {damping: 15, mass: 0.8}, durationInFrames: 30});
  const btn = spring({
    frame: frame - 22,
    fps,
    config: {damping: 14, mass: 0.7},
    durationInFrames: 26,
  });
  const pulse = 1 + Math.sin(Math.max(0, frame - 44) * 0.2) * 0.018;
  const draw = interpolate(frame, [6, 26], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill>
      <Backdrop />
      <OrbField count={5} />
      <CornerFrame inset={pad * 0.55} delay={2} />

      <Ticker
        text="APPLY NOW"
        y={height * (portrait ? 0.86 : 0.86)}
        size={36 * k}
        angle={-2}
        speed={3.2}
      />

      <Centre pad={pad}>
        <div
          style={{display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 30 * k}}
        >
          <div style={{transform: `scale(${orb})`}}>
            <Logo size={188 * k} draw={draw} />
          </div>

          <MaskReveal delay={16} duration={16}>
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

          <Typewriter
            text="rotanamusic.com/careers"
            delay={36}
            cps={42}
            style={{
              fontFamily: sans,
              fontWeight: 700,
              fontSize: 34 * k,
              letterSpacing: '0.1em',
              color: C.cream,
              textTransform: 'uppercase',
            }}
          />
        </div>
      </Centre>
    </AbsoluteFill>
  );
};
