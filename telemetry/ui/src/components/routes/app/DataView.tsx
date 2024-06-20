import React, { useEffect, useState } from 'react';
import { Step } from '../../../api';
import JsonView from '@uiw/react-json-view';
import { Button } from '../../common/button';
import { Switch, SwitchField } from '../../common/switch';
import { Label } from '../../common/fieldset';
import { classNames } from '../../../utils/tailwind';
import { ChevronDownIcon, ChevronUpIcon } from '@heroicons/react/20/solid';

/**
 * Common JSON view so we can make everything look the same.
 * We override icons to keep them consistent.
 * @param props The value/how deep we want it to be collapsed (defaults to 2)
 * @returns JSON view
 */
const CommonJsonView = (props: { value: object; collapsed?: number }) => {
  const collapsed = props.collapsed || 2;
  return (
    <JsonView value={props.value} collapsed={collapsed} enableClipboard={true}>
      <JsonView.Arrow
        // @ts-ignore
        render={({ 'data-expanded': isExpanded }) => {
          if (isExpanded) {
            return (
              <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 16 16"
                fill="currentColor"
                className="size-4 hover:cursor-pointer"
              >
                <path
                  fillRule="evenodd"
                  d="M4.22 6.22a.75.75 0 0 1 1.06 0L8 8.94l2.72-2.72a.75.75 0 1 1 1.06 1.06l-3.25 3.25a.75.75 0 0 1-1.06 0L4.22 7.28a.75.75 0 0 1 0-1.06Z"
                  clipRule="evenodd"
                />
              </svg>
            );
          }
          return (
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 16 16"
              fill="currentColor"
              className="size-4 hover:cursor-pointer"
            >
              <path
                fillRule="evenodd"
                d="M11.78 9.78a.75.75 0 0 1-1.06 0L8 7.06 5.28 9.78a.75.75 0 0 1-1.06-1.06l3.25-3.25a.75.75 0 0 1 1.06 0l3.25 3.25a.75.75 0 0 1 0 1.06Z"
                clipRule="evenodd"
              />
            </svg>
          );
        }}
      ></JsonView.Arrow>
    </JsonView>
  );
};
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
/**
 * Section header that allows for exapnsion/contraction of all subcomponents
 */
