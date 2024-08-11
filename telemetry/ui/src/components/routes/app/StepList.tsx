import { AttributeModel, ChildApplicationModel, PointerModel, Span, Step } from '../../../api';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../common/table';
import { DateTimeDisplay, DurationDisplay, TimeDisplay } from '../../common/dates';
import {
  AppViewHighlightContext,
  backgroundColorsForIndex,
  backgroundColorsForStatus
} from './AppView';
import { Status, getActionStatus, getUniqueAttributeID } from '../../../utils';
import { Chip } from '../../common/chip';
import { useContext, useRef, useState } from 'react';
import { TbGrillFork } from 'react-icons/tb';
import { FiEye } from 'react-icons/fi';

import {
  ArrowPathIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  MinusIcon,
  PlusIcon
} from '@heroicons/react/24/outline';

import { PauseIcon } from '@heroicons/react/24/solid';
import { TiFlowChildren } from 'react-icons/ti';

import { RiCornerDownRightLine } from 'react-icons/ri';
import { Link } from 'react-router-dom';

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
        if (props.currentSelectedIndex === props.sequenceID) {
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
  isTracesExpanded: boolean;
  toggleTraceExpanded: (index: number) => void;
  isLinksExpanded: boolean;
  toggleLinksExpanded: (index: number) => void;
  minimized: boolean;
  links: ChildApplicationModel[];
  displaySpansCol: boolean;
  displayLinksCol: boolean;
}) => {
  const sequenceID = props.step.step_start_log.sequence_id;
  const isHovered = props.currentHoverIndex === sequenceID;
  const spanCount = props.step.spans.length;
  const childCount = props.links.length;
  const shouldBeHighlighted =
    props.currentSelectedIndex !== undefined &&
    sequenceID <= props.currentSelectedIndex &&
    sequenceID >= props.currentSelectedIndex - props.numPriorIndices;
  const TraceExpandIcon = props.isTracesExpanded ? MinusIcon : PlusIcon;
  const LinkExpandIcon = props.isLinksExpanded ? MinusIcon : PlusIcon;
  const attributes = props.step.attributes || [];
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
      <TableCell className="truncate w-40 min-w-40">{props.step.step_start_log.action}</TableCell>
      {!props.minimized && (
        <>
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
          {props.displaySpansCol && (
            <TableCell>
              {spanCount > 0 ? (
                <div className="flex flex-row justify-between items-center">
                  <div className="flex gap-1 items-center">
                    <TraceExpandIcon
                      className="h-4 w-4 text-gray-600 hover:scale-110 cursor-pointer"
                      onClick={(e) => {
                        props.toggleTraceExpanded(sequenceID);
                        e.stopPropagation();
                      }}
                    />
                    <span className="text-gray-600">{spanCount}</span>
                  </div>
                  {/* {attributes.length > 0 ? <AttributeLink attributes={attributes} /> : <></>} */}
                </div>
              ) : (
                <span></span>
              )}
            </TableCell>
          )}
          <TableCell className="w-5 min-w-5">
            {attributes.length > 0 ? <AttributeLink attributes={attributes} /> : <></>}
          </TableCell>
          {props.displayLinksCol && (
            <TableCell>
              {childCount > 0 ? (
                <div className="flex gap-1 items-center">
                  <LinkExpandIcon
                    className="h-4 w-4 text-gray-600 hover:scale-110 cursor-pointer"
                    onClick={(e) => {
                      props.toggleLinksExpanded(sequenceID);
                      e.stopPropagation();
                    }}
                  />
                  <span className="text-gray-600">{childCount}</span>
                </div>
              ) : (
                <span></span>
              )}
            </TableCell>
          )}
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

const LinkSubTable = (props: {
  step: Step;
  currentHoverIndex: number | undefined;
  setCurrentHoverIndex: (index?: number) => void;
  currentSelectedIndex: number | undefined;
  setCurrentSelectedIndex: (index?: number) => void;
  numPriorIndices: number;
  minimized: boolean;
  links: ChildApplicationModel[];
  projectId: string;
  displaySpansCol: boolean;
  displayLinksCol: boolean;
}) => {
  const sequenceID = props.step.step_start_log.sequence_id;
  const isHovered = props.currentHoverIndex === sequenceID;
  const shouldBeHighlighted =
    props.currentSelectedIndex !== undefined &&
    sequenceID <= props.currentSelectedIndex &&
    sequenceID >= props.currentSelectedIndex - props.numPriorIndices;
  const normalText = shouldBeHighlighted ? 'text-gray-100' : 'text-gray-600';
  const iconColor = shouldBeHighlighted ? 'text-gray-100' : 'text-gray-400';
  return (
    <>
      {props.links.map((subApp) => {
        const childType = subApp.event_type;
        const Icon = childType === 'fork' ? TbGrillFork : TiFlowChildren;
        return (
          <CommonTableRow
            key={`${subApp.child.app_id}-link-table-row`}
            sequenceID={sequenceID}
            isHovered={isHovered}
            shouldBeHighlighted={shouldBeHighlighted}
            currentSelectedIndex={props.currentSelectedIndex}
            step={props.step}
            setCurrentHoverIndex={props.setCurrentHoverIndex}
            setCurrentSelectedIndex={props.setCurrentSelectedIndex}
          >
            <TableCell colSpan={1}>
              <Icon className={`h-5 w-5 ${iconColor} `} />
            </TableCell>
            <TableCell colSpan={1} className={` ${normalText}  w-48 min-w-48 max-w-48 truncate`}>
              <Link to={`/project/${props.projectId}/${subApp.child.app_id}`}>
                <span className="hover:underline">{subApp.child.app_id}</span>
              </Link>
            </TableCell>
            <TableCell colSpan={1} className={` ${normalText} min-w-10`}>
              <div className="flex flex-row justify-end">
                <DateTimeDisplay date={subApp.event_time} mode={'short'} />
              </div>
            </TableCell>
            <TableCell
              colSpan={1 + +!!props.displayLinksCol + +!!props.displaySpansCol}
            ></TableCell>
            <TableCell colSpan={1} className="text-gray-500">
              <Chip
                label={subApp.event_type === 'fork' ? 'forked' : 'spawned'}
                chipType={subApp.event_type === 'fork' ? 'fork' : 'spawn'}
                className="w-16 flex flex-row justify-center"
              />
            </TableCell>
          </CommonTableRow>
        );
      })}
    </>
  );
};

const scrollToAttribute = (attribute: AttributeModel) => {
  const element = document.getElementById(getUniqueAttributeID(attribute));
  if (element) {
    const scroll = () => {
      element.scrollIntoView({ behavior: 'smooth', block: 'start', inline: 'nearest' });
    };
    scroll();
    const observer = new ResizeObserver(() => {
      scroll();
    });
    observer.observe(element);
    setTimeout(() => observer.disconnect(), 1000); // Adjust timeout as needed
  }
};

const AttributeLink = (props: { attributes: AttributeModel[] }) => {
  const { setAttributesHighlighted, setTab } = useContext(AppViewHighlightContext);
  return (
    <FiEye
      className="text-xl cursor-pointer hover:scale-125"
      onClick={() => {
        scrollToAttribute(props.attributes[0]);
        setAttributesHighlighted(props.attributes);
        setTab('data');
      }}
    />
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
  displaySpansCol: boolean;
  displayLinksCol: boolean;
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
        const lightText = 'text-gray-300';
        const normalText = shouldBeHighlighted ? 'text-gray-100' : 'text-gray-400';
        const attrsForSpan = props.step.attributes.filter(
          (attr) => attr.span_id === span.begin_entry.span_id
        );
        return (
          <CommonTableRow
            key={`${span.begin_entry.span_id}-trace-table-row`}
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
                        className={`${i === depth - 1 ? 'opacity-100' : 'opacity-0'} text-lg`}
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
                  <div className="flex flex-row justify-between">
                    <WaterfallPiece
                      step={props.step}
                      span={span}
                      bgColor={backgroundColorsForStatus(getActionStatus(props.step))}
                      isHighlighted={shouldBeHighlighted}
                    />
                  </div>
                </TableCell>
                <TableCell className="w-5 min-w-5">
                  {attrsForSpan.length > 0 ? <AttributeLink attributes={attrsForSpan} /> : <></>}
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
          width: `${Math.min(((spanEndMilliseconds - spanStartMilliseconds) / totalTimeMilliseconds) * 100, 100)}%`,
          position: 'relative',
          height: '100%',
          left: `${((spanStartMilliseconds - new Date(props.step.step_start_log.start_time).getTime()) / totalTimeMilliseconds) * 100}%`
        }}
      ></div>
    </div>
  );
};

const ExpandAllButton = (props: {
  isExpanded: boolean;
  toggleExpandAll: () => void;
  disabled: boolean;
}) => {
  const ExpandAllIcon = props.isExpanded ? MinusIcon : PlusIcon;
  const textColor = props.disabled ? 'text-gray-300' : 'text-gray-600';
  const hoverScale = props.disabled ? '' : 'hover:scale-110 cursor-pointer';
  return (
    <ExpandAllIcon
      className={`h-4 w-4 cursor-pointer ${textColor} ${hoverScale}`}
      onClick={(e) => {
        if (!props.disabled) {
          props.toggleExpandAll();
        }
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
  projectId: string;
  parentPointer: PointerModel | undefined;
  spawningParentPointer: PointerModel | undefined;
  links: ChildApplicationModel[];
}) => {
  // This is a quick way of expanding the actions all at once
  const [traceExpandedActions, setTraceExpandedActions] = useState<number[]>([]);
  const toggleTraceExpandedActions = (index: number) => {
    if (traceExpandedActions.includes(index)) {
      setTraceExpandedActions(traceExpandedActions.filter((i) => i !== index));
    } else {
      setTraceExpandedActions([...traceExpandedActions, index]);
    }
  };
  const [intentionExpandAll, setIntentionExpandAll] = useState(false);

  const [linksExpandedActions, setLinksExpandedActions] = useState<number[]>([]);
  const toggleExpandAllTraces = () => {
    if (intentionExpandAll) {
      setTraceExpandedActions([]);
    } else {
      const allIndices = props.steps.map((step) => step.step_start_log.sequence_id);
      setTraceExpandedActions(allIndices);
    }
    setIntentionExpandAll(!intentionExpandAll);
  };
  const isLinksExpanded = (index: number) => {
    return linksExpandedActions.includes(index);
  };
  const toggleLinksExpanded = (index: number) => {
    if (isLinksExpanded(index)) {
      setLinksExpandedActions(linksExpandedActions.filter((i) => i !== index));
    } else {
      setLinksExpandedActions([...linksExpandedActions, index]);
    }
  };
  const MinimizeTableIcon = props.minimized ? ChevronRightIcon : ChevronLeftIcon;
  const displaySpansCol = props.steps.some((step) => step.spans.length > 0);
  const displayLinksCol = props.links.length > 0;
  const linksBySequenceID = props.links.reduce((acc, child) => {
    const existing = acc.get(child.sequence_id || -1) || [];
    existing.push(child);
    acc.set(child.sequence_id || -1, existing);
    return acc;
  }, new Map<number, ChildApplicationModel[]>());
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
                  disabled={!displaySpansCol}
                  isExpanded={intentionExpandAll}
                  toggleExpandAll={toggleExpandAllTraces}
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
          <TableHeader>Action</TableHeader>

          {!props.minimized && (
            <>
              <TableHeader>
                <span className="flex justify-end">Ran</span>
              </TableHeader>
              <TableHeader>Duration</TableHeader>
              {displaySpansCol && (
                <TableHeader>
                  <div className="flex flex-row items-center gap-2">
                    <ExpandAllButton
                      disabled={!displaySpansCol}
                      isExpanded={intentionExpandAll}
                      toggleExpandAll={toggleExpandAllTraces}
                    />
                    Spans
                  </div>
                </TableHeader>
              )}
              <TableHeader className="w-5"></TableHeader>

              {displayLinksCol && (
                <TableHeader>
                  <div className="flex flex-row items-center gap-2">
                    <ExpandAllButton
                      disabled={!displaySpansCol}
                      isExpanded={intentionExpandAll}
                      toggleExpandAll={toggleExpandAllTraces}
                    />
                    Links
                  </div>
                </TableHeader>
              )}
              <TableHeader>
                <div className="flex flex-row items-center gap-2">
                  <AutoRefreshSwitch
                    setAutoRefresh={props.setAutoRefresh}
                    autoRefresh={props.autoRefresh}
                  />
                  <span>Live</span>
                </div>
              </TableHeader>
            </>
          )}
        </TableRow>
      </TableHead>
      {/* <div className="h-10"></div> */}
      <TableBody className="pt-10">
        {props.steps.map((step) => {
          const isTraceExpanded = traceExpandedActions.includes(step.step_start_log.sequence_id);
          const isLinksExpanded = linksExpandedActions.includes(step.step_start_log.sequence_id);
          const links = linksBySequenceID.get(step.step_start_log.sequence_id) || [];
          return (
            <>
              <ActionTableRow
                key={`${step.step_start_log.sequence_id}-action-table-row`}
                step={step}
                currentHoverIndex={props.currentHoverIndex}
                setCurrentHoverIndex={props.setCurrentHoverIndex}
                currentSelectedIndex={props.currentSelectedIndex}
                setCurrentSelectedIndex={props.setCurrentSelectedIndex}
                numPriorIndices={props.numPriorIndices}
                isTracesExpanded={isTraceExpanded}
                isLinksExpanded={isLinksExpanded}
                toggleTraceExpanded={toggleTraceExpandedActions}
                toggleLinksExpanded={toggleLinksExpanded}
                minimized={props.minimized}
                links={links}
                displaySpansCol={displaySpansCol}
                displayLinksCol={displayLinksCol}
              ></ActionTableRow>
              {isTraceExpanded && (
                <TraceSubTable
                  spans={step.spans}
                  step={step}
                  currentHoverIndex={props.currentHoverIndex}
                  setCurrentHoverIndex={props.setCurrentHoverIndex}
                  currentSelectedIndex={props.currentSelectedIndex}
                  setCurrentSelectedIndex={props.setCurrentSelectedIndex}
                  numPriorIndices={props.numPriorIndices}
                  minimized={props.minimized}
                  displaySpansCol={displaySpansCol}
                  displayLinksCol={displayLinksCol}
                />
              )}
              {isLinksExpanded && (
                <LinkSubTable
                  step={step}
                  links={links}
                  currentHoverIndex={props.currentHoverIndex}
                  setCurrentHoverIndex={props.setCurrentHoverIndex}
                  currentSelectedIndex={props.currentSelectedIndex}
                  setCurrentSelectedIndex={props.setCurrentSelectedIndex}
                  numPriorIndices={props.numPriorIndices}
                  minimized={props.minimized}
                  projectId={props.projectId}
                  displaySpansCol={displaySpansCol}
                  displayLinksCol={displayLinksCol}
                />
              )}
            </>
          );
        })}
        {props.parentPointer ? (
          <ParentLink parentPointer={props.parentPointer} projectId={props.projectId} type="fork" />
        ) : (
          <></>
        )}
        {props.spawningParentPointer ? (
          <ParentLink
            parentPointer={props.spawningParentPointer}
            projectId={props.projectId}
            type="spawn"
            displayLinksCol={displayLinksCol}
            displaySpansCol={displaySpansCol}
          />
        ) : (
          <></>
        )}
      </TableBody>
    </Table>
  );
};

const ParentLink = (props: {
  parentPointer: PointerModel;
  projectId: string;
  displayLinksCol?: boolean;
  displaySpansCol?: boolean;
  type: 'spawn' | 'fork';
}) => {
  const Icon = props.type === 'fork' ? TbGrillFork : TiFlowChildren;
  return (
    <TableRow className="text-gray-500 cursor-pointer bg-gray-100">
      <TableCell colSpan={1} className="items-center justify-center flex max-w-20">
        <Icon className="h-5 w-5 -ml-1.5" />
      </TableCell>
      <TableCell
        colSpan={3 + +!!props.displayLinksCol + +!!props.displaySpansCol}
        className="text-gray-500"
      >
        <div className="flex flex-row gap-1 items-center ">
          <Link to={`/project/${props.projectId}/${props.parentPointer.app_id}`}>
            <span className="hover:underline">{props.parentPointer.app_id}</span>
          </Link>
          <span>@</span>
          <span>{props.parentPointer.sequence_id}</span>
        </div>
      </TableCell>
      <TableCell colSpan={1} className="text-gray-500">
        <Chip
          label={'parent'}
          chipType={props.type}
          className="w-16 flex flex-row justify-center"
        />
      </TableCell>
    </TableRow>
  );
};
