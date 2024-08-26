/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { AttributeModel } from './AttributeModel';
import type { BeginEntryModel } from './BeginEntryModel';
import type { EndEntryModel } from './EndEntryModel';
import type { EndStreamModel } from './EndStreamModel';
import type { FirstItemStreamModel } from './FirstItemStreamModel';
import type { InitializeStreamModel } from './InitializeStreamModel';
import type { Span } from './Span';
/**
 * Log of  astep -- has a start and an end.
 */
export type Step = {
  step_start_log: BeginEntryModel;
  step_end_log: EndEntryModel | null;
  spans: Array<Span>;
  attributes: Array<AttributeModel>;
  streaming_events: Array<InitializeStreamModel | FirstItemStreamModel | EndStreamModel>;
};
