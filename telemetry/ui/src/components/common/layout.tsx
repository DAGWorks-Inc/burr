import React, { ReactNode } from 'react';

type TwoPanelLayoutProps = {
  firstItem: ReactNode;
  secondItem: ReactNode;
  mode: 'half' | 'first-minimal' | 'third';
};
/**
 * A layout component that takes two children and renders them in a 50/50 split.
 */
export const TwoColumnLayout: React.FC<TwoPanelLayoutProps> = ({
  firstItem: firstColumnContent,
  secondItem: secondColumnContent,
  mode
}) => {
  if (mode === 'first-minimal') {
    return (
      <div className={`flex h-full w-full ${mode === 'first-minimal' ? 'flex flex-1' : ''}`}>
        <div className="h-full">{firstColumnContent}</div>
        <div className="h-full grow">{secondColumnContent}</div>
      </div>
    );
  }
  if (mode === 'third') {
    return (
      <div className={`flex h-full w-full' : ''}`}>
        <div className="w-1/3 h-full">{firstColumnContent}</div>
        <div className="w-2/3 h-full">{secondColumnContent}</div>
      </div>
    );
  }
  return (
    <div className="flex h-full w-full">
      <div className="w-1/2 h-full">{firstColumnContent}</div>
      <div className="w-1/2 h-full">{secondColumnContent}</div>
    </div>
  );
};
export const TwoRowLayout: React.FC<TwoPanelLayoutProps> = ({
  firstItem: topRowContent,
  secondItem: bottomRowContent
}) => {
  return (
    <div className="flex flex-col h-full w-full gap-2">
      <div className="h-1/2 overflow-auto">{topRowContent}</div>
      <div className="h-1/2">{bottomRowContent}</div>
    </div>
  );
};
