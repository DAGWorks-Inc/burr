/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { PointerModel } from './PointerModel';
/**
 * Stores data about a child application (either a fork or a spawned application).
 * This allows us to link from parent -> child in the UI.
 */
export type ChildApplicationModel = {
  type?: string;
  child: PointerModel;
  event_time: string;
  event_type: ChildApplicationModel.event_type;
  sequence_id: number | null;
};
export namespace ChildApplicationModel {
  export enum event_type {
    FORK = 'fork',
    SPAWN_START = 'spawn_start'
  }
}
