import React, { useState } from 'react';
import { Step } from '../../../api';
import JsonView from '@uiw/react-json-view';
import { Button } from '../../common/button';
import { Switch, SwitchField } from '../../common/switch';
import { Label } from '../../common/fieldset';
import { classNames } from '../../../utils/tailwind';
import { ChevronDownIcon, ChevronUpIcon } from '@heroicons/react/20/solid';

const StateButton = (props: { label: string; selected: boolean; setSelected: () => void }) => {
  const color = props.selected ? 'zinc' : 'light';
  return (
    <Button className="w-min cursor-pointer" color={color} onClick={props.setSelected}>
      {props.label}
    </Button>
  );
};

export const ErrorView = (props: { error: string }) => {
  return (
    <>
      <pre className="text-dwred rounded-sm p-2  text-wrap text-xs">{props.error}</pre>
    </>
  );
};
export const DataView = (props: { currentStep: Step | undefined; priorStep: Step | undefined }) => {
  const [whichState, setWhichState] = useState<'after' | 'before'>('after');
  const stepToExamine = whichState === 'after' ? props.currentStep : props.priorStep;
  const stateData = stepToExamine?.step_end_log?.state;
  const resultData = stepToExamine?.step_end_log?.result || undefined;
  const inputs = stepToExamine?.step_start_log?.inputs;
  const error = props.currentStep?.step_end_log?.exception;
  const [viewRawData, setViewRawData] = useState<'raw' | 'render'>('render');

  return (
    <div className="pl-1 flex flex-col gap-2 hide-scrollbar">
      <div className="flex flex-row justify-between sticky top-0 z-20 bg-white">
        <h1 className="text-2xl text-black-1000 font-semibold pt-2">State</h1>
        <div className="flex flex-row justify-end gap-2 pr-2">
          <SwitchField>
            <Switch
              name="test"
              checked={viewRawData === 'raw'}
              onChange={(checked) => {
                setViewRawData(checked ? 'raw' : 'render');
              }}
            ></Switch>
            <Label className="-mx-2">Raw</Label>
          </SwitchField>

          {stateData !== undefined && (
            <StateButton
              label="after"
              selected={whichState === 'after'}
              setSelected={() => {
                setWhichState('after');
              }}
            />
          )}

          {
            <StateButton
              label="before"
              selected={whichState === 'before'}
              setSelected={() => {
                setWhichState('before');
              }}
            />
          }
        </div>
      </div>

      <StateView stateData={stateData} viewRawData={viewRawData} />
      {error && (
        <>
          <h1 className="text-2xl text-black-1000 font-semibold">Error</h1>
          <ErrorView error={error} />
        </>
      )}
      {resultData && Object.keys(resultData).length > 0 && (
        <>
          <h1 className="text-2xl text-black-1000 font-semibold sticky top-8 bg-white">Result</h1>
          <ResultView resultData={resultData} viewRawData={viewRawData} />
        </>
      )}
      {inputs && Object.keys(inputs).length > 0 && (
        <>
          <h1 className="text-2xl text-black-1000 font-semibold sticky top-8 bg-white">Input</h1>
          <InputsView inputs={inputs || {}} />
        </>
      )}
    </div>
  );
};

export const StateView = (props: {
  stateData: DataType | undefined;
  viewRawData: 'render' | 'raw';
}) => {
  const { stateData, viewRawData } = props;
  return (
    <>
      {stateData !== undefined && viewRawData === 'render' && <FormRenderer data={stateData} />}
      {stateData !== undefined && viewRawData === 'raw' && (
        <JsonView value={stateData} collapsed={2} enableClipboard={false} />
      )}
    </>
  );
};

export const ResultView = (props: {
  resultData: DataType | undefined;
  viewRawData: 'render' | 'raw';
}) => {
  const { resultData, viewRawData } = props;
  return (
    <>
      {resultData && viewRawData === 'render' && (
        <>
          <FormRenderer data={resultData} />
        </>
      )}
      {resultData && viewRawData === 'raw' && (
        <>
          <JsonView value={resultData} collapsed={2} enableClipboard={false} />
        </>
      )}
    </>
  );
};

export const InputsView = (props: { inputs: object }) => {
  const { inputs } = props;
  return <FormRenderer data={inputs as DataType} />;
};

type DataType = Record<string, string | number | boolean | object>;

interface FormRendererProps {
  data: Record<string, string | number | boolean | object>;
}

const Header = (props: {
  name: string;
  isExpanded: boolean;
  setExpanded: (expanded: boolean) => void;
}) => {
  const MinimizeMaximizeIcon = props.isExpanded ? ChevronUpIcon : ChevronDownIcon;

  return (
    <div className="flex flex-row gap-1 z-10 pb-2 items-center">
      <h1 className="text-lg text-black-900 font-semibold text-under">{props.name}</h1>
      <MinimizeMaximizeIcon
        className={classNames(
          'text-gray-500',
          'h-7 w-7 hover:bg-gray-50 rounded-md hover:cursor-pointer hover:scale-105'
        )}
        aria-hidden="true"
        onClick={() => {
          props.setExpanded(!props.isExpanded);
        }}
      />
    </div>
  );
};
const RenderedField = (props: {
  value: string | number | boolean | object;
  keyName: string;
  level: number;
}) => {
  const [isExpanded, setExpanded] = useState(true);
  // TODO: have max level depth.
  const { value, keyName: key, level } = props;
  const bodyClassNames =
    'border-gray-100 border-l-[8px] pl-1 hover:bg-gray-100 text-sm text-gray-700';
  if (key.startsWith('__')) {
    return null;
  }
  return (
    <>
      <Header name={key} isExpanded={isExpanded} setExpanded={setExpanded} />
      {isExpanded &&
        (typeof value === 'string' ? (
          <div key={key + '-' + String(level)}>
            <pre
              className={bodyClassNames}
              style={{ whiteSpace: 'pre-wrap', wordWrap: 'break-word', maxWidth: '1000px' }}
            >
              {value}
            </pre>
          </div>
        ) : Array.isArray(value) ? (
          <div key={key + String(level)}>
            <div>
              {value.map((v, i) => {
                return (
                  <div key={key + '-' + i.toString()} className={bodyClassNames}>
                    <RenderedField
                      value={v}
                      keyName={key + '[' + i.toString() + ']'}
                      level={level + 1}
                    />
                  </div>
                );
              })}
            </div>
          </div>
        ) : typeof value === 'object' ? (
          <div key={key}>
            <div>
              {value === null ? (
                <span>NULL</span>
              ) : (
                Object.entries(value).map(([k, v]) => {
                  return (
                    <div key={key + '-' + k} className={bodyClassNames}>
                      <RenderedField value={v} keyName={k} level={level + 1} />
                    </div>
                  );
                })
              )}
            </div>
          </div>
        ) : value === null ? (
          <div key={key + '-' + String(level)}>
            <pre className={bodyClassNames}>NULL</pre>
          </div>
        ) : (
          <div key={key + '-' + String(level)} className="">
            <pre>{value.toString()}</pre>
          </div>
        ))}
    </>
  );
};

// This component is used to render the form data in a structured way
const FormRenderer: React.FC<FormRendererProps> = ({ data }) => {
  if (data !== null) {
    return (
      <>
        {Object.entries(data).map(([key, value]) => {
          return <RenderedField keyName={key} value={value} level={0} key={key} />;
        })}
      </>
    );
  }
  return null;
};

export default FormRenderer;
