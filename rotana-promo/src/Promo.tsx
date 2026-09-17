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
} from 'remotion';
import {C, SCENES, layout, Format} from './theme';
import {Backdrop} from './Backdrop';
import {Words, Rule, fontFamily} from './Type';
import {Logo} from './Logo';
import {HAS_MUSIC_FILE} from './logoFlag';

/**
 * Wraps a scene in a quick push-in + push-out so cuts read as hard and fast
 * rather than as dissolves. `hold` is the scene length in frames.
 */
const Cut: React.FC<{hold: number; children: React.ReactNode}> = ({hold, children}) => {
  const frame = useCurrentFrame();
  const inScale = interpolate(frame, [0, 8], [1.06, 1], {extrapolateRight: 'clamp'});
  const outScale = interpolate(frame, [hold - 7, hold], [1, 0.965], {
    extrapolateLeft: 'clamp',
  });
  const opacity = interpolate(
    frame,
    [0, 3, hold - 5, hold],
    [0, 1, 1, 0],
    {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}
  );
  return (
    <AbsoluteFill
      style={{
        transform: `scale(${inScale * outScale})`,
        opacity,
        justifyContent: 'center',
        alignItems: 'center',
      }}
    >
      {children}
    </AbsoluteFill>
  );
};

const Stack: React.FC<{gap: number; children: React.ReactNode; pad: number}> = ({
  gap,
  children,
  pad,
}) => (
  <div
    style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      gap,
      paddingLeft: pad,
      paddingRight: pad,
      textAlign: 'center',
    }}
  >
    {children}
  </div>
);

export const Promo: React.FC<{format: Format}> = ({format}) => {
  const {k, pad, maxTextWidth, portrait} = layout(format);

  return (
    <AbsoluteFill style={{backgroundColor: C.greenDeep}}>
      <Backdrop />

      {HAS_MUSIC_FILE ? <Audio src={staticFile('music.mp3')} volume={0.9} /> : null}

      {/* 1 — HOOK */}
      <Sequence {...SCENES.hook}>
        <Cut hold={SCENES.hook.durationInFrames}>
          <Stack gap={44 * k} pad={pad}>
            <CornerMark k={k} />
            <Words
              text="Ready for your next move?"
              size={118 * k}
              delay={6}
              stagger={3}
              maxWidth={maxTextWidth}
            />
            <Rule width={260 * k} delay={30} thickness={9 * k} />
          </Stack>
        </Cut>
      </Sequence>

      {/* 2 — WE'RE HIRING */}
      <Sequence {...SCENES.hiring}>
        <Cut hold={SCENES.hiring.durationInFrames}>
          <Stack gap={30 * k} pad={pad}>
            <Words
              text="We're"
              size={132 * k}
              color={C.white}
              delay={2}
              stagger={0}
            />
            <HiringSlam k={k} />
          </Stack>
        </Cut>
      </Sequence>

      {/* 3 — THE ROLE */}
      <Sequence {...SCENES.role}>
        <Cut hold={SCENES.role.durationInFrames}>
          <Stack gap={34 * k} pad={pad}>
            <Kicker text="Now open" k={k} />
            <Words
              text="Senior Social Media Specialist"
              size={(portrait ? 82 : 96) * k}
              delay={8}
              stagger={2}
              maxWidth={maxTextWidth}
            />
            <Rule width={200 * k} delay={30} thickness={7 * k} />
            <Words
              text="& Creative Content Writer"
              size={(portrait ? 82 : 96) * k}
              color={C.greenBright}
              delay={38}
              stagger={2}
              maxWidth={maxTextWidth}
            />
          </Stack>
        </Cut>
      </Sequence>

      {/* 4 — THE LINE */}
      <Sequence {...SCENES.line}>
        <Cut hold={SCENES.line.durationInFrames}>
          <Stack gap={36 * k} pad={pad}>
            <Words
              text="Turn ideas into impact."
              size={104 * k}
              delay={4}
              stagger={3}
              maxWidth={maxTextWidth}
            />
            <Words
              text="Join Rotana Music."
              size={104 * k}
              color={C.greenBright}
              delay={30}
              stagger={3}
              maxWidth={maxTextWidth}
            />
          </Stack>
        </Cut>
      </Sequence>

      {/* 5 — CTA */}
      <Sequence {...SCENES.cta}>
        <CtaScene k={k} pad={pad} hold={SCENES.cta.durationInFrames} />
      </Sequence>
    </AbsoluteFill>
  );
};

