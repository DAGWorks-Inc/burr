/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type EmailAssistantState = {
  app_id: string;
  email_to_respond: string | null;
  response_instructions: string | null;
  questions: Array<string> | null;
  answers: Array<string> | null;
  drafts: Array<string>;
  feedback_history: Array<string>;
  final_draft: string | null;
  next_step: EmailAssistantState.next_step;
};
export namespace EmailAssistantState {
  export enum next_step {
    PROCESS_INPUT = 'process_input',
    CLARIFY_INSTRUCTIONS = 'clarify_instructions',
    PROCESS_FEEDBACK = 'process_feedback'
  }
}
