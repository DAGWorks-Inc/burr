import { useQuery, useMutation } from 'react-query';
import { ApplicationSummary, DefaultService } from '../api';
import AsyncCreatableSelect from 'react-select/async-creatable';
import { DateTimeDisplay } from '../components/common/dates';

const Label = (props: { application: ApplicationSummary }) => {
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
export const AppSelector = (props: {
  projectId: string;
  setApp: (app: ApplicationSummary) => void;
  currentApp: ApplicationSummary | undefined;
}) => {
  const { projectId, setApp } = props;
  const { data, refetch } = useQuery(
    ['apps', projectId],
    () => DefaultService.getAppsApiV0ProjectIdAppsGet(projectId as string),
    { enabled: projectId !== undefined }
  );
  const createAndUpdateMutation = useMutation(
    (app_id: string) =>
      DefaultService.createNewApplicationApiV0ChatbotProjectIdAppIdCreatePost(projectId, app_id),
    {
      onSuccess: (appID) => {
        refetch().then((data) => {
          const appSummaries = data.data || [];
          const app = appSummaries.find((app) => app.app_id === appID);
          if (app) {
            setApp(app);
          }
        });
      }
    }
  );
  const dataOrEmpty = Array.from(data || []);
  const options = dataOrEmpty
    .sort((a, b) => {
      return new Date(a.last_written) > new Date(b.last_written) ? -1 : 1;
    })
    .map((app) => {
      return {
        value: app.app_id,
        label: <Label application={app} />
      };
    });
  return (
    <AsyncCreatableSelect
      placeholder="Select a conversation to view telemetry and interact or create a new one by typing..."
      cacheOptions
      defaultOptions={options}
      onCreateOption={(inputValue) => {
        createAndUpdateMutation.mutate(inputValue);
      }}
      value={options.find((option) => option.value === props.currentApp?.app_id) || null}
      // options={options}
      // isLoading={isLoading || isRefetching || createAndUpdateMutation.isLoading}
      onChange={(choice) => {
        const app = dataOrEmpty.find((app) => app.app_id === choice?.value);
        if (app) {
          setApp(app);
        }
      }}
      // onCreateOption={(inputValue) => {
      //   setApp({
      //     app_id: inputValue,
      //     first_written: new Date().toISOString(),
      //     last_written: new Date().toISOString(),
      //     num_steps: 0,
      //     tags: {}
      //   });
      //   createAndUpdateMutation.mutate(inputValue);
      // }}
      // onCreateOption={(inputValue) => {
      //   const newApp: ApplicationSummary = {
      //     app_id: inputValue,
      //     first_written: new Date().toISOString(),
      //     last_written: new Date().toISOString(),
      //     num_steps: 0,
      //     tags: {}
      //   };
      //   setApp(newApp);
      //   refetch().then(() => {
      //     setApp(newApp);
      //   });
      // }}
    />
  );
};
