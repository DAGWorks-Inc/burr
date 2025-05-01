/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ActionModel } from './ActionModel';
import type { TransitionModel } from './TransitionModel';
/**
 * Pydantic model that represents an application for storing/visualization in the UI
 */
export type ApplicationModel = {
  type?: string;
  entrypoint: string;
  actions: Array<ActionModel>;
  transitions: Array<TransitionModel>;
};
