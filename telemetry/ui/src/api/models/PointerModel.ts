/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Stores pointers to unique identifiers for an application.
 * This is used by a few different places to, say, store parent references
 * bewteen application instances.
 */
export type PointerModel = {
  type?: string;
  app_id: string;
  sequence_id: number | null;
  partition_key: string | null;
};
