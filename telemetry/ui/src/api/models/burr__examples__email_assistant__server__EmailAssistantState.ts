/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type burr__examples__email_assistant__server__EmailAssistantState = {
  app_id: string;
  email_to_respond: string | null;
  response_instructions: string | null;
  questions: Array<string> | null;
  answers: Array<string> | null;
  drafts: Array<string>;
  feedback_history: Array<string>;
  final_draft: string | null;
  next_step: burr__examples__email_assistant__server__EmailAssistantState.next_step;
};
export namespace burr__examples__email_assistant__server__EmailAssistantState {
  export enum next_step {
    PROCESS_INPUT = 'process_input',
    CLARIFY_INSTRUCTIONS = 'clarify_instructions',
    PROCESS_FEEDBACK = 'process_feedback'
  }
}
