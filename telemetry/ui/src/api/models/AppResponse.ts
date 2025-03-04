/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { examples__fastapi__application__EmailAssistantState } from './examples__fastapi__application__EmailAssistantState';
export type AppResponse = {
  app_id: string;
  next_step: 'process_input' | 'clarify_instructions' | 'process_feedback' | null;
  state: examples__fastapi__application__EmailAssistantState;
};
