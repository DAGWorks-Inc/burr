/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Pydantic model that represents an entry for the first item of a stream
 */
export type EndStreamModel = {
  type?: string;
  action_sequence_id: number;
  span_id: string | null;
  end_time: string;
  items_streamed: number;
};
