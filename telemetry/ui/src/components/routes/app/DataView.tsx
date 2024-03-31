import React, { useState } from 'react';
import { Step } from '../../../api';
import JsonView from '@uiw/react-json-view';
import { Button } from '../../common/button';

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
  const [viewRawData, setViewRawData] = useState<'raw' | 'render'>('render');

  return (
    <div className="h-full pl-3 pt-2 flex flex-col gap-2">
      <div className="flex flex-row justify-between">
        <h1 className="text-2xl text-gray-600 font-semibold">State</h1>
        <div className="flex flex-row justify-end gap-2 pr-2">
          {stateData !== undefined && (
            <>
              <StateButton
                label="raw"
                selected={viewRawData === 'raw'}
                setSelected={() => {
                  setViewRawData('raw');
                }}
              />
              <StateButton
                label="render"
                selected={viewRawData === 'render'}
                setSelected={() => {
                  setViewRawData('render');
                }}
              />
              <StateButton
                label="after"
                selected={whichState === 'after'}
                setSelected={() => {
                  setWhichState('after');
                }}
              />
            </>
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

      {stateData !== undefined && viewRawData === 'render' && (
        // <JsonView value={stateData} collapsed={2} enableClipboard={false} />
        <FormRenderer data={stateData} />
      )}
      {stateData !== undefined && viewRawData === 'raw' && (
        <JsonView value={stateData} collapsed={2} enableClipboard={false} />
      )}
      {error && (
        <>
          <h1 className="text-2xl text-gray-600 font-semibold">Error</h1>
          <ErrorView error={error} />
        </>
      )}
      {resultData && viewRawData === 'render' && (
        <>
          <h1 className="text-2xl text-gray-600 font-semibold">Result</h1>
          <FormRenderer data={resultData} />
        </>
      )}
      {resultData && viewRawData === 'raw' && (
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

interface StringComponentProps {
  name: string;
  value: string;
  level: number;
}
// String component is used to render string data
const StringComponent: React.FC<StringComponentProps> = ({ name, value, level }) => {
  const renderField = (name: string, value: string, level: number) => {
    return (
      <div key={name + '-' + String(level)} className="border">
        <label className="border text-xl font-semibold">{name}</label>
        <br />
        <pre
          className=""
          style={{ whiteSpace: 'pre-wrap', wordWrap: 'break-word', maxWidth: '1000px' }}
        >
          {value}
        </pre>
      </div>
    );
  };
  return <div>{renderField(name, value, level)}</div>;
};

interface FormRendererProps {
  data: Record<string, string | number | boolean | object>;
}

// This component is used to render the form data in a structured way
const FormRenderer: React.FC<FormRendererProps> = ({ data }) => {
  const renderField = (value: string | number | boolean | object, key: string, level: number) => {
    // TODO: have max level depth.
    if (typeof value === 'string') {
      return <StringComponent name={key} value={value} level={level} />;
    } else if (Array.isArray(value)) {
      return (
        <div key={key + '-' + String(level)} className="border">
          <label className="border text-xl font-semibold">{key}</label>
          <br />
          <div>
            {value.map((v, i) => {
              return (
                <div key={key + '-' + i.toString()} className="border-2">
                  {renderField(v, key + '-' + i.toString(), level + 1)}
                </div>
              );
            })}
          </div>
        </div>
      );
    } else if (typeof value === 'object') {
      return (
        <div key={key} className="border">
          <label className="border text-xl font-semibold">{key}</label>
          <br />
          <div>
            {value === null ? (
              <span>NULL</span>
            ) : (
              Object.entries(value).map(([k, v]) => {
                return (
                  <div key={key + '-' + k} className="border-2">
                    {renderField(v, k, level + 1)}
                  </div>
                );
              })
            )}
          </div>
        </div>
      );
    } else if (value === null) {
      <div key={key + '-' + String(level)} className="border">
        <label className="border text-xl font-semibold">{key}</label>
        <br />
        <span>NULL</span>
      </div>;
    } else {
      return (
        <div key={key + '-' + String(level)} className="border">
          <label className="border text-xl font-semibold">{key}</label>
          <br />
          <span>{value.toString()}</span>
        </div>
      );
    }
  };

  const renderFields = () => {
    if (data !== null) {
      return Object.entries(data).map(([key, value]) => renderField(value, key, 0));
    }
    return null;
  };

  return <div>{renderFields()}</div>;
};

export default FormRenderer;
