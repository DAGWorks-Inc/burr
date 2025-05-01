/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { BeginSpanModel } from './BeginSpanModel';
import type { EndSpanModel } from './EndSpanModel';
/**
 * Represents a span. These have action sequence IDs associated with
 * them to put them in order.
 */
export type Span = {
  begin_entry: BeginSpanModel;
  end_entry: EndSpanModel | null;
};
