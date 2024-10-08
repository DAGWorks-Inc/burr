import { AppView } from '../components/routes/app/AppView';

export const MiniTelemetry = (props: {
  projectId: string;
  partitionKey: string | null;
  appId: string | undefined;
}) => {
  //TODO -- put this upstream
  const { projectId, appId, partitionKey } = props;
  if (appId === undefined) {
    return <div></div>;
  }
  return (
    <AppView
      projectId={projectId}
      appId={appId}
      orientation="stacked_vertical"
      defaultAutoRefresh={true}
      enableFullScreenStepView={false}
      enableMinimizedStepView={false}
      allowAnnotations={false}
      partitionKey={partitionKey === 'null' ? null : partitionKey}
    />
  );
};
