import {
  AnnotationOut,
  AttributeModel,
  ChildApplicationModel,
  EndStreamModel,
  FirstItemStreamModel,
  InitializeStreamModel,
  PointerModel,
  Span,
  Step
} from '../../../api';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../common/table';
import { DateTimeDisplay, DurationDisplay } from '../../common/dates';
import { AppContext, backgroundColorsForIndex, backgroundColorsForStatus } from './AppView';
import { Status, getActionStatus } from '../../../utils';
import { Chip } from '../../common/chip';
import { useContext, useEffect, useRef, useState } from 'react';
import { TbGrillFork } from 'react-icons/tb';
import {
  FiArrowDown,
  FiArrowUp,
  FiChevronDown,
  FiChevronUp,
  FiClock,
  FiDatabase
} from 'react-icons/fi';

import {
  ChevronLeftIcon,
  ChevronRightIcon,
  MinusIcon,
  PlayIcon,
  PlusIcon
} from '@heroicons/react/24/outline';

import { PauseIcon } from '@heroicons/react/24/solid';
import { TiFlowChildren } from 'react-icons/ti';

import { Link, useNavigate } from 'react-router-dom';
import { AiOutlineFullscreenExit, AiOutlineFullscreen } from 'react-icons/ai';
import { RiCornerDownRightLine } from 'react-icons/ri';

import { RxActivityLog } from 'react-icons/rx';
import { RenderedField } from './DataView';
import { FaPencilAlt } from 'react-icons/fa';
import { AnnotateButton } from './AnnotationsView';

const StatusChip = (props: { status: Status }) => {
  return (
    <Chip
      label={props.status}
      chipType={props.status}
      className="w-16 flex flex-row justify-center"
    />
  );
};

// The threshold between steps for a "Pause"
// E.G. that control flow moves out of Burr for a bit
// Really we should be recording this using the client, but this is fine for now
const PAUSE_TIME_THRESHOLD_MILLIS = 1_000;

/**
 * Quick auto-refresh switch.
 * TODO -- remove this once we get websockets working.
 */
