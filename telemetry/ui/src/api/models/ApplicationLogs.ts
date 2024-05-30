/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ApplicationModel } from './ApplicationModel';
import type { ChildApplicationModel } from './ChildApplicationModel';
import type { PointerModel } from './PointerModel';
import type { Step } from './Step';
/**
 * Application logs are purely flat --
 * we will likely be rethinking this but for now this provides for easy parsing.
 */
export type ApplicationLogs = {
  application: ApplicationModel;
  children: Array<ChildApplicationModel>;
  steps: Array<Step>;
  parent_pointer?: PointerModel | null;
  spawning_parent_pointer?: PointerModel | null;
};
