import { useState } from 'react';
import { ApplicationModel, Step } from '../../../api';
import { Tabs } from '../../common/tabs';
import { GraphView } from './GraphView';
import { DataView } from './DataView';
import { ActionView } from './ActionView';

export const AppStateView = (props: {
  steps: Step[];
  stateMachine: ApplicationModel;
  highlightedActions: Step[] | undefined;
  hoverAction: Step | undefined;
  currentSequenceID: number | undefined;
}) => {
  const [currentTab, setCurrentTab] = useState('graph');
  const currentStep = props.steps.find(
    (step) => step.step_start_log.sequence_id === props.currentSequenceID
  );
  const priorStep = props.steps.find(
    (step) => step.step_start_log.sequence_id === (props.currentSequenceID || 0) - 1
  );

  const actionModel = props.stateMachine.actions.find(
    (action) => action.name === currentStep?.step_start_log.action
  );
  const tabs = [{ id: 'graph', displayName: 'Graph' }];
  if (currentStep) {
    tabs.push({ id: 'data', displayName: 'Data' });
    tabs.push({ id: 'action', displayName: 'Action' });
  }
  return (
    <>
      <Tabs tabs={tabs} currentTab={currentTab} setCurrentTab={setCurrentTab} />
      <div className="px-4 h-full w-full hide-scrollbar overflow-y-auto">
        {currentTab === 'graph' && (
          <GraphView
            stateMachine={props.stateMachine}
            currentAction={currentStep}
            highlightedActions={props.highlightedActions}
            hoverAction={props.hoverAction}
          />
        )}
        {currentTab === 'data' && <DataView currentStep={currentStep} priorStep={priorStep} />}
        {currentTab === 'action' && <ActionView currentAction={actionModel} />}
      </div>
    </>
  );
};
