import { ReactNode, useState } from 'react';

export const Tooltip: React.FC<{ text: string; children: ReactNode }> = ({ text, children }) => {
  const [isVisible, setIsVisible] = useState(false);
  const [tooltipStyle, setTooltipStyle] = useState<React.CSSProperties>({});

  const handleMouseEnter = (e: React.MouseEvent) => {
    const { clientX, clientY } = e;
    setTooltipStyle({
      left: `${clientX}px`,
      top: `${clientY - 5}px`, // 5px above the cursor
      position: 'absolute'
    });
    setIsVisible(true);
  };

  const handleMouseLeave = () => {
    setIsVisible(false);
  };

  return (
    <div className="relative inline-block">
      <div
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
        className="cursor-pointer"
      >
        {children}
      </div>
      {isVisible && (
        <div className="absolute bg-gray-700 text-white text-sm p-2 rounded" style={tooltipStyle}>
          {text}
        </div>
      )}
    </div>
  );
};

export default Tooltip;
