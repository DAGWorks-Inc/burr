import React, { ReactNode } from 'react';

type TwoColumnLayoutProps = {
  leftColumnContent: ReactNode;
  rightColumnContent: ReactNode;
};
/**
 * A layout component that takes two children and renders them in a 50/50 split.
 */
const TwoColumnLayout: React.FC<TwoColumnLayoutProps> = ({
  leftColumnContent,
  rightColumnContent
}) => {
  return (
    <div className="flex h-full w-full">
      <div className="w-1/2 h-full hide-scrollbar overflow-y-auto">
        {/* Render left column content */}
        {leftColumnContent}
      </div>
      <div className="w-1/2 h-full  hide-scrollbar overflow-hidden">
        {/* Render right column content */}
        {rightColumnContent}
      </div>
    </div>
  );
};

export default TwoColumnLayout;
