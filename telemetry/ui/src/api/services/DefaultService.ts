/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ApplicationLogs } from '../models/ApplicationLogs';
import type { ApplicationSummary } from '../models/ApplicationSummary';
import type { ChatItem } from '../models/ChatItem';
import type { Project } from '../models/Project';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class DefaultService {
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
   * @returns ApplicationSummary Successful Response
   * @throws ApiError
   */
  public static getAppsApiV0ProjectIdAppsGet(
    projectId: string
  ): CancelablePromise<Array<ApplicationSummary>> {
    return __request(OpenAPI, {
      method: 'GET',
      url: '/api/v0/{project_id}/apps',
      path: {
        project_id: projectId
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
   * :param app_id: ID of the associated application
   * :return: A list of steps with all associated step data
   * @param projectId
   * @param appId
   * @returns ApplicationLogs Successful Response
   * @throws ApiError
   */
  public static getApplicationLogsApiV0ProjectIdAppIdAppsGet(
    projectId: string,
    appId: string
  ): CancelablePromise<ApplicationLogs> {
    return __request(OpenAPI, {
      method: 'GET',
      url: '/api/v0/{project_id}/{app_id}/apps',
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
   * Chat Response
   * Chat response endpoint.
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
  public static chatResponseApiV0ChatbotProjectIdAppIdResponsePost(
    projectId: string,
    appId: string,
    prompt: string
  ): CancelablePromise<Array<ChatItem>> {
    return __request(OpenAPI, {
      method: 'POST',
      url: '/api/v0/chatbot/{project_id}/{app_id}/response',
      path: {
        project_id: projectId,
        app_id: appId
      },
      query: {
        prompt: prompt
      },
      errors: {
        422: `Validation Error`
      }
    });
  }
  /**
   * Chat History
   * @param projectId
   * @param appId
   * @returns ChatItem Successful Response
   * @throws ApiError
   */
  public static chatHistoryApiV0ChatbotProjectIdAppIdHistoryGet(
    projectId: string,
    appId: string
  ): CancelablePromise<Array<ChatItem>> {
    return __request(OpenAPI, {
      method: 'GET',
      url: '/api/v0/chatbot/{project_id}/{app_id}/history',
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
   * Quick helper to create a new application. Just returns true, you'll want to fetch afterwards.
   * In a better chatbot you'd want to either have the frontend store this and create on demand or return
   * the actual application model
   * @param projectId
   * @param appId
   * @returns string Successful Response
   * @throws ApiError
   */
  public static createNewApplicationApiV0ChatbotProjectIdAppIdCreatePost(
    projectId: string,
    appId: string
  ): CancelablePromise<string> {
    return __request(OpenAPI, {
      method: 'POST',
      url: '/api/v0/chatbot/{project_id}/{app_id}/create',
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
