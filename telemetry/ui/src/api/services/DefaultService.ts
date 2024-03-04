/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ApplicationLogs } from '../models/ApplicationLogs';
import type { ApplicationSummary } from '../models/ApplicationSummary';
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
            url: '/api/v0/projects',
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
        projectId: string,
    ): CancelablePromise<Array<ApplicationSummary>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v0/{project_id}/apps',
            path: {
                'project_id': projectId,
            },
            errors: {
                422: `Validation Error`,
            },
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
        appId: string,
    ): CancelablePromise<ApplicationLogs> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v0/{project_id}/{app_id}/apps',
            path: {
                'project_id': projectId,
                'app_id': appId,
            },
            errors: {
                422: `Validation Error`,
            },
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
            url: '/api/v0/ready',
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
    public static reactAppRestOfPathGet(
        restOfPath: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/{rest_of_path}',
            path: {
                'rest_of_path': restOfPath,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
