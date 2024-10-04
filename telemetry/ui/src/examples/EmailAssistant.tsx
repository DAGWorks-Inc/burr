import { TwoColumnLayout } from '../components/common/layout';
import { MiniTelemetry } from './MiniTelemetry';
import {
  ApplicationSummary,
  DefaultService,
  DraftInit,
  // examples__fastapi__application__EmailAssistantState as EmailAssistantState,
  AppResponse,
  Feedback,
  QuestionAnswers,
  Email
} from '../api';
import { useEffect, useState } from 'react';
import { useMutation, useQuery } from 'react-query';
import { Loading } from '../components/common/loading';
import { Field, Label } from '../components/common/fieldset';
import { Textarea } from '../components/common/textarea';
import { Input } from '../components/common/input';
import { Text } from '../components/common/text';
import { Button } from '../components/common/button';
import { DateTimeDisplay } from '../components/common/dates';
import AsyncCreatableSelect from 'react-select/async-creatable';

export const InitialDraftView = (props: {
  submitInitial: (initial: DraftInit) => void;
  isLoading: boolean;
  responseInstructions: string | null;
  emailToRespond: string | null;
}) => {
  const [userProvidedEmailToRespond, setUserProvidedEmailToRespond] = useState<string>(
    props.emailToRespond || ''
  );
  const [userProvidedResponseInstructions, setUserProvidedResponseInstructions] = useState<string>(
    props.responseInstructions || ''
  );
  const editMode = props.emailToRespond === null;

  return (
    <div className="w-full flex flex-col gap-2">
      <Field>
        <Label>Email to respond to</Label>
        <Textarea
          name="email_to_respond"
          value={userProvidedEmailToRespond}
          onChange={(e) => {
            setUserProvidedEmailToRespond(e.target.value);
          }}
          disabled={!editMode}
        />
      </Field>
      <Field>
        <Label>Response Instructions</Label>
        <Input
          name="response_instructions"
          value={userProvidedResponseInstructions}
          onChange={(e) => {
            setUserProvidedResponseInstructions(e.target.value);
          }}
          disabled={!editMode}
        />
      </Field>
      {editMode && (
        <Button
          color="white"
          className="cursor-pointer w-full"
          disabled={props.isLoading}
          onClick={() =>
            props.submitInitial({
              email_to_respond: userProvidedEmailToRespond,
              response_instructions: userProvidedResponseInstructions
            })
          }
        >
          {'Submit'}
        </Button>
      )}
    </div>
  );
};

export const SubmitAnswersView = (props: {
  state: AppResponse;
  submitAnswers: (questions: QuestionAnswers) => void;
  questions: string[] | null;
  answers: string[] | null;
  isLoading: boolean;
}) => {
  const questions = props.state.state.questions?.question || [];
  const [answers, setAnswers] = useState<string[]>(props.answers || questions.map(() => ''));
  const editMode = props.isLoading || props.answers === null;
  const { state } = props.state;
  return (
    <div className="w-full flex flex-col gap-2">
      <div className="flex flex-col gap-2">
        {(state.questions?.question || []).map((question, index) => {
          return (
            <Field key={index}>
              <Label>{question}</Label>
              <Input
                disabled={!editMode}
                value={answers[index]}
                onChange={(e) => {
                  const newAnswers = [...answers];
                  newAnswers[index] = e.target.value;
                  setAnswers(newAnswers);
                }}
              />
            </Field>
          );
        })}
      </div>
      {editMode && (
        <Button
          color="white"
          className="cursor-pointer w-full"
          disabled={props.isLoading}
          onClick={() => props.submitAnswers({ answers: answers })}
        >
          {'Submit'}
        </Button>
      )}
    </div>
  );
};

export const SubmitFeedbackView = (props: {
  state: AppResponse;
  submitFeedback: (feedbacks: Feedback) => void;
  drafts: Email[] | null;
  feedbacks: string[] | null;
  isLoading: boolean;
}) => {
  const editMode = props.feedbacks === null || props.feedbacks.length !== props.drafts?.length; // if its not equal we are one step behind
  const [feedback, setFeedback] = useState<string>(props.feedbacks?.[-1] || '');
  return (
    <div className="w-full flex flex-col gap-2">
      <Field>
        <Label className="text-lg font-bold text-gray-600">Drafts</Label>
      </Field>
      <div className="flex flex-col gap-2">
        {(props.drafts || []).map((draft, index) => {
          const providedFeedback = props.feedbacks?.[index];
          return (
            <>
              <Text>
                <pre className="whitespace-pre-wrap text-xs" key={index}>
                  {draft.subject + '\n' + draft.contents || ''}
                </pre>
              </Text>
              <h3 className="text-sm font-semibold text-gray-600"></h3>
              <Input
                disabled={!editMode || props.isLoading || index !== (props.drafts || []).length - 1}
                placeholder="Provide feedback here..."
                value={providedFeedback || feedback}
                onChange={(e) => {
                  setFeedback(e.target.value);
                }}
              />
            </>
          );
        })}
        {editMode && (
          <div className="flex flex-row gap-1">
            <Button
              color="white"
              className="cursor-pointer w-full"
              disabled={props.isLoading}
              onClick={() => {
                props.submitFeedback({ feedback: feedback }), setFeedback('');
              }}
            >
              {'Submit Feedback'}
            </Button>
            <Button
              color="white"
              className="cursor-pointer w-full"
              disabled={props.isLoading}
              onClick={() => props.submitFeedback({ feedback: '' })}
            >
              {'Looks good!'}
            </Button>
          </div>
        )}
      </div>
    </div>
  );
};

