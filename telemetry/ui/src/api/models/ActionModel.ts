/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Pydantic model that represents an action for storing/visualization in the UI
 */
export type ActionModel = {
    type?: string;
    name: string;
    reads: Array<string>;
    writes: Array<string>;
    code: string;
};

