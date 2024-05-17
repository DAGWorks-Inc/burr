/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ApplicationModel } from './ApplicationModel';
import type { PointerModel } from './PointerModel';
import type { Step } from './Step';
/**
 * Application logs are purely flat --
 * we will likely be rethinking this but for now this provides for easy parsing.
 */
export type ApplicationLogs = {
  application: ApplicationModel;
  steps: Array<Step>;
  parent_pointer?: PointerModel | null;
};
