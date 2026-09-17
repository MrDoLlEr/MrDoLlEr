import React from 'react';
import {AbsoluteFill} from 'remotion';
import {Logo} from './Logo';

/** Logo alone on transparency — rendered to PNG for import into After Effects. */
export const LogoStill: React.FC = () => (
  <AbsoluteFill style={{justifyContent: 'center', alignItems: 'center'}}>
    <Logo size={1000} />
  </AbsoluteFill>
);
