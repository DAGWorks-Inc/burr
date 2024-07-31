/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Generic link for indexing job -- can be exposed in 'admin mode' in the UI
 */
export type IndexingJob = {
  id: number;
  start_time: string;
  end_time: string | null;
  status: string;
  records_processed: number;
  metadata: Record<string, any>;
};
