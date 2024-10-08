/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type AnnotationDataPointer = {
  type: AnnotationDataPointer.type;
  field_name: string;
  span_id: string | null;
};
export namespace AnnotationDataPointer {
  export enum type {
    STATE_FIELD = 'state_field',
    ATTRIBUTE = 'attribute'
  }
}