export const EmailAssistant = (props: { projectId: string; appId: string | undefined }) => {
  // starts off as null
  const [appResponse, setAppResponse] = useState<AppResponse | null>(null);
  const { data: validationData, isLoading: isValidationLoading } = useQuery(
    ['valid', props.projectId, props.appId],
    DefaultService.validateEnvironmentApiV0EmailAssistantTypedValidateProjectIdAppIdGet
  );

  useEffect(() => {
    if (props.appId !== undefined) {
      // TODO -- handle errors
      DefaultService.getStateApiV0EmailAssistantTypedStateProjectIdAppIdGet(
        props.projectId,
        props.appId
      )
        .then((data) => {
          setAppResponse(data); // we want to initialize the chat history
        })
        .catch((e) => {
          // eslint-disable-next-line
          console.error(e); // TODO -- handle errors
        });
    }
  }, [props.appId, props.projectId]); // This will only get called when the appID or projectID changes, which will be at the beginning

  const { isLoading: isGetInitialStateLoading } = useQuery(
    // TODO -- handle errors
    ['emailAssistant', props.projectId, props.appId],
    () =>
      DefaultService.getStateApiV0EmailAssistantTypedStateProjectIdAppIdGet(
        props.projectId,
        props.appId || '' // TODO -- find a cleaner way of doing a skip-token like thing here
        // This is skipped if the appId is undefined so this is just to make the type-checker happy
      ),
    {
      enabled: props.appId !== undefined,
      onSuccess: (data) => {
        setAppResponse(data); // when its succesful we want to set the displayed chat history
      }
    }
  );

  const submitInitialMutation = useMutation(
    (draftData: DraftInit) =>
      DefaultService.initializeDraftApiV0EmailAssistantTypedCreateProjectIdAppIdPost(
        props.projectId,
        props.appId || 'create_new',
        draftData
      ),
    {
      onSuccess: (data) => {
        setAppResponse(data);
      }
    }
  );

  const submitAnswersMutation = useMutation(
    (answers: QuestionAnswers) =>
      DefaultService.answerQuestionsApiV0EmailAssistantTypedAnswerQuestionsProjectIdAppIdPost(
        props.projectId,
        props.appId || '',
        answers
      ),
    {
      onSuccess: (data) => {
        setAppResponse(data);
      }
    }
  );
  const submitFeedbackMutation = useMutation(
    (feedbacks: Feedback) =>
      DefaultService.provideFeedbackApiV0EmailAssistantTypedProvideFeedbackProjectIdAppIdPost(
        props.projectId,
        props.appId || '',
        feedbacks
      ),
    {
      onSuccess: (data) => {
        setAppResponse(data);
      }
    }
  );

  const isLoading = isGetInitialStateLoading;
  const anyMutationLoading =
    submitInitialMutation.isLoading ||
    submitAnswersMutation.isLoading ||
    submitFeedbackMutation.isLoading;

  if (isLoading || isValidationLoading) {
    return <Loading />;
  }
  const displayValidationError = validationData !== null;
  const displayInstructions = appResponse === null && !displayValidationError;
  const displayInitialDraft = appResponse !== null;
  const displaySubmitAnswers = displayInitialDraft && appResponse.next_step !== 'process_input';
  const displaySubmitFeedback =
    displaySubmitAnswers && appResponse.next_step !== 'clarify_instructions';
  const displayFinalDraft = displaySubmitFeedback && appResponse.next_step === null;
  return (
    <div className="px-4 bg-white  w-full flex flex-col  h-full gap-5 overflow-y-scroll">
      <h1 className="text-2xl font-bold  text-gray-600">{'Learn Burr '}</h1>
      <h2 className="text-lg font-normal text-gray-500 flex flex-row">
        The email assistant below is implemented using Burr. Copy/paste the email you want to
        respond to and provide directions, it will ask you questions, generate a response, and
        adjust for your feedback.
      </h2>
      <div className="flex flex-col">
        {displayInstructions && (
          <p className="text-lg font-normal text-gray-500">
            Please click &apos;create new&apos; on the right to get started!
          </p>
        )}
        {displayValidationError && (
          <p className="text-lg font-normal text-dwred">{validationData}</p>
        )}
        {displayInitialDraft && (
          <InitialDraftView
            isLoading={anyMutationLoading}
            submitInitial={(initial) => {
              submitInitialMutation.mutate(initial);
            }}
            responseInstructions={appResponse.state?.response_instructions || null}
            emailToRespond={appResponse.state?.email_to_respond || null}
          />
        )}
      </div>
      {displaySubmitAnswers && (
        <SubmitAnswersView
          state={appResponse}
          submitAnswers={(answers) => {
            submitAnswersMutation.mutate(answers);
          }}
          questions={appResponse.state.questions?.question || null}
          answers={appResponse.state.answers?.answers || null}
          isLoading={anyMutationLoading}
        />
      )}
      {displaySubmitFeedback && (
        <SubmitFeedbackView
          state={appResponse}
          submitFeedback={(feedbacks) => {
            submitFeedbackMutation.mutate(feedbacks);
          }}
          drafts={appResponse.state.draft_history || null}
          feedbacks={appResponse.state.feedback_history || null}
          isLoading={anyMutationLoading}
        />
      )}
      {displayFinalDraft && (
        <div className="flex flex-col gap-2">
          <h2 className="text-lg font-bold text-gray-600">Final Draft</h2>
          <Text>
            <pre className="whitespace-pre-wrap text-xs">
              {appResponse.state.current_draft?.subject +
                '\n' +
                appResponse.state.current_draft?.contents || ''}
            </pre>
          </Text>
        </div>
      )}
    </div>
  );
};