/** Small orb + wordmark lockup that sits above the hook line. */
const CornerMark: React.FC<{k: number}> = ({k}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const p = spring({frame, fps, config: {damping: 200}, durationInFrames: 22});
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 22 * k,
        opacity: p,
        transform: `translateY(${(1 - p) * 26}px)`,
      }}
    >
      <Logo size={74 * k} />
      <div
        style={{
          fontFamily: `${fontFamily}, Helvetica, Arial, sans-serif`,
          fontWeight: 800,
          fontSize: 34 * k,
          letterSpacing: '0.30em',
          color: C.cream,
          textTransform: 'uppercase',
        }}
      >
        Rotana Music
      </div>
    </div>
  );
};

const Kicker: React.FC<{text: string; k: number}> = ({text, k}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const p = spring({frame, fps, config: {damping: 200}, durationInFrames: 18});
  return (
    <div
      style={{
        fontFamily: `${fontFamily}, Helvetica, Arial, sans-serif`,
        fontWeight: 800,
        fontSize: 30 * k,
        letterSpacing: '0.36em',
        color: C.greenBright,
        textTransform: 'uppercase',
        opacity: p,
        transform: `translateY(${(1 - p) * 18}px)`,
      }}
    >
      {text}
    </div>
  );
};

/** "HIRING!" lands hard on a cream band. */
const HiringSlam: React.FC<{k: number}> = ({k}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const p = spring({
    frame: frame - 10,
    fps,
    config: {damping: 14, mass: 0.9, stiffness: 180},
    durationInFrames: 30,
  });
  const scale = interpolate(p, [0, 1], [1.5, 1]);
  return (
    <div
      style={{
        transform: `scale(${scale})`,
        opacity: interpolate(frame, [10, 14], [0, 1], {
          extrapolateLeft: 'clamp',
          extrapolateRight: 'clamp',
        }),
        backgroundColor: C.cream,
        padding: `${16 * k}px ${46 * k}px ${24 * k}px`,
        borderRadius: 14 * k,
      }}
    >
      <div
        style={{
          fontFamily: `${fontFamily}, Helvetica, Arial, sans-serif`,
          fontWeight: 900,
          fontSize: 184 * k,
          lineHeight: 1,
          letterSpacing: '-0.03em',
          color: C.greenDark,
          textTransform: 'uppercase',
        }}
      >
        Hiring!
      </div>
    </div>
  );
};

const CtaScene: React.FC<{k: number; pad: number; hold: number}> = ({k, pad, hold}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const orb = spring({frame, fps, config: {damping: 200}, durationInFrames: 26});
  const btn = spring({frame: frame - 26, fps, config: {damping: 14, mass: 0.7}, durationInFrames: 24});
  const pulse = 1 + Math.sin(Math.max(0, frame - 50) * 0.22) * 0.018;
  const fade = interpolate(frame, [0, 4, hold - 8, hold], [0, 1, 1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill
      style={{justifyContent: 'center', alignItems: 'center', opacity: fade}}
    >
      <Stack gap={40 * k} pad={pad}>
        <div style={{transform: `scale(${orb})`, opacity: orb}}>
          <Logo size={230 * k} />
        </div>

        <div
          style={{
            fontFamily: `${fontFamily}, Helvetica, Arial, sans-serif`,
            fontWeight: 800,
            fontSize: 38 * k,
            letterSpacing: '0.32em',
            color: C.cream,
            textTransform: 'uppercase',
            opacity: orb,
          }}
        >
          Rotana Music
        </div>

        <div
          style={{
            transform: `scale(${btn * pulse})`,
            opacity: btn,
            backgroundColor: C.greenBright,
            padding: `${22 * k}px ${64 * k}px`,
            borderRadius: 999,
          }}
        >
          <div
            style={{
              fontFamily: `${fontFamily}, Helvetica, Arial, sans-serif`,
              fontWeight: 900,
              fontSize: 60 * k,
              letterSpacing: '0.04em',
              color: C.greenDeep,
              textTransform: 'uppercase',
            }}
          >
            Apply now
          </div>
        </div>

        <div
          style={{
            fontFamily: `${fontFamily}, Helvetica, Arial, sans-serif`,
            fontWeight: 700,
            fontSize: 38 * k,
            letterSpacing: '0.12em',
            color: C.cream,
            textTransform: 'uppercase',
            opacity: interpolate(frame, [40, 52], [0, 1], {
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
            }),
          }}
        >
          rotanamusic.com/careers
        </div>
      </Stack>
    </AbsoluteFill>
  );
};
