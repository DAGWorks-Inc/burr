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
  spawn: 'bg-purple-600'
};

export type ChipType = keyof typeof chipColorMap;
/**
 * Chip component for displaying a label with a background color.
 * This currently centralizes the color mapping for the chips.
 * This makes it easy to centralize meaning across the repository
 * although it breaks encapsulation.
 */
export const Chip = (props: { label: string; chipType: ChipType; className?: string }) => {
  const bgColor = chipColorMap[props.chipType];
  return (
    <div
      className={`relative grid select-none items-center whitespace-nowrap rounded-lg
        p-1 px-3 font-sans text-xs font-semibold text-white ${bgColor} ${
          props.className ? props.className : ''
        }`}
    >
      <span className="">{props.label}</span>
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