export const TelemetryWithSelector = (props: {
  projectId: string;
  currentApp: ApplicationSummary | undefined;
  setCurrentApp: (app: ApplicationSummary) => void;
}) => {
  return (
    <div className="w-full h-[90%]">
      <div className="w-full">
        <EmailAssistantAppSelector
          projectId={props.projectId}
          setApp={props.setCurrentApp}
          currentApp={props.currentApp}
          placeholder={'Select a conversation or create a new one by typing...'}
        ></EmailAssistantAppSelector>
      </div>
      <MiniTelemetry projectId={props.projectId} appId={props.currentApp?.app_id}></MiniTelemetry>
    </div>
  );
};

const EmailAssistantLabel = (props: { application: ApplicationSummary }) => {
  return (
    <div className="flex flex-row gap-2 items-center justify-between">
      <div className="flex flex-row gap-2 items-center">
        <span className="text-gray-400 w-10">{props.application.num_steps}</span>
        <span>{props.application.app_id}</span>
      </div>
      <DateTimeDisplay date={props.application.first_written} mode="short" />
    </div>
  );
};

export const EmailAssistantAppSelector = (props: {
  projectId: string;
  setApp: (app: ApplicationSummary) => void;
  currentApp: ApplicationSummary | undefined;
  placeholder: string;
}) => {
  const { projectId, setApp } = props;
  const { data, refetch } = useQuery(
    ['apps', projectId],
    () => DefaultService.getAppsApiV0ProjectIdPartitionKeyAppsGet(projectId as string, '__none__'),
    { enabled: projectId !== undefined }
  );
  const createAndUpdateMutation = useMutation(
    (app_id: string) =>
      DefaultService.createNewApplicationApiV0EmailAssistantCreateNewProjectIdAppIdPost(
        projectId,
        app_id
      ),
    {
      onSuccess: (appID) => {
        refetch().then((data) => {
          const appSummaries = data.data?.applications || [];
          const app = appSummaries.find((app) => app.app_id === appID);
          if (app) {
            setApp(app);
          }
        });
      }
    }
  );
  const appSetter = (appID: string) => createAndUpdateMutation.mutate(appID);
  const dataOrEmpty = Array.from(data?.applications || []);
  const options = dataOrEmpty
    .sort((a, b) => {
      return new Date(a.last_written) > new Date(b.last_written) ? -1 : 1;
    })
    .map((app) => {
      return {
        value: app.app_id,
        label: <EmailAssistantLabel application={app} />
      };
    });
  return (
    <AsyncCreatableSelect
      placeholder={props.placeholder}
      cacheOptions
      defaultOptions={options}
      onCreateOption={appSetter}
      value={options.find((option) => option.value === props.currentApp?.app_id) || null}
      onChange={(choice) => {
        const app = dataOrEmpty.find((app) => app.app_id === choice?.value);
        if (app) {
          setApp(app);
        }
      }}
    />
  );
};

export const EmailAssistantWithTelemetry = () => {
  const currentProject = 'demo_email-assistant';
  const [currentApp, setCurrentApp] = useState<ApplicationSummary | undefined>(undefined);

  return (
    <TwoColumnLayout
      firstItem={<EmailAssistant projectId={currentProject} appId={currentApp?.app_id} />}
      secondItem={
        <TelemetryWithSelector
          projectId={currentProject}
          currentApp={currentApp}
          setCurrentApp={setCurrentApp}
        />
      }
      mode={'third'}
    ></TwoColumnLayout>
  );
};
