import React, { ReactNode, useEffect } from 'react';

type TwoPanelLayoutProps = {
  firstItem: ReactNode;
  secondItem: ReactNode;
  mode: 'half' | 'first-minimal' | 'third' | 'expanding-second';
  animateSecondPanel?: boolean;
};
/**
 * A layout component that takes two children and renders them.
 *
 * This is an ugly monolith as we specifically want this to be the same object
 * across react renders (which can be finnicky), as we want the state of the
 * contents to be preserved. This allows you to toglge full screen.
 *
 * TODO -- manage the state of the contents better so we can split this into
 * multiple separate component types.
 *
 */
export const TwoColumnLayout: React.FC<TwoPanelLayoutProps> = ({
  firstItem: firstColumnContent,
  secondItem: secondColumnContent,
  mode,
  animateSecondPanel = false
}) => {
  const [showSecondPanel, setShowSecondPanel] = React.useState(animateSecondPanel);
  useEffect(() => {
    if (mode === 'expanding-second') {
      setShowSecondPanel(animateSecondPanel);
    }
  }, [animateSecondPanel, mode]);
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
  if (mode === 'expanding-second') {
    return (
      <div
        className={`flex h-full w-full transition-all duration-500 ${mode === 'expanding-second' && showSecondPanel ? 'overflow-hidden' : ''}`}
      >
        <div
          className={`h-full ${mode === 'expanding-second' ? 'transition-all duration-500' : ''} ${showSecondPanel ? 'w-1/2' : 'w-full'}`}
        >
          {firstColumnContent}
        </div>
        {mode === 'expanding-second' && (
          <div
            className={`h-full ${showSecondPanel ? 'w-1/2' : 'w-0'} transition-all duration-500 overflow-hidden`}
          >
            {secondColumnContent}
          </div>
        )}
        {mode !== 'expanding-second' && (
          <div className={`w-1/2 h-full ${mode === 'third' ? 'w-2/3' : 'w-1/2'}`}>
            {secondColumnContent}
          </div>
        )}
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
