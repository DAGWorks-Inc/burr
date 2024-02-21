import { Step } from '../../../api';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../common/table';
import { DateTimeDisplay, DurationDisplay } from '../../common/dates';
import { backgroundColorsForIndex } from './AppView';
import { Status, getActionStatus } from '../../../utils';
import { Chip } from '../../common/chip';

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
  return (
    <fieldset>
      <div className="space-y-5">
        <div className="relative flex items-start">
          <div className="flex h-6 items-center">
            <input
              id="comments"
              aria-describedby="comments-description"
              name="comments"
              type="checkbox"
              value={props.autoRefresh ? 'on' : 'off'}
              checked={props.autoRefresh}
              onChange={(e) => props.setAutoRefresh(e.target.checked)}
              className="h-4 w-4 rounded border-gray-300 text-dwdarkblue focus:ring-dwdarkblue selected:bg-dwdarkblue"
            />
          </div>
          <div className="ml-3 text-sm leading-6">
            <label htmlFor="comments" className="font-medium text-gray-500">
              Tail
            </label>
          </div>
        </div>
      </div>
    </fieldset>
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
}) => {
  return (
    <Table dense={2}>
      <TableHead>
        <TableRow>
          <TableHeader></TableHeader>
          <TableHeader>Action</TableHeader>
          <TableHeader>Ran</TableHeader>
          <TableHeader>Duration</TableHeader>
          <TableHeader>
            <AutoRefreshSwitch
              setAutoRefresh={props.setAutoRefresh}
              autoRefresh={props.autoRefresh}
            />
          </TableHeader>
        </TableRow>
      </TableHead>
      <TableBody>
        {props.steps.map((step, i) => {
          const isHovered = i === props.currentHoverIndex;
          const shouldBeHighlighted =
            props.currentSelectedIndex !== undefined &&
            i >= props.currentSelectedIndex &&
            i <= props.currentSelectedIndex + props.numPriorIndices;

          return (
            <TableRow
              key={i}
              className={`${isHovered ? 'opacity-50' : ''} cursor-pointer
                ${
                  shouldBeHighlighted && props.currentSelectedIndex !== undefined
                    ? backgroundColorsForIndex(
                        i - props.currentSelectedIndex,
                        getActionStatus(props.steps[i])
                      )
                    : ''
                }`}
              onMouseOver={() => {
                props.setCurrentHoverIndex(i);
              }}
              onClick={() => {
                if (props.currentSelectedIndex == i) {
                  props.setCurrentSelectedIndex(undefined);
                } else {
                  props.setCurrentSelectedIndex(i);
                }
              }}
            >
              <TableCell className="w-5 text-gray-500">{step.step_sequence_id}</TableCell>
              <TableCell className="font-semibold text-gray-600">
                {step.step_start_log.action}
              </TableCell>
              <TableCell>
                <DateTimeDisplay date={step.step_start_log.start_time} mode={'short'} />
              </TableCell>
              <TableCell>
                <RuntimeDisplay
                  start={step.step_start_log.start_time}
                  end={step.step_end_log?.end_time}
                />
              </TableCell>
              <TableCell>
                <div className="max-w-min">
                  <StatusChip status={getActionStatus(step)} />
                </div>
              </TableCell>
            </TableRow>
          );
        })}
      </TableBody>
    </Table>
  );
};
