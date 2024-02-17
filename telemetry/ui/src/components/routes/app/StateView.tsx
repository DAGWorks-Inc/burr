import { Step } from '../../../api';
import JsonView from '@uiw/react-json-view';

export const StateView = (props: {
  currentStep: Step | undefined;
  priorStep: Step | undefined;
}) => {
  const stateData = props.currentStep?.step_end_log?.state;
  const resultData = props.currentStep?.step_end_log?.result;

  if (stateData === undefined || resultData === null) {
    return <></>;
  }
  return (
    <div className="h-full overflow-y-scroll pl-3">
      <h1 className="text-lg text-gray-600 font-semibold">State</h1>
      <JsonView value={stateData} collapsed={2} />
      <h1 className="text-lg text-gray-600 font-semibold">Result</h1>
      <JsonView value={resultData} collapsed={2} />
    </div>
  );
};
