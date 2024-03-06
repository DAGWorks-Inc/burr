import React, { ReactNode } from 'react';

type TwoColumnLayoutProps = {
  leftColumnContent: ReactNode;
  rightColumnContent: ReactNode;
  mode: 'half' | 'first-minimal';
};
/**
 * A layout component that takes two children and renders them in a 50/50 split.
 */
const TwoColumnLayout: React.FC<TwoColumnLayoutProps> = ({
  leftColumnContent,
  rightColumnContent,
  mode
}) => {
  if (mode === 'first-minimal') {
    return (
      <div className={`flex h-full w-full ${mode === 'first-minimal' ? 'flex flex-1' : ''}`}>
        <div className="h-full">{leftColumnContent}</div>
        <div className="h-full grow">{rightColumnContent}</div>
      </div>
    );
  }

  return (
    <div className={`flex h-full w-full' : ''}`}>
      <div className="w-1/2 h-full">{leftColumnContent}</div>
      <div className="w-1/2 h-full">{rightColumnContent}</div>
    </div>
  );
};

export default TwoColumnLayout;
