import { AppView } from '../components/routes/app/AppView';

export const MiniTelemetry = (props: { projectId: string; appId: string | undefined }) => {
  //TODO -- put this upstream
  const { projectId, appId } = props;
  if (appId === undefined) {
    return <div></div>;
  }
  return (
    <AppView
      projectId={projectId}
      appId={appId}
      orientation="stacked_vertical"
      defaultAutoRefresh={true}
    />
  );
};