const AutoRefreshSwitch = (props: {
  autoRefresh: boolean;
  setAutoRefresh: (b: boolean) => void;
  textColor?: string;
}) => {
  const AutoRefreshIcon = props.autoRefresh ? PauseIcon : PlayIcon;
  const textColor = props.textColor || 'text-gray-600';

  return (
    <AutoRefreshIcon
      className={`h-4 w-4 ${textColor} hover:scale-110 cursor-pointer`}
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
      className={`h-full ${props.isHovered ? 'opacity-80' : ''} cursor-pointer
            ${
              props.shouldBeHighlighted && props.currentSelectedIndex !== undefined
                ? backgroundColorsForIndex(
                    props.currentSelectedIndex - props.sequenceID,
                    getActionStatus(props.step)
                  )
                : ''
            }`}
      onMouseEnter={() => {
        props.setCurrentHoverIndex(props.sequenceID);
      }}
      onMouseLeave={() => {
        props.setCurrentHoverIndex(undefined);
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
  step: StepWithEllapsedTime;
  numPriorIndices: number;
  isTracesExpanded: boolean;
  toggleTraceExpanded: (index: number) => void;
  isLinksExpanded: boolean;
  toggleLinksExpanded: (index: number) => void;
  minimized: boolean;
  links: ChildApplicationModel[];
  displaySpansCol: boolean;
  displayLinksCol: boolean;
  earliestTimeSeen: Date;
  latestTimeSeen: Date;
  isExpanded: boolean;
  allowExpand: boolean;
  setExpanded: (b: boolean) => void;
  expandNonSpanAttributes: boolean;
  setExpandNonSpanAttributes: (b: boolean) => void;
  streamingEvents: Array<InitializeStreamModel | FirstItemStreamModel | EndStreamModel>;
  displayAnnotations: boolean;
  existingAnnotation: AnnotationOut | undefined;
}) => {
  const sequenceID = props.step.step_start_log.sequence_id;
  const {
    setCurrentEditingAnnotationContext,
    setTab,
    currentHoverIndex,
    setCurrentHoverIndex,
    currentSelectedIndex,
    setCurrentSelectedIndex
  } = useContext(AppContext);

  const isHovered = currentHoverIndex === sequenceID;
  // const spanCount = props.step.spans.length;
  const childCount = props.links.length;
  const shouldBeHighlighted =
    currentSelectedIndex !== undefined &&
    sequenceID <= currentSelectedIndex &&
    sequenceID >= currentSelectedIndex - props.numPriorIndices;
  // const TraceExpandIcon = props.isTracesExpanded ? MinusIcon : PlusIcon;
  const LinkExpandIcon = props.isLinksExpanded ? MinusIcon : PlusIcon;
  const attributes = props.step.attributes || [];
  const allSpansRecorded = props.step.spans.map((span) => span.begin_entry.span_id);
  const nonSpanAttributes = attributes.filter(
    (attr) => !allSpansRecorded.includes(attr.span_id || '')
  );
  const isStreaming = props.step.streaming_events.length > 0;
  return (
    <CommonTableRow
      sequenceID={sequenceID}
      isHovered={isHovered}
      shouldBeHighlighted={shouldBeHighlighted}
      currentSelectedIndex={currentSelectedIndex}
      step={props.step}
      setCurrentHoverIndex={setCurrentHoverIndex}
      setCurrentSelectedIndex={setCurrentSelectedIndex}
    >
      <TableCell className="text-gray-500 w-12 max-w-12 min-w-12">{sequenceID}</TableCell>
      <TableCell>
        <div className="flex flex-row gap-1 items-center">
          <div className={`${props.allowExpand ? '' : 'invisible'}`}>
            <ToggleButton
              isExpanded={props.isExpanded}
              toggle={() => props.setExpanded(!props.isExpanded)}
              disabled={false}
            />
          </div>
          <div
            className={`${props.minimized ? 'w-32' : 'w-72 max-w-72'} flex flex-row justify-start gap-1 items-center`}
          >
            <Chip
              label={isStreaming ? 'stream' : 'action'}
              chipType={isStreaming ? 'stream' : 'action'}
              className="w-16 flex flex-row justify-center"
            />
            {props.step.step_start_log.action}
            {props.isExpanded && nonSpanAttributes.length > 0 ? (
              <ToggleButton
                isExpanded={nonSpanAttributes.length > 0 ? props.expandNonSpanAttributes : true}
                toggle={
                  nonSpanAttributes.length > 0
                    ? () => props.setExpandNonSpanAttributes(!props.expandNonSpanAttributes)
                    : () => {}
                }
                disabled={false}
                IconExpanded={MinusIcon}
                IconCollapsed={FiDatabase}
              />
            ) : (
              <></>
            )}
          </div>
        </div>
      </TableCell>
      {!props.minimized && (
        <>
          <TableCell className="h-[1px] px-0">
            <WaterfallPiece
              step={props.step}
              earliestStartTime={props.earliestTimeSeen}
              latestEndTime={props.latestTimeSeen}
              endTime={
                props.step.step_end_log ? new Date(props.step.step_end_log?.end_time) : undefined
              }
              startTime={new Date(props.step.step_start_log.start_time)}
              bgColor={backgroundColorsForStatus(getActionStatus(props.step))}
              isHighlighted={shouldBeHighlighted}
              isEvent={false}
              globalEllapsedTimeMillis={props.step.latestGlobalEllapsedTime}
            />
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
          <TableCell className="w-16">
            <div className="max-w-min">
              <StatusChip status={getActionStatus(props.step)} />
            </div>
          </TableCell>
          {props.displayAnnotations && (
            <TableCell className="w-10">
              <AnnotateButton
                sequenceID={sequenceID}
                existingAnnotation={props.existingAnnotation}
                setCurrentEditingAnnotationContext={(context) => {
                  setCurrentEditingAnnotationContext(context);
                  setTab('annotations');
                }}
              />
            </TableCell>
          )}
        </>
      )}
    </CommonTableRow>
  );
};

const LinkSubTable = (props: {
  step: StepWithEllapsedTime;
  numPriorIndices: number;
  minimized: boolean;
  links: ChildApplicationModel[];
  projectId: string;
  displaySpansCol: boolean;
  displayLinksCol: boolean;
}) => {
  const { currentHoverIndex, setCurrentHoverIndex, currentSelectedIndex, setCurrentSelectedIndex } =
    useContext(AppContext);
  const sequenceID = props.step.step_start_log.sequence_id;
  const isHovered = currentHoverIndex === sequenceID;
  const shouldBeHighlighted =
    currentSelectedIndex !== undefined &&
    sequenceID <= currentSelectedIndex &&
    sequenceID >= currentSelectedIndex - props.numPriorIndices;
  const normalText = shouldBeHighlighted ? 'text-gray-100' : 'text-gray-600';
  const iconColor = shouldBeHighlighted ? 'text-gray-100' : 'text-gray-400';
  const navigate = useNavigate();
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
            currentSelectedIndex={currentSelectedIndex}
            step={props.step}
            setCurrentHoverIndex={setCurrentHoverIndex}
            setCurrentSelectedIndex={setCurrentSelectedIndex}
          >
            <TableCell colSpan={1}>
              <Icon className={`h-5 w-5 ${iconColor} -ml-1 `} />
            </TableCell>
            <TableCell
              colSpan={3}
              className={` ${normalText} w-48 min-w-48 max-w-48 truncate pl-9`}
            >
              <div
                className="z-50"
                onClick={(e) => {
                  navigate(
                    `/project/${props.projectId}/${subApp.child.partition_key || 'null'}/${subApp.child.app_id}`
                  );
                  e.stopPropagation();
                }}
              >
                <span className="hover:underline">{subApp.child.app_id}</span>
              </div>
            </TableCell>
            {!props.minimized && (
              <TableCell colSpan={1} className="text-gray-500">
                <Chip
                  label={subApp.event_type === 'fork' ? 'forked' : 'spawned'}
                  chipType={subApp.event_type === 'fork' ? 'fork' : 'spawn'}
                  className="w-16 flex flex-row justify-center"
                />
              </TableCell>
            )}
            <TableCell colSpan={1} />
          </CommonTableRow>
        );
      })}
    </>
  );
};

