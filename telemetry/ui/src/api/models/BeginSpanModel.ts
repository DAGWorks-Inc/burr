/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Pydantic model that represents an entry for the beginning of a span
 */
export type BeginSpanModel = {
  type?: string;
  start_time: string;
  action_sequence_id: number;
  span_id: string;
  span_name: string;
  parent_span_id: string | null;
  span_dependencies: Array<string>;
};
