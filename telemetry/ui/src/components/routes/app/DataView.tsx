import { Step } from '../../../api';
import JsonView from '@uiw/react-json-view';
import { Button } from '../../common/button';
import { useState } from 'react';

const StateButton = (props: { label: string; selected: boolean; setSelected: () => void }) => {
  const color = props.selected ? 'zinc' : 'light';
  return (
    <Button className="w-min cursor-pointer" color={color} onClick={props.setSelected}>
      {props.label}
    </Button>
  );
};

export const ErrorView = (props: { error: string }) => {
  return <pre className="text-dwred rounded-sm p-2  text-wrap text-xs">{props.error}</pre>;
};
export const DataView = (props: { currentStep: Step | undefined; priorStep: Step | undefined }) => {
  const [whichState, setWhichState] = useState<'after' | 'before'>('after');
  const stepToExamine = whichState === 'after' ? props.currentStep : props.priorStep;
  const stateData = stepToExamine?.step_end_log?.state;
  const resultData = stepToExamine?.step_end_log?.result;
  const inputs = stepToExamine?.step_start_log?.inputs;
  const error = props.currentStep?.step_end_log?.exception;

  return (
    <div className="h-full pl-3 pt-2 flex flex-col gap-2">
      <div className="flex flex-row justify-between">
        <h1 className="text-2xl text-gray-600 font-semibold">State</h1>
        <div className="flex flex-row justify-end gap-2 pr-2">
          {stateData !== undefined && (
            <StateButton
              label="after"
              selected={whichState == 'after'}
              setSelected={() => {
                setWhichState('after');
              }}
            />
          )}

          {
            <StateButton
              label="before"
              selected={whichState == 'before'}
              setSelected={() => {
                setWhichState('before');
              }}
            />
          }
        </div>
      </div>

      {stateData !== undefined && (
        <JsonView value={stateData} collapsed={2} enableClipboard={false} />
      )}
      {error && (
        <>
          <h1 className="text-2xl text-gray-600 font-semibold">Error</h1>
          <ErrorView error={error} />
        </>
      )}
      {resultData && (
        <>
          <h1 className="text-2xl text-gray-600 font-semibold">Result</h1>
          <JsonView value={resultData} collapsed={2} enableClipboard={false} />
        </>
      )}
      {Object.keys(inputs || {}).length > 0 && (
        <>
          <h1 className="text-2xl text-gray-600 font-semibold">Inputs</h1>
          <JsonView value={inputs} collapsed={2} enableClipboard={false} />
        </>
      )}
    </div>
  );
};