const StepSubTableRow = (props: {
  spanID: string | null; // undefined if it is not associated with a span, E.G a free-standing attribute
  name: string;
  minimized: boolean;
  sequenceID: number;
  isHovered: boolean;
  shouldBeHighlighted: boolean;
  step: StepWithEllapsedTime;
  startTime: Date;
  endTime: Date | undefined;
  model: Span | AttributeModel | InitializeStreamModel | FirstItemStreamModel | EndStreamModel;
  modelType: 'span' | 'attribute' | 'first_item_stream' | 'end_stream';
  earliestTimeSeen: Date;
  latestTimeSeen: Date;
  displayFullAppWaterfall: boolean;
  displaySpanID: boolean;
  setDisplayAttributes?: (b: boolean) => void;
  displayAttributes?: boolean;
  displayAnnotations: boolean;
}) => {
  const {
    setCurrentHoverIndex,
    currentSelectedIndex,
    setCurrentSelectedIndex,
    setTab,
    setAttributesHighlighted
  } = useContext(AppContext);
  const lightText = 'text-gray-300';
  const normalText = props.shouldBeHighlighted ? 'text-gray-100' : 'text-gray-600';
  const attrsForSpan = props.step.attributes.filter((attr) => attr.span_id === props.spanID);
  const spanIDUniqueToAction = props.spanID?.split(':')[1] || '';
  const Icon = props.modelType === 'span' ? RiCornerDownRightLine : RxActivityLog;
  const [displayAttributeValue, setDisplayAttributeValue] = useState(
    props.modelType === 'attribute'
  );
  // This is a quick implementation for prototyping -- we will likely switch this up
  // This assumes that the span UID is of the form "actionID:spanID.spanID.spanID..."
  // Which is currently the case
  let depth = spanIDUniqueToAction.split('.').length;
  if (props.modelType === 'attribute') {
    depth += 1;
  }
  if (props.modelType === 'first_item_stream' || props.modelType === 'end_stream') {
    depth += 1;
  }
  const isEvent = props.modelType !== 'span';
  // const idToDisplay = props.displaySpanID ? spanIDUniqueToAction : '';
  const onClick = () => {
    if (props.modelType !== 'attribute') {
      return;
    }
    setAttributesHighlighted([props.model as AttributeModel]);
    // TODO -- this is not setting in the URL, we need to figure out why
    setTab('data');
  };
  return (
    <CommonTableRow
      sequenceID={props.sequenceID}
      isHovered={props.isHovered}
      shouldBeHighlighted={props.shouldBeHighlighted}
      currentSelectedIndex={currentSelectedIndex}
      step={props.step}
      setCurrentHoverIndex={setCurrentHoverIndex}
      setCurrentSelectedIndex={setCurrentSelectedIndex}
    >
      <TableCell
        className={` ${lightText} w-10 min-w-10 ${props.displaySpanID ? '' : 'text-opacity-0'}`}
      >
        {spanIDUniqueToAction}
      </TableCell>
      {!props.minimized ? (
        <>
          <TableCell
            onClick={onClick}
            className={`${normalText} ${props.minimized ? 'w-32 min-w-32' : 'w-72 max-w-72'} flex flex-col`}
          >
            <div className="flex flex-row gap-1 items-center">
              {[...Array(depth).keys()].map((i) => (
                <Icon
                  key={i}
                  className={`${i === depth - 1 ? 'opacity-0' : 'opacity-0'} text-lg text-gray-600 w-4 flex-shrink-0`}
                ></Icon>
              ))}
              <Chip
                label={
                  props.modelType === 'end_stream'
                    ? 'end'
                    : props.modelType === 'first_item_stream'
                      ? 'start'
                      : props.modelType
                }
                chipType={props.modelType}
                className="w-16 min-w-16 justify-center"
              />
              {props.modelType === 'attribute' ? (
                <ToggleButton
                  isExpanded={displayAttributeValue}
                  toggle={() => setDisplayAttributeValue(!displayAttributeValue)}
                  disabled={false}
                  IconExpanded={FiChevronUp}
                  IconCollapsed={FiChevronDown}
                />
              ) : (
                <></>
              )}
              <span>{props.name}</span>
              {props.setDisplayAttributes && attrsForSpan.length > 0 ? (
                <ToggleButton
                  isExpanded={props.displayAttributes || false}
                  toggle={() => props.setDisplayAttributes?.(!props.displayAttributes)}
                  disabled={false}
                  IconExpanded={MinusIcon}
                  IconCollapsed={FiDatabase}
                />
              ) : (
                <></>
              )}
            </div>
          </TableCell>
          <TableCell className="h-[1px] pl-0">
            {!displayAttributeValue ? (
              <WaterfallPiece
                step={props.step}
                earliestStartTime={props.earliestTimeSeen}
                latestEndTime={props.latestTimeSeen}
                endTime={props.endTime}
                startTime={props.startTime}
                bgColor={backgroundColorsForStatus(getActionStatus(props.step))}
                isHighlighted={props.shouldBeHighlighted}
                isEvent={isEvent}
                globalEllapsedTimeMillis={props.step.latestGlobalEllapsedTime}
              />
            ) : (
              <div
                className="flex justify-start overflow-hidden pl-20"
                onClick={(e) => {
                  e.stopPropagation();
                }}
              >
                <RenderedField
                  value={(props.model as AttributeModel).value}
                  defaultExpanded={true} // no real need for default expanded
                />
              </div>
            )}
          </TableCell>
          <TableCell className="" />
          {props.displayAnnotations && <TableCell className="" />}
        </>
      ) : (
        <TableCell colSpan={5}></TableCell>
      )}
    </CommonTableRow>
  );
};

