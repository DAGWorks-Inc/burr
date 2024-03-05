import { Span, Step } from '../../../api';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../common/table';
import { DateTimeDisplay, DurationDisplay, TimeDisplay } from '../../common/dates';
import { backgroundColorsForIndex, backgroundColorsForStatus } from './AppView';
import { Status, getActionStatus } from '../../../utils';
import { Chip } from '../../common/chip';
import { useRef, useState } from 'react';
import {
  ArrowPathIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  MinusIcon,
  PlusIcon
} from '@heroicons/react/24/outline';

import { PauseIcon } from '@heroicons/react/24/solid';

import { RiCornerDownRightLine } from 'react-icons/ri';

/**
 * Quick display to suggest that the action is still running
 * This is a placeholder for any columns that have null data
 */
const InProgress = () => {
  return <span></span>;
};

/**
 * Display the runtime of a step.
 * TODO -- display the current one on a ticker if it's still running
 */
const RuntimeDisplay = (props: { start: string; end: string | undefined }) => {
  if (props.end === undefined) {
    return <InProgress />;
  }
  return <DurationDisplay startDate={props.start} endDate={props.end} />;
};
const StatusChip = (props: { status: Status }) => {
  return (
    <Chip
      label={props.status}
      chipType={props.status}
      className="w-16 flex flex-row justify-center"
    />
  );
};

/**
 * Quick auto-refresh switch.
 * TODO -- remove this once we get websockets working.
 */
const AutoRefreshSwitch = (props: {
  autoRefresh: boolean;
  setAutoRefresh: (b: boolean) => void;
}) => {
  const AutoRefreshIcon = props.autoRefresh ? PauseIcon : ArrowPathIcon;
  return (
    <AutoRefreshIcon
      className="h-4 w-4 text-gray-600 hover:scale-110 cursor-pointer"
      onClick={(e) => {
        props.setAutoRefresh(!props.autoRefresh);
        e.stopPropagation();
      }}
    />
  );
};
/**
 * Quick component to make the table row common between
 * the action and span rows
 * @param props
 * @returns
 */
const CommonTableRow = (props: {
  children: React.ReactNode;
  sequenceID: number;
  isHovered: boolean;
  shouldBeHighlighted: boolean;
  currentSelectedIndex: number | undefined;
  step: Step;
  setCurrentHoverIndex: (index?: number) => void;
  setCurrentSelectedIndex: (index?: number) => void;
}) => {
  return (
    <TableRow
      key={props.sequenceID}
      className={`${props.isHovered ? 'opacity-50' : ''} cursor-pointer
            ${
              props.shouldBeHighlighted && props.currentSelectedIndex !== undefined
                ? backgroundColorsForIndex(
                    props.currentSelectedIndex - props.sequenceID,
                    getActionStatus(props.step)
                  )
                : ''
            }`}
      onMouseOver={() => {
        props.setCurrentHoverIndex(props.sequenceID);
      }}
      onClick={() => {
        if (props.currentSelectedIndex == props.sequenceID) {
          props.setCurrentSelectedIndex(undefined);
        } else {
          props.setCurrentSelectedIndex(props.sequenceID);
        }
      }}
    >
      {props.children}
    </TableRow>
  );
};

const ActionTableRow = (props: {
  step: Step;
  currentHoverIndex: number | undefined;
  setCurrentHoverIndex: (index?: number) => void;
  currentSelectedIndex: number | undefined;
  setCurrentSelectedIndex: (index?: number) => void;
  numPriorIndices: number;
  isExpanded: boolean;
  toggleExpanded: (index: number) => void;
  minimized: boolean;
}) => {
  const sequenceID = props.step.step_start_log.sequence_id;
  const isHovered = props.currentHoverIndex === sequenceID;
  const spanCount = props.step.spans.length;
  const shouldBeHighlighted =
    props.currentSelectedIndex !== undefined &&
    sequenceID <= props.currentSelectedIndex &&
    sequenceID >= props.currentSelectedIndex - props.numPriorIndices;
  const ExpandIcon = props.isExpanded ? MinusIcon : PlusIcon;
  return (
    <CommonTableRow
      sequenceID={sequenceID}
      isHovered={isHovered}
      shouldBeHighlighted={shouldBeHighlighted}
      currentSelectedIndex={props.currentSelectedIndex}
      step={props.step}
      setCurrentHoverIndex={props.setCurrentHoverIndex}
      setCurrentSelectedIndex={props.setCurrentSelectedIndex}
    >
      <TableCell className="text-gray-500 w-12 max-w-12 min-w-12">{sequenceID}</TableCell>
      {!props.minimized && (
        <>
          <TableCell className="truncate w-48 min-w-48">
            {props.step.step_start_log.action}
          </TableCell>
          <TableCell>
            <div className="flex flex-row justify-end">
              <DateTimeDisplay date={props.step.step_start_log.start_time} mode={'short'} />
            </div>
          </TableCell>
          <TableCell>
            <RuntimeDisplay
              start={props.step.step_start_log.start_time}
              end={props.step.step_end_log?.end_time}
            />
          </TableCell>
          <TableCell>
            {spanCount > 0 ? (
              <div className="flex gap-1 items-center">
                <ExpandIcon
                  className="h-4 w-4 text-gray-600 hover:scale-110 cursor-pointer"
                  onClick={(e) => {
                    props.toggleExpanded(sequenceID);
                    e.stopPropagation();
                  }}
                />
                <span className="text-gray-600">{spanCount}</span>
              </div>
            ) : (
              <span></span>
            )}
          </TableCell>
          <TableCell>
            <div className="max-w-min">
              <StatusChip status={getActionStatus(props.step)} />
            </div>
          </TableCell>
        </>
      )}
    </CommonTableRow>
  );
};

