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
  currentActionIndex: number | undefined;
}) => {
  const [currentTab, setCurrentTab] = useState('graph');
  const currentStep =
    props.currentActionIndex !== undefined ? props.steps[props.currentActionIndex] : undefined;
  const priorStep =
    props.currentActionIndex !== undefined ? props.steps[props.currentActionIndex + 1] : undefined;

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
      <div className="px-10 h-full w-full overflow-y-auto">
        {currentTab === 'graph' && (
          <GraphView
            stateMachine={props.stateMachine}
            currentAction={
              props.currentActionIndex !== undefined
                ? props.steps[props.currentActionIndex]
                : undefined
            }
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
