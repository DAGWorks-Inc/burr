/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Pydantic model that represents an entry for the beginning of a step
 */
export type BeginEntryModel = {
    type?: string;
    start_time: string;
    action: string;
    inputs: Record<string, any>;
    sequence_id: number;
};