const StepSubTable = (props: {
  spans: Span[];
  attributes: AttributeModel[];
  streamingEvents: Array<InitializeStreamModel | FirstItemStreamModel | EndStreamModel>;
  step: StepWithEllapsedTime;
  numPriorIndices: number;
  minimized: boolean;
  displaySpansCol: boolean;
  displayLinksCol: boolean;
  earliestTimeSeen: Date;
  latestTimeSeen: Date;
  expandNonSpanAttributes: boolean;
  topToBottomChronological: boolean;
  displayAnnotations: boolean;
}) => {
  const { currentHoverIndex, currentSelectedIndex } = useContext(AppContext);
  const attributesBySpanID = props.attributes.reduce((acc, attr) => {
    const existing = acc.get(attr.span_id) || [];
    existing.push(attr);
    acc.set(attr.span_id, existing);
    return acc;
  }, new Map<string | null, AttributeModel[]>());
  // TODO -- display
  // const streamingEventsBySpanID = props.streamingEvents.reduce((acc, event) => {
  //   const existing = acc.get(event.span_id) || [];
  //   existing.push(event);
  //   acc.set(event.span_id, existing);
  //   return acc;
  // }, new Map<string | null, Array<InitializeStreamModel | FirstItemStreamModel | EndStreamModel>>());
  const sequenceID = props.step.step_start_log.sequence_id;
  const isHovered = currentHoverIndex === sequenceID;
  const shouldBeHighlighted =
    currentSelectedIndex !== undefined &&
    sequenceID <= currentSelectedIndex &&
    sequenceID >= currentSelectedIndex - props.numPriorIndices;
  const displayFullAppWaterfall = true; // TODO -- configure if we zoom on a step
  const allSpanIds = props.spans.map((span) => span.begin_entry.span_id);
  const [spanIdsWithAttributesDisplayed, setSpanIdsWithAttributesDisplayed] = useState<string[]>(
    []
  );
  // N^2
  // This is because we create span references without logging them -- using the trace at the root level
  // E.G. 15:0 -- this is just the root. No need to display it, we'll just show it on the action
  const attributesNoSpanInfo = props.attributes.filter(
    (attr) => !allSpanIds.includes(attr.span_id || '')
  );
  const nonSpanAttributes = attributesBySpanID.get(null) || [];
  const stepStartTime = new Date(props.step.step_start_log.start_time);
  nonSpanAttributes.sort((a, b) => {
    return (
      (new Date(a.time_logged || stepStartTime) > new Date(b.time_logged || stepStartTime)
        ? 1
        : -1) * (props.topToBottomChronological ? -1 : 1)
    );
  });
  const spans = [...props.spans];
  spans.sort((a, b) => {
    if (a.begin_entry.span_id > b.begin_entry.span_id) {
      return 1;
    }
    return -1;
  });

  const seenNonSpanAttributes = new Set<string | null>();

  const firstStream = props.streamingEvents.find((event) => event.type === 'first_item_stream') as
    | FirstItemStreamModel
    | undefined;

  const streamingEventsToRender = props.streamingEvents.filter(
    (item) => item.type === 'first_item_stream' || item.type === 'end_stream'
  );
  streamingEventsToRender.sort((a, b) => {
    return (
      (new Date((a as FirstItemStreamModel).first_item_time) >
      new Date((b as FirstItemStreamModel).first_item_time)
        ? 1
        : -1) * (props.topToBottomChronological ? -1 : 1)
    );
  });

  return (
    <>
      {streamingEventsToRender.map((event, i) => {
        if (event.type === 'first_item_stream') {
          const streamModel = event as FirstItemStreamModel;
          const ttfs =
            new Date(streamModel.first_item_time).getTime() -
            new Date(props.step.step_start_log.start_time).getTime();
          return (
            <StepSubTableRow
              key={`streaming-${i}`}
              spanID={null}
              name={`delay: ${ttfs}ms`}
              minimized={props.minimized}
              sequenceID={sequenceID}
              isHovered={isHovered}
              shouldBeHighlighted={shouldBeHighlighted}
              step={props.step}
              startTime={new Date(streamModel.first_item_time)}
              endTime={new Date(streamModel.first_item_time)}
              model={streamModel}
              modelType={event.type}
              earliestTimeSeen={props.earliestTimeSeen}
              latestTimeSeen={props.latestTimeSeen}
              displayFullAppWaterfall={displayFullAppWaterfall}
              displaySpanID={true}
              displayAnnotations={props.displayAnnotations}
            />
          );
        } else {
          const streamModel = event as EndStreamModel;
          const ellapsedStreamTime = firstStream
            ? new Date(streamModel.end_time).getTime() -
              new Date(firstStream?.first_item_time).getTime()
            : undefined;
          const numStreamed = streamModel.items_streamed;
          // const name = ellapsedStreamTime ? `last token (throughput=${ellapsedStreamTime/streamModel.items_streamed} ms/token)` : 'last token';
          // const name = `throughput: ${(ellapsedStreamTime || 0) / numStreamed} ms/token (${numStreamed} tokens/${ellapsedStreamTime}ms)`;
          const name = `throughput: ${((ellapsedStreamTime || 0) / numStreamed).toFixed(1)} ms/token (${numStreamed}/${ellapsedStreamTime}ms)`;
          return (
            <StepSubTableRow
              key={`streaming-${i}`}
              spanID={null}
              name={name}
              minimized={props.minimized}
              sequenceID={sequenceID}
              isHovered={isHovered}
              shouldBeHighlighted={shouldBeHighlighted}
              step={props.step}
              startTime={new Date(streamModel.end_time)}
              endTime={new Date(streamModel.end_time)}
              model={streamModel}
              modelType={'end_stream'}
              earliestTimeSeen={props.earliestTimeSeen}
              latestTimeSeen={props.latestTimeSeen}
              displayFullAppWaterfall={displayFullAppWaterfall}
              displaySpanID={true}
              displayAnnotations={props.displayAnnotations}
            />
          );
        }
      })}
      {props.expandNonSpanAttributes ? (
        attributesNoSpanInfo.map((attr, i) => {
          const displaySpanID = !seenNonSpanAttributes.has(attr.span_id) && attr.span_id !== null;
          seenNonSpanAttributes.add(attr.span_id);
          return (
            <StepSubTableRow
              key={`${attr.key}-${i}`}
              spanID={attr.span_id}
              name={attr.key}
              minimized={props.minimized}
              sequenceID={sequenceID}
              isHovered={isHovered}
              shouldBeHighlighted={shouldBeHighlighted}
              step={props.step}
              startTime={new Date(attr.time_logged || stepStartTime)}
              endTime={new Date(attr.time_logged || stepStartTime)}
              model={attr}
              modelType="attribute"
              earliestTimeSeen={props.earliestTimeSeen}
              latestTimeSeen={props.latestTimeSeen}
              displayFullAppWaterfall={displayFullAppWaterfall}
              displaySpanID={displaySpanID}
              displayAnnotations={props.displayAnnotations}
            />
          );
        })
      ) : (
        <></>
      )}
      {spans.flatMap((span, i) => {
        const spanID = span.begin_entry.span_id;
        // if (!openSpanIDs.includes(spanID)) {
        //   return [];
        // }
        // TODO -- add null
        const hasAttributes = attributesBySpanID.has(spanID);
        const attributesToDisplay =
          hasAttributes && spanIdsWithAttributesDisplayed.includes(spanID)
            ? attributesBySpanID.get(spanID) || []
            : [];

        return [
          <StepSubTableRow
            key={i}
            spanID={spanID}
            name={span.begin_entry.span_name}
            minimized={props.minimized}
            sequenceID={sequenceID}
            isHovered={isHovered}
            shouldBeHighlighted={shouldBeHighlighted}
            step={props.step}
            startTime={new Date(span.begin_entry.start_time)}
            endTime={span.end_entry?.end_time ? new Date(span.end_entry.end_time) : undefined}
            model={span}
            modelType="span"
            earliestTimeSeen={props.earliestTimeSeen}
            latestTimeSeen={props.latestTimeSeen}
            displayFullAppWaterfall={displayFullAppWaterfall}
            displaySpanID={true}
            setDisplayAttributes={(b) => {
              if (b) {
                setSpanIdsWithAttributesDisplayed([...spanIdsWithAttributesDisplayed, spanID]);
              } else {
                setSpanIdsWithAttributesDisplayed(
                  spanIdsWithAttributesDisplayed.filter((id) => id !== spanID)
                );
              }
            }}
            displayAttributes={spanIdsWithAttributesDisplayed.includes(spanID)}
            displayAnnotations={props.displayAnnotations}
          />,
          ...attributesToDisplay.map((attr, i) => {
            return (
              <StepSubTableRow
                key={`${attr.key}-${i}`}
                spanID={attr.span_id}
                name={attr.key}
                minimized={props.minimized}
                sequenceID={sequenceID}
                isHovered={isHovered}
                shouldBeHighlighted={shouldBeHighlighted}
                step={props.step}
                startTime={new Date(attr.time_logged || new Date(span.begin_entry.start_time))}
                endTime={new Date(attr.time_logged || new Date(span.begin_entry.start_time))}
                model={attr}
                modelType="attribute"
                earliestTimeSeen={props.earliestTimeSeen}
                latestTimeSeen={props.latestTimeSeen}
                displayFullAppWaterfall={displayFullAppWaterfall}
                displaySpanID={false}
                displayAnnotations={props.displayAnnotations}
              />
            );
          })
        ];
      })}
    </>
  );
};

