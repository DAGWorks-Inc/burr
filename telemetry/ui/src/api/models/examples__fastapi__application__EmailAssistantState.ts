/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ClarificationAnswers } from './ClarificationAnswers';
import type { ClarificationQuestions } from './ClarificationQuestions';
import type { Email } from './Email';
export type examples__fastapi__application__EmailAssistantState = {
  email_to_respond?: string | null;
  response_instructions?: string | null;
  questions?: ClarificationQuestions | null;
  answers?: ClarificationAnswers | null;
  draft_history?: Array<Email>;
  current_draft?: Email | null;
  feedback_history?: Array<string>;
  feedback?: string | null;
  final_draft?: string | null;
};
