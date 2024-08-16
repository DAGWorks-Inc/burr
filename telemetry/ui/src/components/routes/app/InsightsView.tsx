import { AttributeModel, Step } from '../../../api';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../common/table';
import React from 'react';
import { ChevronDownIcon, ChevronUpIcon } from '@heroicons/react/24/outline';

/**
 * Insights allow us to visualize and surface attributes stored in steps.
 * The common use-case is LLM calls -- we want to summarize tokens, prompts, etc...
 * That said, we could also use it for loss functions on ML training, whatnot
 * Eventually we will be moving this to the server side and make it at a project level, but this is
 * a good start (at the app level).
 *
 * Insights are an aggregation over attributes
 */
type InsightBase = {
  // Tells whether or not we have the insight, meaning whether it should register or not
  hasInsight: (allAttributes: AttributeModel[]) => boolean;
  // Name of the insight
  insightName: string;
  // The insight value
  RenderInsightValue: React.FC<{ attributes: AttributeModel[] }>;
};

/**
 * We want to allow them to expose individual values, but we may change the types here
 * later. Basically we have a simple flag on whether they show individual values (E.g if they're an aggregation),
 * and if they do, we have a function to capture them and a function to render them.
 *
 * These are undefined if we do not.
 *
 * Code will likely be repeated between this and the hasInsight/RenderInsightValue, but we'll keep it separate
 * for now.
 */

type InsightWithIndividualValues = InsightBase & {
  // Captures individual values for the insight -- allows you to expand out
  captureIndividualValues: (allAttributes: AttributeModel[]) => AttributeModel[];
  // Render the individual values
  RenderIndividualValue: React.FC<{ attribute: AttributeModel }>;
};

type InsightWithoutIndividualValues = InsightBase & {
  captureIndividualValues?: never;
  RenderIndividualValue?: never;
};

type Insight = InsightWithIndividualValues | InsightWithoutIndividualValues;

const REGISTERED_INSIGHTS: Insight[] = [
  {
    hasInsight: (allAttributes) => {
      return allAttributes.some((attribute) => attribute.key.endsWith('prompt_tokens'));
    },
    insightName: 'Total Prompt Tokens',
    RenderInsightValue: (props) => {
      let totalPromptTokens = 0;
      props.attributes.forEach((attribute) => {
        if (attribute.key.endsWith('prompt_tokens')) {
          totalPromptTokens += attribute.value as number;
        }
      });
      return <p>{totalPromptTokens}</p>;
    },
    captureIndividualValues: (allAttributes) => {
      return allAttributes.filter((attribute) => attribute.key.endsWith('prompt_tokens'));
    },
    RenderIndividualValue: (props: { attribute: AttributeModel }) => {
      return <p>{props.attribute.value?.toString()}</p>;
    }
  },
  {
    hasInsight: (allAttributes) => {
      return allAttributes.some((attribute) => attribute.key.endsWith('completion_tokens'));
    },
    insightName: 'Total Completion Tokens',
    RenderInsightValue: (props) => {
      let totalCompletionTokens = 0;
      props.attributes.forEach((attribute) => {
        if (attribute.key.endsWith('completion_tokens')) {
          totalCompletionTokens += attribute.value as number;
        }
      });
      return <p>{totalCompletionTokens}</p>;
    },
    captureIndividualValues: (allAttributes) => {
      return allAttributes.filter((attribute) => attribute.key.endsWith('completion_tokens'));
    },
    RenderIndividualValue: (props: { attribute: AttributeModel }) => {
      return <p>{props.attribute.value?.toString()}</p>;
    }
  },
  {
    hasInsight: (allAttributes) => {
      return allAttributes.some((attribute) => attribute.key.endsWith('prompt_tokens'));
    },
    insightName: 'Total LLM Calls',
    RenderInsightValue: (props) => {
      let totalLLMCalls = 0;
      props.attributes.forEach((attribute) => {
        if (attribute.key.endsWith('prompt_tokens')) {
          totalLLMCalls += 1;
        }
      });
      return <p>{totalLLMCalls}</p>;
    }
    // TODO -- get this to work
    // Currently it's just a filter but we should be able to create individual values here
    // It's just a simmple groupby/count
    // captureIndividualValues: (allAttributes) => {
    //   return allAttributes.filter((attribute) => attribute.key.endsWith('prompt_tokens'));
    // },
    // RenderIndividualValue: (props: { attribute: AttributeModel }) => {
    //   debugger;
    //   return <p>1</p>;
    // }
  }
];

const InsightSubTable = (props: { attributes: AttributeModel[]; insight: Insight }) => {
  const individualValues = props.insight.captureIndividualValues?.(props.attributes);
  const [isExpanded, setIsExpanded] = React.useState(false);
  const ExpandIcon = isExpanded ? ChevronUpIcon : ChevronDownIcon;
  const canExpand = props.insight.captureIndividualValues !== undefined;
  return (
    <>
      <TableRow className="hover:bg-gray-50">
        <TableCell>{props.insight.insightName}</TableCell>
        <TableCell></TableCell>
        <TableCell>
          <props.insight.RenderInsightValue attributes={props.attributes} />
        </TableCell>
        <TableCell>
          {canExpand ? (
            <button
              onClick={() => {
                setIsExpanded(!isExpanded);
              }}
            >
              <ExpandIcon className="h-5 w-5" />
            </button>
          ) : (
            <></>
          )}
        </TableCell>
      </TableRow>
      {isExpanded
        ? individualValues?.map((attribute, i) => {
            const insightCasted = props.insight as InsightWithIndividualValues;
            return (
              <TableRow key={attribute.key + i} className="hover:bg-gray-50">
                <TableCell></TableCell>
                <TableCell className=" text-gray-400">{attribute.span_id}</TableCell>
                <TableCell>
                  <insightCasted.RenderIndividualValue attribute={attribute} />
                </TableCell>
                <TableCell></TableCell>
              </TableRow>
            );
          })
        : null}
    </>
  );
};

export const InsightsView = (props: { steps: Step[] }) => {
  const allAttributes: AttributeModel[] = props.steps.flatMap((step) => step.attributes);
  let noInsights = true;

  const out = (
    <div className="pt-0">
      <Table dense={1}>
        <TableHead>
          <TableRow className="hover:bg-gray-100">
            <TableHeader>Name </TableHeader>
            <TableHeader>Span ID</TableHeader>
            <TableHeader>Value</TableHeader>
            <TableHeader></TableHeader>
            <TableHeader colSpan={1}></TableHeader>
          </TableRow>
        </TableHead>
        <TableBody>
          {REGISTERED_INSIGHTS.map((insight) => {
            if (insight.hasInsight(allAttributes)) {
              noInsights = false;
              return (
                <InsightSubTable
                  key={insight.insightName}
                  attributes={allAttributes}
                  insight={insight}
                />
              );
            }
          })}
        </TableBody>
      </Table>
    </div>
  );
  if (noInsights) {
    return (
      <div>
        <h2 className="text-gray-500 max-w-xl">
          Use this tab to view summaries of your application -- E.G. LLM call data. To instrument,
          and start collecting, see{' '}
          <a
            className="text-dwlightblue"
            href={'https://burr.dagworks.io/concepts/additional-visibility/#quickstart'}
          >
            see docs.
          </a>
        </h2>
      </div>
    );
  }
  return out;
};