const WaterfallPiece: React.FC<{
  step: StepWithEllapsedTime;
  startTime: Date;
  endTime: Date | undefined;
  earliestStartTime: Date;
  latestEndTime: Date | undefined;
  globalEllapsedTimeMillis: number; // Total time of active trace
  bgColor: string;
  isHighlighted: boolean;
  isEvent: boolean;
  // Whether to display just ellapsed (clock) time
  displayAbsoluteOrEllapsedTime?: 'absolute' | 'ellapsed';
}> = (props) => {
  const useAbsoluteTime = (props.displayAbsoluteOrEllapsedTime || 'ellapsed') === 'absolute';
  const containerRef = useRef<HTMLDivElement>(null);

  const stepStartTimeAbsolute = new Date(props.step.step_start_log.start_time).getTime();
  // Subtract the duration of the step to get the start time
  const stepStartTimeRelative = props.step.cumulativeTimeMillis - props.step.stepDurationMillis;
  const eventStartTimeSinceStepBegan = props.startTime.getTime() - stepStartTimeAbsolute;
  const eventEndTimeSinceStepBegan =
    (props.endTime || new Date()).getTime() - stepStartTimeAbsolute;

  const earliestStartTimeMilliseconds = useAbsoluteTime ? props.earliestStartTime.getTime() : 0;

  const latestEndTimeMilliseconds = useAbsoluteTime
    ? (props.latestEndTime || new Date()).getTime()
    : props.globalEllapsedTimeMillis;

  const stepBeganReferencePoint = useAbsoluteTime ? stepStartTimeAbsolute : stepStartTimeRelative;

  const startTimeMilliseconds = stepBeganReferencePoint + eventStartTimeSinceStepBegan;
  const endTimeMilliseconds = stepBeganReferencePoint + eventEndTimeSinceStepBegan;
  const earliestToLatestMilliseconds = latestEndTimeMilliseconds - earliestStartTimeMilliseconds;

  const bgColor = props.isHighlighted ? 'bg-white' : props.bgColor;
  const [isHovered, setIsHovered] = useState(false);
  return (
    <div ref={containerRef} className="w-full px-2 h-full">
      {(() => {
        const leftPositionPercentage =
          ((startTimeMilliseconds - earliestStartTimeMilliseconds) / earliestToLatestMilliseconds) *
          100;
        const widthPercentage =
          Math.max(
            Math.max(
              (endTimeMilliseconds - startTimeMilliseconds) / earliestToLatestMilliseconds,
              0.005
            )
            // 0.1
          ) * 100;
        const isCloseToEnd = leftPositionPercentage + widthPercentage > 80; // Threshold for "close to the end"
        // TODO -- unhack these, we're converting back and forth cause we already have interfaces for strings and
        // don't want to change
        const hoverItem = props.isEvent ? (
          <></>
        ) : (
          <div className="flex flex-row gap-1 items-center">
            <DurationDisplay
              startDate={new Date(startTimeMilliseconds).toISOString()}
              endDate={new Date(endTimeMilliseconds).toISOString()}
            />
            <DateTimeDisplay
              date={props.startTime.toISOString()}
              mode={'short'}
              displayMillis={true}
            />
          </div>
        );

        return (
          <>
            {!props.isEvent ? (
              <div
                className={`${bgColor} opacity-50 h-12 px-0 rounded-sm`}
                onMouseEnter={() => setIsHovered(true)}
                onMouseLeave={() => setIsHovered(false)}
                style={{
                  width: `${widthPercentage}%`,
                  position: 'absolute',
                  bottom: '5%',
                  height: '90%',
                  left: `${leftPositionPercentage}%`
                }}
              ></div>
            ) : (
              <div
                className={`h-5 w-5 ${bgColor} opacity-50 absolute`}
                style={{
                  left: `${leftPositionPercentage}%`,
                  top: '50%',
                  transform: 'translate(-50%, -50%) rotate(45deg)'
                }}
              />
            )}

            {/* Hoverable zone with buffer to avoid flicker */}
            <div
              className="absolute h-full"
              onMouseEnter={() => setIsHovered(true)}
              onMouseLeave={() => setIsHovered(false)}
              style={{
                left: `calc(${leftPositionPercentage}% - 20px)`,
                width: `calc(${widthPercentage}% + 40px)` // 20px buffer on each side
              }}
            ></div>

            {
              <div
                className={`backdrop-blur-lg rounded-md px-4 transition-opacity duration-500 ${
                  isHovered ? 'opacity-100' : 'opacity-0 pointer-events-none'
                }`}
                style={{
                  position: 'absolute',
                  top: 5,
                  right: isCloseToEnd ? `calc(100% - ${leftPositionPercentage}%)` : `auto`,
                  left: isCloseToEnd
                    ? `auto`
                    : `calc(${leftPositionPercentage}% + ${widthPercentage}%)`
                }}
              >
                {hoverItem}
              </div>
            }
          </>
        );
      })()}
    </div>
  );
};

