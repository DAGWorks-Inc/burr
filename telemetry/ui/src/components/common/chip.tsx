import { ReactNode } from 'react';

const chipColorMap = {
  stateRead: 'bg-dwdarkblue',
  stateWrite: 'bg-dwred',
  input: 'bg-yellow-500',
  success: 'bg-green-500',
  failure: 'bg-dwred',
  running: 'bg-dwlightblue',
  demo: 'bg-yellow-400',
  test: 'bg-gray-800',
  fork: 'bg-dwdarkblue/80',
  spawn: 'bg-purple-600',
  span: 'bg-yellow-500/80',
  attribute: 'bg-teal-700',
  state: 'bg-dwlightblue',
  error: 'bg-dwred',
  action: 'bg-dwlightblue/90',
  stream: 'bg-dwlightblue/90',
  first_item_stream: 'bg-pink-400',
  end_stream: 'bg-pink-400',
  llm: 'bg-gray-400/50',
  metric: 'bg-gray-400/50',
  tag: 'bg-gray-700/50',
  annotateDataPointerAttribute: 'bg-teal-700', // same as attribute
  annotateDataPointerState: 'bg-dwlightblue'
};

export type ChipType = keyof typeof chipColorMap;

export const Chip = (props: {
  label: string;
  chipType: ChipType;
  className?: string;
  onClick?: (e: React.MouseEvent) => void;
}) => {
  // Function to generate a hash code from a string
  const stringToHash = (str: string) => {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      hash = str.charCodeAt(i) + ((hash << 5) - hash);
      hash |= 0; // Convert to 32bit integer
    }
    return hash;
  };

  // Function to generate a color from a hash
  const hashToColor = (hash: number) => {
    // Generate RGB values between 64 and 192 for more vibrant colors
    const r = 64 + (Math.abs(hash) % 128);
    const g = 64 + (Math.abs(hash >> 8) % 128);
    const b = 64 + (Math.abs(hash >> 16) % 128);

    return `rgb(${r}, ${g}, ${b})`;
  };

  // Generate color if chipType is 'tag'
  const bgStyle = props.chipType === 'tag' ? hashToColor(stringToHash(props.label)) : undefined;
  const bgColor = props.chipType === 'tag' ? '' : chipColorMap[props.chipType];
  const clickable = props.onClick !== undefined;

  return (
    <div
      className={`relative grid select-none items-center whitespace-nowrap rounded-lg
        p-1 px-3 font-sans text-xs font-semibold text-white ${bgColor} ${clickable ? 'cursor-pointer hover:underline' : ''} ${props.className ? props.className : ''}`}
      style={{ backgroundColor: bgStyle }}
      onClick={props.onClick}
    >
      <span>{props.label}</span>
    </div>
  );
};

/**
 * A group of chips -- displays in a row with a "label" (just a react component)
 */
export const ChipGroup = (props: { chips: string[]; type: ChipType; label?: ReactNode }) => {
  return (
    <div className="flex gap-2">
      {props.label ? props.label : <></>}
      {props.chips.map((chip, i) => (
        <Chip key={i} label={chip} chipType={props.type} />
      ))}
    </div>
  );
};
