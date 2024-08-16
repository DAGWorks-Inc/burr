import { ApplicationModel, Step } from '../../../api';
import { Tabs } from '../../common/tabs';
import { DataView } from './DataView';
import { ActionView } from './ActionView';
import { GraphView } from './GraphView';
import { InsightsView } from './InsightsView';
import { ReproduceView } from './ReproduceView';
import { useParams } from 'react-router-dom';

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
  currentTab: string;
  setCurrentTab: (tab: string) => void;
  displayGraphAsTab: boolean;
}) => {
  const { currentTab, setCurrentTab } = props;
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
  return (
    <>
      <Tabs tabs={tabs} currentTab={currentTab} setCurrentTab={setCurrentTab} />
      <div className="px-4 h-full w-full hide-scrollbar overflow-y-auto">
        {currentTab === 'data' &&
          (currentStep ? (
            <DataView currentStep={currentStep} priorStep={priorStep} />
          ) : (
            <NoStepSelected />
          ))}
        {currentTab === 'code' &&
          (currentStep ? <ActionView currentAction={actionModel} /> : <NoStepSelected />)}
        {currentTab === 'graph' && (
          <GraphView
            stateMachine={props.stateMachine}
            currentAction={currentStep}
            highlightedActions={props.highlightedActions}
            hoverAction={props.hoverAction}
          />
        )}
        {currentTab === 'insights' && <InsightsView steps={props.steps} />}
        {currentTab === 'reproduce' &&
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
