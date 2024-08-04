import { AttributeModel, Step } from './api';

export type Status = 'success' | 'failure' | 'running';
/*
 * Gets the action given a step.
 * TODO -- put this in the BE
 */
export const getActionStatus = (action: Step) => {
  if (action.step_end_log === null) {
    return 'running';
  }
  if (action?.step_end_log?.exception) {
    return 'failure';
  }
  return 'success';
};

export const getUniqueAttributeID = (attribute: AttributeModel) => {
  return `${attribute.action_sequence_id}-${attribute.span_id}`;
};
