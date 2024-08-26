import { ApplicationModel, Step } from '../../../api';
import { Tabs } from '../../common/tabs';
import { DataView } from './DataView';
import { ActionView } from './ActionView';
import { GraphView } from './GraphView';
import { InsightsView } from './InsightsView';
import { ReproduceView } from './ReproduceView';
import { useParams } from 'react-router-dom';
import { useContext } from 'react';
import { AppViewHighlightContext } from './AppView';
import { ChevronLeftIcon, ChevronRightIcon } from '@heroicons/react/24/outline';

const NoStepSelected = () => {
  return (
    <div className="flex flex-col items-center justify-center h-full">
      <p className="text-xl text-gray-400">Please select a step from the table on the left</p>
    </div>
  );
};

export const AppStateView = (props: {
  steps: Step[];
  stateMachine: ApplicationModel;
  highlightedActions: Step[] | undefined;
  hoverAction: Step | undefined;
  currentSequenceID: number | undefined;
  displayGraphAsTab: boolean;
  setMinimized: (minimized: boolean) => void;
  isMinimized: boolean;
  allowMinimized: boolean;
}) => {
  const { tab, setTab } = useContext(AppViewHighlightContext);
  const currentStep = props.steps.find(
    (step) => step.step_start_log.sequence_id === props.currentSequenceID
  );
  const priorStep = props.steps.find(
    (step) => step.step_start_log.sequence_id === (props.currentSequenceID || 0) - 1
  );

  const actionModel = props.stateMachine.actions.find(
    (action) => action.name === currentStep?.step_start_log.action
  );
  const { projectId, appId, partitionKey } = useParams();
  const tabs = [
    { id: 'data', displayName: 'Data' },
    { id: 'code', displayName: 'Code' },
    { id: 'reproduce', displayName: 'Reproduce' },
    { id: 'insights', displayName: 'Insights' }
  ];
  if (props.displayGraphAsTab) {
    tabs.push({ id: 'graph', displayName: 'Graph' });
  }
  const MinimizeTableIcon = props.isMinimized ? ChevronLeftIcon : ChevronRightIcon;
  return (
    <>
      <div className="flex flex-row items-center pl-4">
        {props.allowMinimized && (
          <button onClick={() => props.setMinimized(!props.isMinimized)}>
            <MinimizeTableIcon className="h-4 w-4 hover:scale-110 cursor-pointer text-gray-600" />
          </button>
        )}
        <Tabs tabs={tabs} currentTab={tab} setCurrentTab={setTab} />
      </div>
      <div className="px-4 h-full w-full hide-scrollbar overflow-y-auto">
        {tab === 'data' &&
          (currentStep ? (
            <DataView currentStep={currentStep} priorStep={priorStep} />
          ) : (
            <NoStepSelected />
          ))}
        {tab === 'code' &&
          (currentStep ? <ActionView currentAction={actionModel} /> : <NoStepSelected />)}
        {tab === 'graph' && (
          <GraphView
            stateMachine={props.stateMachine}
            currentAction={currentStep}
            highlightedActions={props.highlightedActions}
            hoverAction={props.hoverAction}
          />
        )}
        {tab === 'insights' && <InsightsView steps={props.steps} />}
        {tab === 'reproduce' &&
          (currentStep ? (
            <ReproduceView
              step={currentStep}
              appId={appId as string}
              partitionKey={partitionKey as string}
              projectID={projectId as string}
            />
          ) : (
            <NoStepSelected />
          ))}
      </div>
    </>
  );
};