const TraceSubTable = (props: {
  spans: Span[];
  step: Step;
  currentHoverIndex: number | undefined;
  setCurrentHoverIndex: (index?: number) => void;
  currentSelectedIndex: number | undefined;
  setCurrentSelectedIndex: (index?: number) => void;
  numPriorIndices: number;
  minimized: boolean;
}) => {
  return (
    <>
      {props.spans.map((span) => {
        // This is a quick implementation for prototyping -- we will likely switch this up
        // This assumes that the span UID is of the form "actionID:spanID.spanID.spanID..."
        // Which is currently the case
        const spanIDUniqueToAction = span.begin_entry.span_id.split(':')[1];
        const depth = spanIDUniqueToAction.split('.').length;
        const sequenceID = props.step.step_start_log.sequence_id;
        const isHovered = props.currentHoverIndex === sequenceID;
        const shouldBeHighlighted =
          props.currentSelectedIndex !== undefined &&
          sequenceID <= props.currentSelectedIndex &&
          sequenceID >= props.currentSelectedIndex - props.numPriorIndices;
        console.log(depth, Array(depth));
        const lightText = 'text-gray-300';
        const normalText = shouldBeHighlighted ? 'text-gray-100' : 'text-gray-400';
        return (
          <CommonTableRow
            key={span.begin_entry.span_id}
            sequenceID={sequenceID}
            isHovered={isHovered}
            shouldBeHighlighted={shouldBeHighlighted}
            currentSelectedIndex={props.currentSelectedIndex}
            step={props.step}
            setCurrentHoverIndex={props.setCurrentHoverIndex}
            setCurrentSelectedIndex={props.setCurrentSelectedIndex}
          >
            <TableCell className={` ${lightText} w-10 min-w-10`}>{spanIDUniqueToAction}</TableCell>
            {!props.minimized && (
              <>
                <TableCell className={`${normalText}  w-12 max-w-12 min-w-12`}>
                  <div className="flex flex-row gap-1 items-center min-w-48">
                    {[...Array(depth).keys()].map((i) => (
                      <RiCornerDownRightLine
                        key={i}
                        className={`${i == depth - 1 ? 'opacity-100' : 'opacity-0'} text-lg`}
                      ></RiCornerDownRightLine>
                    ))}
                    {span.begin_entry.span_name}
                  </div>
                </TableCell>
                <TableCell>
                  <div className="flex flex-row justify-end">
                    <TimeDisplay date={props.step.step_start_log.start_time} />
                  </div>
                </TableCell>
                <TableCell colSpan={1}>
                  <RuntimeDisplay
                    start={span.begin_entry.start_time}
                    end={span.end_entry?.end_time}
                  />
                </TableCell>
                <TableCell colSpan={1} className="h-full">
                  <WaterfallPiece
                    step={props.step}
                    span={span}
                    bgColor={backgroundColorsForStatus(getActionStatus(props.step))}
                    isHighlighted={shouldBeHighlighted}
                  />
                </TableCell>
                <TableCell />
              </>
            )}
          </CommonTableRow>
        );
      })}
    </>
  );
};

const WaterfallPiece: React.FC<{
  step: Step;
  span: Span;
  bgColor: string;
  isHighlighted: boolean;
}> = (props) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const totalTimeMilliseconds =
    new Date(props.step.step_end_log?.end_time || new Date()).getTime() -
    new Date(props.step.step_start_log.start_time).getTime();

  const spanStartMilliseconds = new Date(props.span.begin_entry.start_time).getTime();
  const spanEndMilliseconds = new Date(props.span.end_entry?.end_time || new Date()).getTime();
  const bgColor = props.isHighlighted ? 'bg-white' : props.bgColor;
  return (
    <div ref={containerRef} className="w-full h-4 px-3">
      <div
        className={`${bgColor} opacity-50`}
        style={{
          width: `${Math.max(((spanEndMilliseconds - spanStartMilliseconds) / totalTimeMilliseconds) * 100, 1)}%`,
          position: 'relative',
          height: '100%',
          left: `${((spanStartMilliseconds - new Date(props.step.step_start_log.start_time).getTime()) / totalTimeMilliseconds) * 100}%`
        }}
      ></div>
    </div>
  );
};