const SectionHeaderWithExpand = (props: {
  name: string;
  defaultExpanded?: boolean;
  setDefaultExpanded?: (expanded: boolean) => void;
  enableExpansion: boolean;
}) => {
  const MinimizeMaximizeIcon = props.defaultExpanded ? ChevronUpIcon : ChevronDownIcon;
  return (
    <div className="flex flex-row items-center gap-1">
      <h1 className="text-2xl text-gray-900 font-semibold">{props.name}</h1>
      {props.enableExpansion && (
        <MinimizeMaximizeIcon
          className={classNames(
            'text-gray-500',
            'h-5 w-5 rounded-md hover:cursor-pointer hover:scale-105'
          )}
          aria-hidden="true"
          onClick={() => {
            if (props.setDefaultExpanded) {
              props.setDefaultExpanded(!props.defaultExpanded);
            }
          }}
        />
      )}
    </div>
  );
};
export const DataView = (props: { currentStep: Step | undefined; priorStep: Step | undefined }) => {
  const [whichState, setWhichState] = useState<'after' | 'before' | 'compare'>('after');
  const stepToExamine = whichState !== 'before' ? props.currentStep : props.priorStep;
  const stateData = stepToExamine?.step_end_log?.state;
  const resultData = stepToExamine?.step_end_log?.result || undefined;
  const inputs = stepToExamine?.step_start_log?.inputs;
  const compareStateData =
    whichState === 'compare' ? props.priorStep?.step_end_log?.state : undefined;
  const error = props.currentStep?.step_end_log?.exception;
  const [viewRawData, setViewRawData] = useState<'raw' | 'render'>('render');

  const [allStateExpanded, setAllStateExpanded] = useState(true);
  const [allResultExpanded, setAllResultExpanded] = useState(true);
  const [allInputExpanded, setAllInputExpanded] = useState(true);

  return (
    <div className="pl-1 flex flex-col gap-2 hide-scrollbar">
      <div className="flex flex-row justify-between sticky top-0 z-20 bg-white">
        <SectionHeaderWithExpand
          name="State"
          defaultExpanded={allStateExpanded}
          setDefaultExpanded={setAllStateExpanded}
          enableExpansion={viewRawData === 'render'}
        />
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
          {stateData !== undefined && (
            <StateButton
              label="difference"
              selected={whichState === 'compare'}
              setSelected={() => {
                setWhichState('compare');
              }}
            />
          )}
        </div>
      </div>

      <StateView
        stateData={stateData}
        viewRawData={viewRawData}
        isExpanded={allStateExpanded}
        compareStateData={compareStateData}
      />
      {error && (
        <>
          <h1 className="text-2xl text-gray-900 font-semibold">Error</h1>
          <ErrorView error={error} />
        </>
      )}
      {resultData && Object.keys(resultData).length > 0 && (
        <>
          <SectionHeaderWithExpand
            name="Result"
            defaultExpanded={allResultExpanded}
            setDefaultExpanded={setAllResultExpanded}
            enableExpansion={viewRawData === 'render'}
          />
          <ResultView
            resultData={resultData}
            viewRawData={viewRawData}
            isExpanded={allResultExpanded}
          />
        </>
      )}
      {inputs && Object.keys(inputs).length > 0 && (
        <>
          <SectionHeaderWithExpand
            name="Inputs"
            defaultExpanded={allInputExpanded}
            setDefaultExpanded={setAllInputExpanded}
            enableExpansion={viewRawData === 'render'}
          />
          <InputsView inputs={inputs} isExpanded={allInputExpanded} viewRawData={viewRawData} />
          {/* <FormRenderer data={inputs as DataType} isDefaultExpanded={allInputExpanded} /> */}
        </>
      )}
    </div>
  );
};
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const primitive = (value: any): boolean => {
  return (typeof value !== 'object' && typeof value !== 'function') || value === null;
};
/**
 * Basic json diff -- will return the json object representing the diffs.
 * Assumes arrays are compared by index -- nothing smarter than that.
 *
 * This has an entry for each difference -- e.g. everything that
 * is in current and not prior or different in current and prior.
 *
 * @param current -- current object/primitive/array
 * @param prior -- prior object/primitive/array
 * @returns -- object representing the diff
 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const diffJSON = (current: any, prior: any): any | undefined => {
  // If the type doesn't match, they're not equal
  if (typeof prior !== typeof current) {
    return current;
  }
  // If they're both primitives, we can compare them directly
  if (primitive(prior) || primitive(current)) {
    return prior !== current ? current : undefined;
  }
  // If they're both arrays, we need to compare each element (recursively)
  if (Array.isArray(prior) && Array.isArray(current)) {
    const currentLength = current.length;
    const arrayDiff = [];
    for (let i = 0; i < currentLength; i++) {
      if (i > prior.length - 1) {
        arrayDiff[i] = current[i];
        continue;
      }
      const result = diffJSON(current[i], prior[i]);
      if (result !== undefined && (Object.keys(result).length !== 0 || primitive(result))) {
        arrayDiff[i] = result;
      }
    }
    if (arrayDiff.length > 0) {
      return arrayDiff.filter((item) => item !== undefined);
    } else {
      return undefined;
    }
  }
  // If they're both objects, we need to compare each key (recursively)
  const keys = new Set([...Object.keys(prior), ...Object.keys(current)]);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const diff: any = {};
  keys.forEach((key) => {
    // key not in prior but in current
    if (prior[key] === undefined && current[key] !== undefined) {
      diff[key] = current[key];
    } else {
      // diff the objects
      const result = diffJSON(current[key], prior[key]);
      if (result !== undefined && (Object.keys(result).length !== 0 || primitive(result))) {
        diff[key] = result;
      }
    }
  });
  return diff;
};

export const StateView = (props: {
  stateData: DataType | undefined;
  compareStateData: DataType | undefined;
  viewRawData: 'render' | 'raw';
  isExpanded: boolean;
}) => {
  const { stateData, viewRawData, isExpanded } = props;
  const stateToView =
    props.stateData === undefined || props.compareStateData === undefined
      ? stateData
      : diffJSON(props.stateData, props.compareStateData);
  return (
    <>
      {stateData !== undefined && viewRawData === 'render' && (
        <FormRenderer data={stateToView || {}} isDefaultExpanded={isExpanded} />
      )}
      {stateData !== undefined && viewRawData === 'raw' && (
        <CommonJsonView value={stateToView || {}} />
      )}
    </>
  );
};

export const ResultView = (props: {
  resultData: DataType | undefined;
  viewRawData: 'render' | 'raw';
  isExpanded: boolean;
}) => {
  const { resultData, viewRawData, isExpanded } = props;
  return (
    <>
      {resultData && viewRawData === 'render' && (
        <>
          <FormRenderer data={resultData} isDefaultExpanded={isExpanded} />
        </>
      )}
      {resultData && viewRawData === 'raw' && (
        <>
          <CommonJsonView value={resultData} />{' '}
        </>
      )}
    </>
  );
};

export const InputsView = (props: {
  inputs: object;
  isExpanded: boolean;
  viewRawData: 'render' | 'raw';
}) => {
  const { inputs, viewRawData, isExpanded } = props;
  return (
    <>
      {inputs && viewRawData === 'render' ? (
        <>
          <FormRenderer data={inputs as DataType} isDefaultExpanded={isExpanded} />
        </>
      ) : (
        (inputs && viewRawData) === 'raw' && (
          <>
            <CommonJsonView value={inputs} />
          </>
        )
      )}
    </>
  );
};

type DataType = Record<string, string | number | boolean | object>;

const Header = (props: {
  name: string;
  isExpanded: boolean;
  setExpanded: (expanded: boolean) => void;
}) => {
  const MinimizeMaximizeIcon = props.isExpanded ? ChevronUpIcon : ChevronDownIcon;

  return (
    <div className="flex flex-row gap-1 z-10 pb-2 items-center">
      <h1 className="text-lg text-gray-900 font-semibold text-under">{props.name}</h1>
      <MinimizeMaximizeIcon
        className={classNames(
          'text-gray-500',
          'h-6 w-6 hover:bg-gray-50 rounded-md hover:cursor-pointer hover:scale-105'
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
  defaultExpanded: boolean;
}) => {
  const [isExpanded, setExpanded] = useState(true);
  useEffect(() => {
    setExpanded(props.defaultExpanded);
  }, [props.defaultExpanded, props.value, props.keyName]);
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
        (props.value instanceof Array &&
        props.value.length > 0 &&
        typeof props.value[0] === 'number' ? (
          <div key={key + '-' + String(level)}>
            <CommonJsonView value={props.value} />
          </div>
        ) : typeof value === 'string' ? (
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
                      defaultExpanded={props.defaultExpanded}
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
                  // if (v instanceof Array && v.length > 0 && typeof v[0] === 'number') {
                  //   // we want to display arrays of numbers as a single string.
                  //   v = v.toString();
                  // }
                  return (
                    <div key={key + '-' + k} className={bodyClassNames}>
                      <RenderedField
                        value={v}
                        keyName={k}
                        level={level + 1}
                        defaultExpanded={props.defaultExpanded}
                      />
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

interface FormRendererProps {
  data: Record<string, string | number | boolean | object>;
  isDefaultExpanded: boolean;
}

// This component is used to render the form data in a structured way
const FormRenderer: React.FC<FormRendererProps> = ({ data, isDefaultExpanded: isExpanded }) => {
  if (data !== null) {
    return (
      <>
        {Object.entries(data).map(([key, value]) => {
          return (
            <RenderedField
              keyName={key}
              value={value}
              level={0}
              key={key}
              defaultExpanded={isExpanded}
            />
          );
        })}
      </>
    );
  }
  return null;
};

export default FormRenderer;
