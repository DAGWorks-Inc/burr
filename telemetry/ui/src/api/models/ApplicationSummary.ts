/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { PointerModel } from './PointerModel';
export type ApplicationSummary = {
  app_id: string;
  partition_key: string | null;
  first_written: string;
  last_written: string;
  num_steps: number;
  tags: Record<string, string>;
  parent_pointer?: PointerModel | null;
};
