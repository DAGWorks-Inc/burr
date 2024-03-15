/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type ChatItem = {
  content: string;
  type: ChatItem.type;
  role: ChatItem.role;
};
export namespace ChatItem {
  export enum type {
    IMAGE = 'image',
    TEXT = 'text',
    CODE = 'code',
    ERROR = 'error'
  }
  export enum role {
    USER = 'user',
    ASSISTANT = 'assistant'
  }
}
