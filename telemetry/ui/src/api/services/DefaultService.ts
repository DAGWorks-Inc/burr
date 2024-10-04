/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ApplicationLogs } from '../models/ApplicationLogs';
import type { ApplicationPage } from '../models/ApplicationPage';
import type { AppResponse } from '../models/AppResponse';
import type { BackendSpec } from '../models/BackendSpec';
import type { burr__examples__email_assistant__server__EmailAssistantState } from '../models/burr__examples__email_assistant__server__EmailAssistantState';
import type { ChatItem } from '../models/ChatItem';
import type { DraftInit } from '../models/DraftInit';
import type { Feedback } from '../models/Feedback';
import type { IndexingJob } from '../models/IndexingJob';
import type { Project } from '../models/Project';
import type { PromptInput } from '../models/PromptInput';
import type { QuestionAnswers } from '../models/QuestionAnswers';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class DefaultService {
  /**
   * Is Ready
   * @returns any Successful Response
   * @throws ApiError
   */
  public static isReadyReadyGet(): CancelablePromise<any> {
    return __request(OpenAPI, {
      method: 'GET',
      url: '/ready'
    });
  }
  /**
   * Get App Spec
   * @returns BackendSpec Successful Response
   * @throws ApiError
   */
  public static getAppSpecApiV0MetadataAppSpecGet(): CancelablePromise<BackendSpec> {
    return __request(OpenAPI, {
      method: 'GET',
      url: '/api/v0/metadata/app_spec'
    });
  }
  /**
   * Get Projects
   * Gets all projects visible by the user.
   *
   * :param request: FastAPI request
   * :return:  a list of projects visible by the user
   * @returns Project Successful Response
   * @throws ApiError
   */
  public static getProjectsApiV0ProjectsGet(): CancelablePromise<Array<Project>> {
    return __request(OpenAPI, {
      method: 'GET',
      url: '/api/v0/projects'
    });
  }
  /**
   * Get Apps
   * Gets all apps visible by the user
   *
   * :param request: FastAPI request
   * :param project_id: project name
   * :return: a list of projects visible by the user
   * @param projectId
   * @param partitionKey
   * @param limit
   * @param offset
   * @returns ApplicationPage Successful Response
   * @throws ApiError
   */
  public static getAppsApiV0ProjectIdPartitionKeyAppsGet(
    projectId: string,
    partitionKey: string,
    limit: number = 100,
    offset?: number
  ): CancelablePromise<ApplicationPage> {
    return __request(OpenAPI, {
      method: 'GET',
      url: '/api/v0/{project_id}/{partition_key}/apps',
      path: {
        project_id: projectId,
        partition_key: partitionKey
      },
      query: {
        limit: limit,
        offset: offset
      },
      errors: {
        422: `Validation Error`
      }
    });
  }
  /**
   * Get Application Logs
   * Lists steps for a given App.
   * TODO: add streaming capabilities for bi-directional communication
   * TODO: add pagination for quicker loading
   *
   * :param request: FastAPI
   * :param project_id: ID of the project
   * :param app_id: ID of the assIndociated application
   * :return: A list of steps with all associated step data
   * @param projectId
   * @param appId
   * @param partitionKey
   * @returns ApplicationLogs Successful Response
   * @throws ApiError
   */
  public static getApplicationLogsApiV0ProjectIdAppIdPartitionKeyAppsGet(
    projectId: string,
    appId: string,
    partitionKey: string
  ): CancelablePromise<ApplicationLogs> {
    return __request(OpenAPI, {
      method: 'GET',
      url: '/api/v0/{project_id}/{app_id}/{partition_key}/apps',
      path: {
        project_id: projectId,
        app_id: appId,
        partition_key: partitionKey
      },
      errors: {
        422: `Validation Error`
      }
    });
  }
  /**
   * Ready
   * @returns boolean Successful Response
   * @throws ApiError
   */
  public static readyApiV0ReadyGet(): CancelablePromise<boolean> {
    return __request(OpenAPI, {
      method: 'GET',
      url: '/api/v0/ready'
    });
  }
  /**
   * Get Indexing Jobs
   * @param offset
   * @param limit
   * @param filterEmpty
   * @returns IndexingJob Successful Response
   * @throws ApiError
   */
  public static getIndexingJobsApiV0IndexingJobsGet(
    offset?: number,
    limit: number = 100,
    filterEmpty: boolean = true
  ): CancelablePromise<Array<IndexingJob>> {
    return __request(OpenAPI, {
      method: 'GET',
      url: '/api/v0/indexing_jobs',
      query: {
        offset: offset,
        limit: limit,
        filter_empty: filterEmpty
      },
      errors: {
        422: `Validation Error`
      }
    });
  }
  /**
   * Version
   * Returns the burr version
   * @returns any Successful Response
   * @throws ApiError
   */
  public static versionApiV0VersionGet(): CancelablePromise<Record<string, any>> {
    return __request(OpenAPI, {
      method: 'GET',
      url: '/api/v0/version'
    });
  }
  /**
   * Chat Response
   * Chat response endpoint. User passes in a prompt and the system returns the
   * full chat history, so its easier to render.
   *
   * :param project_id: Project ID to run
   * :param app_id: Application ID to run
   * :param prompt: Prompt to send to the chatbot
   * :return:
   * @param projectId
   * @param appId
   * @param prompt
   * @returns ChatItem Successful Response
   * @throws ApiError
   */
  public static chatResponseApiV0ChatbotResponseProjectIdAppIdPost(
    projectId: string,
    appId: string,
    prompt: string
  ): CancelablePromise<Array<ChatItem>> {
    return __request(OpenAPI, {
      method: 'POST',
      url: '/api/v0/chatbot/response/{{project_id}}/{{app_id}}',
      query: {
        project_id: projectId,
        app_id: appId,
        prompt: prompt
      },
      errors: {
        422: `Validation Error`
      }
    });
  }
  /**
   * Chat History
   * Endpoint to get chat history. Gets the application and returns the chat history from state.
   *
   * :param project_id: Project ID
   * :param app_id: App ID.
   * :return: The list of chat items in the state
   * @param projectId
   * @param appId
   * @returns ChatItem Successful Response
   * @throws ApiError
   */
  public static chatHistoryApiV0ChatbotResponseProjectIdAppIdGet(
    projectId: string,
    appId: string
  ): CancelablePromise<Array<ChatItem>> {
    return __request(OpenAPI, {
      method: 'GET',
      url: '/api/v0/chatbot/response/{project_id}/{app_id}',
      path: {
        project_id: projectId,
        app_id: appId
      },
      errors: {
        422: `Validation Error`
      }
    });
  }
  /**
   * Create New Application
   * Endpoint to create a new application -- used by the FE when
   * the user types in a new App ID
   *
   * :param project_id: Project ID
   * :param app_id: App ID
   * :return: The app ID
   * @param projectId
   * @param appId
   * @returns string Successful Response
   * @throws ApiError
   */
  public static createNewApplicationApiV0ChatbotCreateProjectIdAppIdPost(
    projectId: string,
    appId: string
  ): CancelablePromise<string> {
    return __request(OpenAPI, {
      method: 'POST',
      url: '/api/v0/chatbot/create/{project_id}/{app_id}',
      path: {
        project_id: projectId,
        app_id: appId
      },
      errors: {
        422: `Validation Error`
      }
    });
  }
  /**
   * Create New Application
   * @param projectId
   * @param appId
   * @returns string Successful Response
   * @throws ApiError
   */
  public static createNewApplicationApiV0EmailAssistantCreateNewProjectIdAppIdPost(
    projectId: string,
    appId: string
  ): CancelablePromise<string> {
    return __request(OpenAPI, {
      method: 'POST',
      url: '/api/v0/email_assistant/create_new/{project_id}/{app_id}',
      path: {
        project_id: projectId,
        app_id: appId
      },
      errors: {
        422: `Validation Error`
      }
    });
  }
  /**
   * Initialize Draft
   * Endpoint to initialize the draft with the email and instructions
   *
   * :param project_id: ID of the project (used by telemetry tracking/storage)
   * :param app_id: ID of the application (used to reference the app)
   * :param draft_data: Data to initialize the draft
   * :return: The state of the application after initialization
   * @param projectId
   * @param appId
   * @param requestBody
   * @returns burr__examples__email_assistant__server__EmailAssistantState Successful Response
   * @throws ApiError
   */
  public static initializeDraftApiV0EmailAssistantCreateProjectIdAppIdPost(
    projectId: string,
    appId: string,
    requestBody: DraftInit
  ): CancelablePromise<burr__examples__email_assistant__server__EmailAssistantState> {
    return __request(OpenAPI, {
      method: 'POST',
      url: '/api/v0/email_assistant/create/{project_id}/{app_id}',
      path: {
        project_id: projectId,
        app_id: appId
      },
      body: requestBody,
      mediaType: 'application/json',
      errors: {
        422: `Validation Error`
      }
    });
  }
  /**
   * Answer Questions
   * Endpoint to answer questions the LLM provides
   *
   * :param project_id: ID of the project (used by telemetry tracking/storage)
   * :param app_id: ID of the application (used to reference the app)
   * :param question_answers: Answers to the questions
   * :return: The state of the application after answering the questions
   * @param projectId
   * @param appId
   * @param requestBody
   * @returns burr__examples__email_assistant__server__EmailAssistantState Successful Response
   * @throws ApiError
   */
  public static answerQuestionsApiV0EmailAssistantAnswerQuestionsProjectIdAppIdPost(
    projectId: string,
    appId: string,
    requestBody: QuestionAnswers
  ): CancelablePromise<burr__examples__email_assistant__server__EmailAssistantState> {
    return __request(OpenAPI, {
      method: 'POST',
      url: '/api/v0/email_assistant/answer_questions/{project_id}/{app_id}',
      path: {
        project_id: projectId,
        app_id: appId
      },
      body: requestBody,
      mediaType: 'application/json',
      errors: {
        422: `Validation Error`
      }
    });
  }
  /**
   * Provide Feedback
   * Endpoint to provide feedback to the LLM
   *
   * :param project_id: ID of the project (used by telemetry tracking/storage)
   * :param app_id: ID of the application (used to reference the app)
   * :param feedback: Feedback to provide to the LLM
   * :return: The state of the application after providing feedback
   * @param projectId
   * @param appId
   * @param requestBody
   * @returns burr__examples__email_assistant__server__EmailAssistantState Successful Response
   * @throws ApiError
   */
  public static provideFeedbackApiV0EmailAssistantProvideFeedbackProjectIdAppIdPost(
    projectId: string,
    appId: string,
    requestBody: Feedback
  ): CancelablePromise<burr__examples__email_assistant__server__EmailAssistantState> {
    return __request(OpenAPI, {
      method: 'POST',
      url: '/api/v0/email_assistant/provide_feedback/{project_id}/{app_id}',
      path: {
        project_id: projectId,
        app_id: appId
      },
      body: requestBody,
      mediaType: 'application/json',
      errors: {
        422: `Validation Error`
      }
    });
  }
  /**
   * Get State
   * Get the current state of the application
   *
   * :param project_id: ID of the project (used by telemetry tracking/storage)
   * :param app_id:  ID of the application (used to reference the app)
   * :return: The state of the application
   * @param projectId
   * @param appId
   * @returns burr__examples__email_assistant__server__EmailAssistantState Successful Response
   * @throws ApiError
   */
  public static getStateApiV0EmailAssistantStateProjectIdAppIdGet(
    projectId: string,
    appId: string
  ): CancelablePromise<burr__examples__email_assistant__server__EmailAssistantState> {
    return __request(OpenAPI, {
      method: 'GET',
      url: '/api/v0/email_assistant/state/{project_id}/{app_id}',
      path: {
        project_id: projectId,
        app_id: appId
      },
      errors: {
        422: `Validation Error`
      }
    });
  }
  /**
   * Validate Environment
   * Validate the environment
   * @returns any Successful Response
   * @throws ApiError
   */
  public static validateEnvironmentApiV0EmailAssistantValidateProjectIdAppIdGet(): CancelablePromise<
    string | null
  > {
    return __request(OpenAPI, {
      method: 'GET',
      url: '/api/v0/email_assistant/validate/{project_id}/{app_id}'
    });
  }
  /**
   * Create New Application
   * @param projectId
   * @param appId
   * @returns string Successful Response
   * @throws ApiError
   */
  public static createNewApplicationApiV0EmailAssistantTypedCreateNewProjectIdAppIdPost(
    projectId: string,
    appId: string
  ): CancelablePromise<string> {
    return __request(OpenAPI, {
      method: 'POST',
      url: '/api/v0/email_assistant_typed/create_new/{project_id}/{app_id}',
      path: {
        project_id: projectId,
        app_id: appId
      },
      errors: {
        422: `Validation Error`
      }
    });
  }
  /**
   * Initialize Draft
   * Endpoint to initialize the draft with the email and instructions
   *
   * :param project_id: ID of the project (used by telemetry tracking/storage)
   * :param app_id: ID of the application (used to reference the app)
   * :param draft_data: Data to initialize the draft
   * :return: The state of the application after initialization
   * @param projectId
   * @param appId
   * @param requestBody
   * @returns AppResponse Successful Response
   * @throws ApiError
   */
  public static initializeDraftApiV0EmailAssistantTypedCreateProjectIdAppIdPost(
    projectId: string,
    appId: string,
    requestBody: DraftInit
  ): CancelablePromise<AppResponse> {
    return __request(OpenAPI, {
      method: 'POST',
      url: '/api/v0/email_assistant_typed/create/{project_id}/{app_id}',
      path: {
        project_id: projectId,
        app_id: appId
      },
      body: requestBody,
      mediaType: 'application/json',
      errors: {
        422: `Validation Error`
      }
    });
  }
  /**
   * Answer Questions
   * Endpoint to answer questions the LLM provides
   *
   * :param project_id: ID of the project (used by telemetry tracking/storage)
   * :param app_id: ID of the application (used to reference the app)
   * :param question_answers: Answers to the questions
   * :return: The state of the application after answering the questions
   * @param projectId
   * @param appId
   * @param requestBody
   * @returns AppResponse Successful Response
   * @throws ApiError
   */
  public static answerQuestionsApiV0EmailAssistantTypedAnswerQuestionsProjectIdAppIdPost(
    projectId: string,
    appId: string,
    requestBody: QuestionAnswers
  ): CancelablePromise<AppResponse> {
    return __request(OpenAPI, {
      method: 'POST',
      url: '/api/v0/email_assistant_typed/answer_questions/{project_id}/{app_id}',
      path: {
        project_id: projectId,
        app_id: appId
      },
      body: requestBody,
      mediaType: 'application/json',
      errors: {
        422: `Validation Error`
      }
    });
  }
  /**
   * Provide Feedback
   * Endpoint to provide feedback to the LLM
   *
   * :param project_id: ID of the project (used by telemetry tracking/storage)
   * :param app_id: ID of the application (used to reference the app)
   * :param feedback: Feedback to provide to the LLM
   * :return: The state of the application after providing feedback
   * @param projectId
   * @param appId
   * @param requestBody
   * @returns AppResponse Successful Response
   * @throws ApiError
   */
  public static provideFeedbackApiV0EmailAssistantTypedProvideFeedbackProjectIdAppIdPost(
    projectId: string,
    appId: string,
    requestBody: Feedback
  ): CancelablePromise<AppResponse> {
    return __request(OpenAPI, {
      method: 'POST',
      url: '/api/v0/email_assistant_typed/provide_feedback/{project_id}/{app_id}',
      path: {
        project_id: projectId,
        app_id: appId
      },
      body: requestBody,
      mediaType: 'application/json',
      errors: {
        422: `Validation Error`
      }
    });
  }
  /**
   * Get State
   * Get the current state of the application
   *
   * :param project_id: ID of the project (used by telemetry tracking/storage)
   * :param app_id:  ID of the application (used to reference the app)
   * :return: The state of the application
   * @param projectId
   * @param appId
   * @returns AppResponse Successful Response
   * @throws ApiError
   */
  public static getStateApiV0EmailAssistantTypedStateProjectIdAppIdGet(
    projectId: string,
    appId: string
  ): CancelablePromise<AppResponse> {
    return __request(OpenAPI, {
      method: 'GET',
      url: '/api/v0/email_assistant_typed/state/{project_id}/{app_id}',
      path: {
        project_id: projectId,
        app_id: appId
      },
      errors: {
        422: `Validation Error`
      }
    });
  }
  /**
   * Validate Environment
   * Validate the environment
   * @returns any Successful Response
   * @throws ApiError
   */
  public static validateEnvironmentApiV0EmailAssistantTypedValidateProjectIdAppIdGet(): CancelablePromise<
    string | null
  > {
    return __request(OpenAPI, {
      method: 'GET',
      url: '/api/v0/email_assistant_typed/validate/{project_id}/{app_id}'
    });
  }
  /**
   * Chat Response
   * Chat response endpoint. User passes in a prompt and the system returns the
   * full chat history, so its easier to render.
   *
   * :param project_id: Project ID to run
   * :param app_id: Application ID to run
   * :param prompt: Prompt to send to the chatbot
   * :return:
   * @param projectId
   * @param appId
   * @param requestBody
   * @returns any Successful Response
   * @throws ApiError
   */
  public static chatResponseApiV0StreamingChatbotResponseProjectIdAppIdPost(
    projectId: string,
    appId: string,
    requestBody: PromptInput
  ): CancelablePromise<any> {
    return __request(OpenAPI, {
      method: 'POST',
      url: '/api/v0/streaming_chatbot/response/{project_id}/{app_id}',
      path: {
        project_id: projectId,
        app_id: appId
      },
      body: requestBody,
      mediaType: 'application/json',
      errors: {
        422: `Validation Error`
      }
    });
  }
  /**
   * Chat History
   * Endpoint to get chat history. Gets the application and returns the chat history from state.
   *
   * :param project_id: Project ID
   * :param app_id: App ID.
   * :return: The list of chat items in the state
   * @param projectId
   * @param appId
   * @returns ChatItem Successful Response
   * @throws ApiError
   */
  public static chatHistoryApiV0StreamingChatbotHistoryProjectIdAppIdGet(
    projectId: string,
    appId: string
  ): CancelablePromise<Array<ChatItem>> {
    return __request(OpenAPI, {
      method: 'GET',
      url: '/api/v0/streaming_chatbot/history/{project_id}/{app_id}',
      path: {
        project_id: projectId,
        app_id: appId
      },
      errors: {
        422: `Validation Error`
      }
    });
  }
  /**
   * Create New Application
   * Endpoint to create a new application -- used by the FE when
   * the user types in a new App ID
   *
   * :param project_id: Project ID
   * :param app_id: App ID
   * :return: The app ID
   * @param projectId
   * @param appId
   * @returns string Successful Response
   * @throws ApiError
   */
  public static createNewApplicationApiV0StreamingChatbotCreateProjectIdAppIdPost(
    projectId: string,
    appId: string
  ): CancelablePromise<string> {
    return __request(OpenAPI, {
      method: 'POST',
      url: '/api/v0/streaming_chatbot/create/{project_id}/{app_id}',
      path: {
        project_id: projectId,
        app_id: appId
      },
      errors: {
        422: `Validation Error`
      }
    });
  }
  /**
   * React App
   * Quick trick to server the react app
   * Thanks to https://github.com/hop-along-polly/fastapi-webapp-react for the example/demo
   * @param restOfPath
   * @returns any Successful Response
   * @throws ApiError
   */
  public static reactAppRestOfPathGet(restOfPath: string): CancelablePromise<any> {
    return __request(OpenAPI, {
      method: 'GET',
      url: '/{rest_of_path}',
      path: {
        rest_of_path: restOfPath
      },
      errors: {
        422: `Validation Error`
      }
    });
  }
}