const ToggleButton = (props: {
  isExpanded: boolean;
  toggle: () => void;
  disabled: boolean;
  IconExpanded?: React.FC;
  IconCollapsed?: React.FC;
}) => {
  const IconExpanded = props.IconExpanded || MinusIcon;
  const IconCollapsed = props.IconCollapsed || PlusIcon;
  const ToggleIcon = props.isExpanded ? IconExpanded : IconCollapsed;
  const textColor = props.disabled ? 'text-gray-300' : 'text-gray-600';
  const hoverScale = props.disabled ? '' : 'hover:scale-110 cursor-pointer';
  return (
    <ToggleIcon
      className={`h-4 w-4 min-w-4 cursor-pointer ${textColor} ${hoverScale}`}
      onClick={(e) => {
        if (!props.disabled) {
          props.toggle();
        }
        e.stopPropagation();
        e.preventDefault();
      }}
    />
  );
};

type StepWithEllapsedTime = Step & {
  cumulativeTimeMillis: number;
  stepDurationMillis: number;
  pauseAfterLastStepMillis: number;
  latestGlobalEllapsedTime: number;
};

/**
 * Quick function to collapse to ellapsed time
 * Note this may break if steps are not in a perfectly linear order.
 * This is not the case now, but as we add parallelism it very well may be.
 * @param steps
 * @returns
 */
const collapseTimestampsToEllapsedTime = (steps: Step[]): StepWithEllapsedTime[] => {
  const sortedSteps = steps.sort((a, b) => {
    return new Date(a.step_start_log.start_time) > new Date(b.step_start_log.start_time) ? 1 : -1;
  });
  if (sortedSteps.length === 0) {
    return [];
  }
  let lastTime = new Date(sortedSteps[0].step_start_log.start_time);
  let cumulativeTimeMillis = 0;
  return sortedSteps
    .map((step) => {
      const stepStartTime = new Date(step.step_start_log.start_time);
      const stepEndTime = new Date(step.step_end_log?.end_time || new Date());
      const pauseAfterLastStepMillis = stepStartTime.getTime() - lastTime.getTime();
      cumulativeTimeMillis += stepEndTime.getTime() - stepStartTime.getTime();
      lastTime = stepEndTime;
      return {
        ...step,
        cumulativeTimeMillis,
        pauseAfterLastStepMillis: pauseAfterLastStepMillis,
        stepDurationMillis: stepEndTime.getTime() - stepStartTime.getTime(),
        latestGlobalEllapsedTime: 0
      };
    })
    .map((step) => {
      return {
        ...step,
        latestGlobalEllapsedTime: cumulativeTimeMillis
      };
    });
};

const PauseRow = (props: { pauseMillis: number }) => {
  return (
    <TableRow className=" bg-gray-50 text-sm text-gray-300">
      <TableCell colSpan={1}>
        <FiClock className="w-5 h-t" />
        {/* <span className="text-gray-500">pause</span> */}
      </TableCell>
      <TableCell colSpan={1}>
        <DurationDisplay startDate={0} endDate={props.pauseMillis} />
      </TableCell>
      <TableCell colSpan={5}></TableCell>
    </TableRow>
  );
};

const ActionSubTable = (props: {
  step: StepWithEllapsedTime;
  numPriorIndices: number;
  isTraceExpanded: boolean;
  toggleTraceExpandedActions: (index: number) => void;
  isLinksExpanded: boolean;
  toggleLinksExpanded: (index: number) => void;
  minimized: boolean;
  links: ChildApplicationModel[];
  displaySpansCol: boolean;
  displayLinksCol: boolean;
  earliestTimeSeen: Date;
  latestTimeSeen: Date;
  setTraceExpanded: (b: boolean) => void;
  projectId: string;
  pauseLocation?: 'top' | 'bottom'; // If it's top then we put one above, if it's bottom then below, otherwise no pause
  pauseTime?: number;
  topToBottomChronological: boolean;
  displayAnnotations: boolean;
  annotationsForStep: AnnotationOut[];
}) => {
  const {
    step,
    latestTimeSeen,
    isTraceExpanded,
    toggleTraceExpandedActions,
    isLinksExpanded,
    toggleLinksExpanded,
    links,
    displaySpansCol,
    displayLinksCol,
    earliestTimeSeen,
    setTraceExpanded,
    pauseTime,
    topToBottomChronological
  } = props;
  const [expandNonSpanAttributes, setExpandNonSpanAttributes] = useState<boolean>(false); // attributes that are associated with the action, not the span...
  // TODO -- lower a lot of this state into this component
  // This was pulled out quickly and we need to put anyting that's not read above into this
  return (
    <>
      {props.pauseLocation === 'top' && pauseTime !== undefined && (
        <PauseRow pauseMillis={pauseTime} />
      )}
      <ActionTableRow
        key={`${step.step_start_log.sequence_id}-action-table-row`}
        step={step}
        numPriorIndices={props.numPriorIndices}
        isTracesExpanded={isTraceExpanded}
        isLinksExpanded={isLinksExpanded}
        toggleTraceExpanded={toggleTraceExpandedActions}
        toggleLinksExpanded={toggleLinksExpanded}
        minimized={props.minimized}
        links={links}
        displaySpansCol={displaySpansCol}
        displayLinksCol={displayLinksCol}
        earliestTimeSeen={earliestTimeSeen}
        isExpanded={isTraceExpanded}
        setExpanded={setTraceExpanded}
        allowExpand={
          step.spans.length > 0 || step.streaming_events.length > 0 || step.attributes.length > 0
        }
        latestTimeSeen={latestTimeSeen}
        expandNonSpanAttributes={expandNonSpanAttributes}
        setExpandNonSpanAttributes={setExpandNonSpanAttributes}
        streamingEvents={step.streaming_events}
        displayAnnotations={props.displayAnnotations}
        existingAnnotation={props.annotationsForStep.find(
          (annotation) =>
            annotation.step_sequence_id === step.step_start_log.sequence_id &&
            annotation.span_id === null
        )}
      />
      {isTraceExpanded && (
        <StepSubTable
          spans={step.spans}
          attributes={step.attributes}
          step={step}
          numPriorIndices={props.numPriorIndices}
          minimized={props.minimized}
          displaySpansCol={displaySpansCol}
          displayLinksCol={displayLinksCol}
          earliestTimeSeen={earliestTimeSeen}
          latestTimeSeen={latestTimeSeen}
          expandNonSpanAttributes={expandNonSpanAttributes}
          streamingEvents={step.streaming_events}
          topToBottomChronological={topToBottomChronological}
          displayAnnotations={props.displayAnnotations}
          // forceCollapsed={!intentionExpandAll}
        />
      )}
      {isLinksExpanded && (
        <LinkSubTable
          step={step}
          links={links}
          numPriorIndices={props.numPriorIndices}
          minimized={props.minimized}
          projectId={props.projectId}
          displaySpansCol={displaySpansCol}
          displayLinksCol={displayLinksCol}
        />
      )}
      {props.pauseLocation === 'bottom' && pauseTime !== undefined && (
        <PauseRow pauseMillis={pauseTime} />
      )}
    </>
  );
};

