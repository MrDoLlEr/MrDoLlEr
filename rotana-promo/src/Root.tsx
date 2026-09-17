import React from 'react';
import {Composition} from 'remotion';
import {Promo} from './Promo';
import {LogoStill} from './LogoStill';
import {FPS, DURATION_FRAMES} from './theme';

export const RemotionRoot: React.FC = () => {
  return (
    <>
      {/* LinkedIn feed — 4:5 portrait */}
      <Composition
        id="Promo-LinkedIn-1080x1350"
        component={Promo}
        durationInFrames={DURATION_FRAMES}
        fps={FPS}
        width={1080}
        height={1350}
        defaultProps={{format: 'linkedin' as const}}
      />

      {/* Website hero — 16:9 landscape */}
      <Composition
        id="Promo-Web-1920x1080"
        component={Promo}
        durationInFrames={DURATION_FRAMES}
        fps={FPS}
        width={1920}
        height={1080}
        defaultProps={{format: 'web' as const}}
      />
      {/* Logo alone on transparency, for export into After Effects. */}
      <Composition
        id="LogoStill"
        component={LogoStill}
        durationInFrames={1}
        fps={FPS}
        width={1024}
        height={1024}
      />
    </>
  );
};
