import { ApplicationModel, Step } from '../../../api';
import { Tabs } from '../../common/tabs';
import { DataView } from './DataView';
import { ActionView } from './ActionView';
import { GraphView } from './GraphView';

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
  const tabs = [
    { id: 'data', displayName: 'Data' },
    { id: 'action', displayName: 'Action' }
  ];
  if (props.displayGraphAsTab) {
    tabs.push({ id: 'graph', displayName: 'Graph' });
  }
  return (
    <>
      <Tabs tabs={tabs} currentTab={currentTab} setCurrentTab={setCurrentTab} />
      <div className="px-4 h-full w-full hide-scrollbar overflow-y-auto">
        {currentTab === 'data' && currentStep && (
          <DataView currentStep={currentStep} priorStep={priorStep} />
        )}
        {currentTab === 'action' && currentStep && <ActionView currentAction={actionModel} />}
        {currentTab === 'graph' && (
          <GraphView
            stateMachine={props.stateMachine}
            currentAction={currentStep}
            highlightedActions={props.highlightedActions}
            hoverAction={props.hoverAction}
          />
        )}
      </div>
    </>
  );
};
