/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Pydantic model that represents an entry for the end of a step
 */
export type EndEntryModel = {
    type?: string;
    end_time: string;
    action: string;
    result: (Record<string, any> | null);
    exception: (string | null);
    state: Record<string, any>;
    sequence_id: number;
};

