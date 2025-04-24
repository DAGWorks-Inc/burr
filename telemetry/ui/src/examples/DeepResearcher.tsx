import { useState } from 'react';
import { ApplicationSummary, DefaultService } from '../api';
import { TwoColumnLayout } from '../components/common/layout';
import { TelemetryWithSelector } from './Common';

export const DeepResearcherWithTelemetry = () => {
  const currentProject = 'demo_deep_researcher';
  const [currentApp, setCurrentApp] = useState<ApplicationSummary | undefined>(undefined);

  return (
    <TwoColumnLayout
      firstItem={<DeepResearcher projectId={currentProject} appId={currentApp?.app_id} />}
      secondItem={
        <TelemetryWithSelector
          projectId={currentProject}
          currentApp={currentApp}
          setCurrentApp={setCurrentApp}
          createNewApp={
            DefaultService.createNewApplicationApiV0DeepResearcherCreateProjectIdAppIdPost
          }
        />
      }
      mode={'third'}
    ></TwoColumnLayout>
  );
};