const ExpandAllButton = (props: { isExpanded: boolean; toggleExpandAll: () => void }) => {
  const ExpandAllIcon = props.isExpanded ? MinusIcon : PlusIcon;
  return (
    <ExpandAllIcon
      className="h-4 w-4 text-gray-600 hover:scale-110 cursor-pointer"
      onClick={(e) => {
        props.toggleExpandAll();
        e.stopPropagation();
      }}
    />
  );
};

/**
 * Table with a list of steps.
 * The indexing is off here -- as it updates the index stays the same.
 * We need to think through the UI a bit, but for now this works cleanly.
 * This also handles setting hover/clicking state through fields/variables
 * passed in.
 *
 * TODO -- add pagination.
 * TODO -- fix up indexing
 */
export const StepList = (props: {
  steps: Step[];
  currentHoverIndex?: number;
  setCurrentHoverIndex: (index?: number) => void;
  currentSelectedIndex?: number;
  setCurrentSelectedIndex: (index?: number) => void;
  numPriorIndices: number;
  autoRefresh: boolean;
  setAutoRefresh: (b: boolean) => void;
  minimized: boolean;
  setMinimized: (b: boolean) => void;
}) => {
  // This is a quick way of expanding the actions all at once
  const [expandedActions, setExpandedActions] = useState<number[]>([]);
  const toggleExpanded = (index: number) => {
    if (expandedActions.includes(index)) {
      setExpandedActions(expandedActions.filter((i) => i !== index));
    } else {
      setExpandedActions([...expandedActions, index]);
    }
  };
  const [intentionExpandAll, setIntentionExpandAll] = useState(false);
  // const ExpandAllIcon = intentionExpandAll ? MinusIcon : PlusIcon;
  const expandAll = () => {
    const allIndices = props.steps.map((step) => step.step_start_log.sequence_id);
    setExpandedActions(allIndices);
  };
  const toggleExpandAll = () => {
    if (intentionExpandAll) {
      setExpandedActions([]);
    } else {
      expandAll();
    }
    setIntentionExpandAll(!intentionExpandAll);
  };
  const isExpanded = (index: number) => {
    return expandedActions.includes(index);
  };
  const MinimizeTableIcon = props.minimized ? ChevronRightIcon : ChevronLeftIcon;
  return (
    <Table dense={2}>
      <TableHead className=" bg-white">
        <TableRow className="">
          <TableHeader className="">
            <div className="py-1 flex flex-row gap-2">
              <MinimizeTableIcon
                className="h-4 w-4 text-gray-600 hover:scale-110 cursor-pointer"
                onClick={(e) => {
                  props.setMinimized(!props.minimized);
                  e.stopPropagation();
                }}
              />
              {props.minimized ? (
                <ExpandAllButton
                  isExpanded={intentionExpandAll}
                  toggleExpandAll={toggleExpandAll}
                />
              ) : (
                <></>
              )}
              {props.minimized ? (
                <AutoRefreshSwitch
                  setAutoRefresh={props.setAutoRefresh}
                  autoRefresh={props.autoRefresh}
                />
              ) : (
                <></>
              )}
            </div>
          </TableHeader>
          {!props.minimized && (
            <>
              <TableHeader>Action</TableHeader>
              <TableHeader>
                <span className="flex justify-end">Ran</span>
              </TableHeader>
              <TableHeader>Duration</TableHeader>
              <TableHeader>
                <div className="flex flex-row items-center gap-2">
                  <ExpandAllButton
                    isExpanded={intentionExpandAll}
                    toggleExpandAll={toggleExpandAll}
                  />
                  Spans
                </div>
              </TableHeader>
              <TableHeader>
                <div className="flex flex-row items-center gap-2">
                  <AutoRefreshSwitch
                    setAutoRefresh={props.setAutoRefresh}
                    autoRefresh={props.autoRefresh}
                  />
                  <span>Tail</span>
                </div>
              </TableHeader>
            </>
          )}
        </TableRow>
      </TableHead>
      {/* <div className="h-10"></div> */}
      <TableBody className="pt-10">
        {props.steps.map((step) => {
          return (
            <>
              <ActionTableRow
                step={step}
                currentHoverIndex={props.currentHoverIndex}
                setCurrentHoverIndex={props.setCurrentHoverIndex}
                currentSelectedIndex={props.currentSelectedIndex}
                setCurrentSelectedIndex={props.setCurrentSelectedIndex}
                numPriorIndices={props.numPriorIndices}
                isExpanded={isExpanded(step.step_start_log.sequence_id)}
                toggleExpanded={toggleExpanded}
                minimized={props.minimized}
              ></ActionTableRow>
              {isExpanded(step.step_start_log.sequence_id) && (
                <TraceSubTable
                  spans={step.spans}
                  step={step}
                  currentHoverIndex={props.currentHoverIndex}
                  setCurrentHoverIndex={props.setCurrentHoverIndex}
                  currentSelectedIndex={props.currentSelectedIndex}
                  setCurrentSelectedIndex={props.setCurrentSelectedIndex}
                  numPriorIndices={props.numPriorIndices}
                  minimized={props.minimized}
                />
              )}
            </>
          );
        })}
      </TableBody>
    </Table>
  );
};