// const TableWithRef = forwardRef<HTMLDivElement, React.ComponentProps<typeof Table>>(
//   (props, ref) => {
//     return <Table {...props} ref={ref as React.Ref<HTMLDivElement>} />;
//   }
// );

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
  annotations: AnnotationOut[];
  numPriorIndices: number;
  autoRefresh: boolean;
  setAutoRefresh: (b: boolean) => void;
  minimized: boolean;
  setMinimized: (b: boolean) => void;
  allowMinimized: boolean;
  projectId: string;
  parentPointer: PointerModel | undefined;
  spawningParentPointer: PointerModel | undefined;
  links: ChildApplicationModel[];
  fullScreen: boolean;
  allowFullScreen: boolean;
  setFullScreen: (b: boolean) => void;
  topToBottomChronological: boolean;
  setTopToBottomChronological: (b: boolean) => void;
  toggleInspectViewOpen: () => void;
  displayAnnotations: boolean;
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
  const stepsWithEllapsedTime = collapseTimestampsToEllapsedTime(props.steps);
  const tableRef = useRef<HTMLTableElement>(null);
  const tableScrollRef = useRef<HTMLDivElement>(null);

  const uniqueStepView = props.steps.flatMap((step) => {
    return [
      step.step_start_log.sequence_id,
      step.step_end_log?.sequence_id || '-',
      ...step.attributes.map((attr) => attr.key || '-'),
      ...step.spans.map((span) => span.begin_entry.span_id || '-')
    ];
  });

  uniqueStepView.sort();
  useEffect(() => {
    if (props.autoRefresh && tableScrollRef.current && props.topToBottomChronological) {
      //TODO -- scroll to the end if we we're on auto-refresh
      tableScrollRef.current.scrollIntoView({ behavior: 'smooth', block: 'end' });
    }
  }, [uniqueStepView.map((i) => i.toString()).join(''), props.autoRefresh]);

  stepsWithEllapsedTime
    .sort((a, b) => {
      const naturalOrder = b.step_start_log.sequence_id - a.step_start_log.sequence_id;
      if (naturalOrder !== 0) {
        return props.topToBottomChronological ? naturalOrder : -naturalOrder;
      }
      return 0;
    })
    .reverse();

  const toggleExpandAllTraces = () => {
    if (intentionExpandAll) {
      setTraceExpandedActions([]);
    } else {
      const allIndices = stepsWithEllapsedTime.map((step) => step.step_start_log.sequence_id);
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
  const earliestTimeSeen =
    stepsWithEllapsedTime.length > 0
      ? new Date(
          Math.min(
            ...stepsWithEllapsedTime.map((step) =>
              new Date(step.step_start_log.start_time).getTime()
            )
          )
        )
      : new Date();

  const endTimes = stepsWithEllapsedTime.map((step) => step.step_end_log?.end_time || new Date());
  const latestTimeSeen =
    endTimes.length > 0
      ? new Date(Math.max(...endTimes.map((date) => new Date(date).getTime())))
      : new Date();
  const MinimizeTableIcon = props.minimized ? ChevronRightIcon : ChevronLeftIcon;
  const FullScreenIcon = props.fullScreen ? AiOutlineFullscreenExit : AiOutlineFullscreen;
  const displaySpansCol = stepsWithEllapsedTime.some(
    (step) => step.spans.length > 0 || step.streaming_events.length > 0
  );
  const displayLinksCol = props.links.length > 0;
  const linksBySequenceID = props.links.reduce((acc, child) => {
    const existing = acc.get(child.sequence_id || -1) || [];
    existing.push(child);
    acc.set(child.sequence_id || -1, existing);
    return acc;
  }, new Map<number, ChildApplicationModel[]>());

  const [tableHeight, setTableHeight] = useState('auto');

  const updateTableHeight = () => {
    if (tableRef.current) {
      const parentElement = tableRef.current.parentElement;
      if (parentElement) {
        const parentHeight = parentElement.clientHeight;
        const tableTop =
          tableRef.current.getBoundingClientRect().top - parentElement.getBoundingClientRect().top;
        const availableHeight = parentHeight - tableTop;
        setTableHeight(`${availableHeight}px`);
      }
    }
  };

  useEffect(() => {
    updateTableHeight(); // Initial calculation on mount
    window.addEventListener('resize', updateTableHeight); // Recalculate on window resize

    // Set up a ResizeObserver to listen to changes in the parent element's size
    const observer = new ResizeObserver(updateTableHeight);
    if (tableRef.current?.parentElement) {
      observer.observe(tableRef.current.parentElement);
    }

    return () => {
      window.removeEventListener('resize', updateTableHeight);
      observer.disconnect(); // Cleanup observer on unmount
    };
  }, []);

  const parentRows = (
    <>
      {props.parentPointer ? (
        <ParentLink
          parentPointer={props.parentPointer}
          projectId={props.projectId}
          type="fork"
          minimized={props.minimized}
        />
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
          minimized={props.minimized}
        />
      ) : (
        <></>
      )}
    </>
  );

  return (
    <div ref={tableRef} style={{ height: tableHeight }}>
      <Table dense={2} style={{ maxHeight: tableHeight }} className="hide-scrollbar">
        <TableHead className=" bg-white sticky top-0 z-50">
          <TableRow className="">
            <TableHeader className="" colSpan={1}>
              <div className="py-1 flex flex-row gap-2 items-center">
                <MinimizeTableIcon
                  className={`h-4 w-4 ${props.fullScreen ? 'text-gray-300' : 'hover:scale-110 cursor-pointer text-gray-600'} ${props.allowMinimized ? '' : 'invisible'}`}
                  onClick={(e) => {
                    props.setMinimized(!props.minimized);
                    e.stopPropagation();
                  }}
                />
                <FullScreenIcon
                  className={`h-4 w-4 text-white hover:scale-125 cursor-pointer bg-dwdarkblue/70 rounded-sm ${!props.allowFullScreen ? 'invisible' : ''}`}
                  onClick={(e) => {
                    props.setFullScreen(!props.fullScreen);
                    props.setMinimized(false);
                    e.stopPropagation();
                  }}
                />
                {props.minimized ? (
                  <ToggleButton
                    disabled={!displaySpansCol}
                    isExpanded={intentionExpandAll}
                    toggle={toggleExpandAllTraces}
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
            <TableHeader className="w-72">
              <div className="flex gap-1 items-center justify-start">
                <ToggleButton
                  disabled={!displaySpansCol}
                  isExpanded={intentionExpandAll}
                  toggle={toggleExpandAllTraces}
                />
                Action
                <ToggleButton
                  disabled={false}
                  isExpanded={props.topToBottomChronological}
                  toggle={() => props.setTopToBottomChronological(!props.topToBottomChronological)}
                  IconCollapsed={FiArrowUp}
                  IconExpanded={FiArrowDown}
                />
              </div>
            </TableHeader>

            {!props.minimized && (
              <>
                {displayLinksCol && (
                  <TableHeader>
                    <div className="flex flex-row items-center gap-2">
                      <ToggleButton
                        disabled={!displaySpansCol}
                        isExpanded={intentionExpandAll}
                        toggle={toggleExpandAllTraces}
                      />
                      Links
                    </div>
                  </TableHeader>
                )}
                <TableHeader></TableHeader>
                <TableHeader className="flex justify-end items-center">
                  <div className="flex flex-row items-center gap-2 bg-dwdarkblue/70 text-white px-1 rounded-md hover:opacity-75">
                    <AutoRefreshSwitch
                      setAutoRefresh={props.setAutoRefresh}
                      autoRefresh={props.autoRefresh}
                      textColor="text-white"
                    />
                    <span className="">Live</span>
                  </div>
                </TableHeader>
                {props.displayAnnotations && (
                  <TableHeader>
                    <FaPencilAlt />
                  </TableHeader>
                )}
              </>
            )}
          </TableRow>
        </TableHead>
        {props.topToBottomChronological ? parentRows : <></>}
        <TableBody className="pt-10">
          {stepsWithEllapsedTime.map((step) => {
            // TODO -- make more efficient with a map
            const annotationsForStep = props.annotations.filter(
              (annotation) => annotation.step_sequence_id === step.step_start_log.sequence_id
            );
            const isTraceExpanded = traceExpandedActions.includes(step.step_start_log.sequence_id);
            const setTraceExpanded = (b: boolean) => {
              if (b) {
                setTraceExpandedActions([...traceExpandedActions, step.step_start_log.sequence_id]);
              } else {
                setTraceExpandedActions(
                  traceExpandedActions.filter((i) => i !== step.step_start_log.sequence_id)
                );
              }
            };
            const isLinksExpanded = linksExpandedActions.includes(step.step_start_log.sequence_id);
            const links = linksBySequenceID.get(step.step_start_log.sequence_id) || [];
            const beforePause = step.pauseAfterLastStepMillis > PAUSE_TIME_THRESHOLD_MILLIS;
            return (
              <ActionSubTable
                key={step.step_start_log.sequence_id}
                step={step}
                numPriorIndices={props.numPriorIndices}
                isTraceExpanded={isTraceExpanded}
                toggleTraceExpandedActions={toggleTraceExpandedActions}
                isLinksExpanded={isLinksExpanded}
                toggleLinksExpanded={toggleLinksExpanded}
                minimized={props.minimized}
                links={links}
                displaySpansCol={displaySpansCol}
                displayLinksCol={displayLinksCol}
                earliestTimeSeen={earliestTimeSeen}
                latestTimeSeen={latestTimeSeen}
                setTraceExpanded={setTraceExpanded}
                projectId={props.projectId}
                pauseLocation={beforePause ? 'bottom' : undefined}
                pauseTime={step.pauseAfterLastStepMillis}
                topToBottomChronological={props.topToBottomChronological}
                displayAnnotations={props.displayAnnotations}
                annotationsForStep={annotationsForStep}
              />
            );
          })}
          {!props.topToBottomChronological ? parentRows : <></>}
        </TableBody>
        <div ref={tableScrollRef}></div>
      </Table>
    </div>
  );
};

const ParentLink = (props: {
  parentPointer: PointerModel;
  projectId: string;
  displayLinksCol?: boolean;
  displaySpansCol?: boolean;
  type: 'spawn' | 'fork';
  minimized: boolean;
}) => {
  const Icon = props.type === 'fork' ? TbGrillFork : TiFlowChildren;
  return (
    <TableRow className="text-gray-500 cursor-pointer bg-gray-100">
      <TableCell colSpan={1} className="items-center justify-center flex max-w-20 -ml-5">
        <Icon className="h-5 w-5 -ml-1" />
      </TableCell>
      <TableCell colSpan={2} className="text-gray-500">
        <div className="flex flex-row gap-1 items-center pl-5">
          <Link
            to={`/project/${props.projectId}/${props.parentPointer.partition_key}/${props.parentPointer.app_id}`}
          >
            <span className="hover:underline">{props.parentPointer.app_id}</span>
          </Link>
          <span>@</span>
          <span>{props.parentPointer.sequence_id}</span>
        </div>
      </TableCell>
      {!props.minimized && (
        <>
          <TableCell colSpan={1} className="text-gray-500">
            <Chip
              label={'parent'}
              chipType={props.type}
              className="w-16 flex flex-row justify-center"
            />
          </TableCell>
          <TableCell colSpan={1} />
        </>
      )}
    </TableRow>
  );
};
