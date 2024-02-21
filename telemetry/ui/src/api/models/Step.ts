/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { BeginEntryModel } from './BeginEntryModel';
import type { EndEntryModel } from './EndEntryModel';
export type Step = {
  step_start_log: BeginEntryModel;
  step_end_log: EndEntryModel | null;
  step_sequence_id: number;
};
