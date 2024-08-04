/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Represents a logged artifact
 */
export type AttributeModel = {
  type?: string;
  key: string;
  action_sequence_id: number;
  span_id: string | null;
  value: Record<string, any> | string | number | boolean | null;
  tags: Record<string, string>;
};
