/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { AnnotationObservation } from './AnnotationObservation';
/**
 * Generic link for indexing job -- can be exposed in 'admin mode' in the UI
 */
export type AnnotationOut = {
  span_id: string | null;
  step_name: string;
  tags: Array<string>;
  observations: Array<AnnotationObservation>;
  id: number;
  project_id: string;
  app_id: string;
  partition_key: string | null;
  step_sequence_id: number;
  created: string;
  updated: string;
};
