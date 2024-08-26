/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Pydantic model that represents an entry for the beginning of a stream
 */
export type InitializeStreamModel = {
  type?: string;
  action_sequence_id: number;
  span_id: string | null;
  stream_init_time: string;
};
