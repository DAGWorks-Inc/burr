import { useQuery } from 'react-query';
import { Navigate, useParams } from 'react-router';
import { Loading } from '../common/loading';
import { ApplicationSummary, DefaultService } from '../../api';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../common/table';
import { DateTimeDisplay } from '../common/dates';
import { Button } from '../common/button';

/**
 * List of applications. Purely rendering a list, also sorts them.
 */
export const AppListTable = (props: { apps: ApplicationSummary[]; projectId: string }) => {
  const appsCopy = [...props.apps];
  const appsSorted = appsCopy.sort((a, b) => {
    return new Date(a.last_written) > new Date(b.last_written) ? -1 : 1;
  });
  return (
    <Table>
      <TableHead>
        <TableRow>
          <TableHeader>ID</TableHeader>
          <TableHeader>First Seen</TableHeader>
          <TableHeader>Last Run</TableHeader>
          <TableHeader>Step Count</TableHeader>
          <TableHeader></TableHeader>
          <TableHeader></TableHeader>
        </TableRow>
      </TableHead>
      <TableBody>
        {appsSorted.map((app) => (
          <TableRow key={app.app_id}>
            <TableCell className="font-semibold text-gray-700">{app.app_id}</TableCell>
            <TableCell>
              <DateTimeDisplay date={app.first_written} mode="long" />
            </TableCell>
            <TableCell>
              <DateTimeDisplay date={app.last_written} mode="long" />
            </TableCell>
            <TableCell>{app.num_steps}</TableCell>
            <TableCell>
              <Button color="white" href={`/project/${props.projectId}/${app.app_id}`}>
                Steps
              </Button>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
};

/**
 * List of applications. This fetches data from the BE and passes it to the table
 */
export const AppList = () => {
  const { projectId } = useParams();
  const { data, error } = useQuery(
    ['apps', projectId],
    () => DefaultService.getAppsApiV0ProjectIdAppsGet(projectId as string),
    { enabled: projectId !== undefined }
  );
  if (projectId === undefined) {
    return <Navigate to={'/projects'} />;
  }

  if (error) return <div>Error loading projects</div>;
  if (data === undefined) return <Loading />;
  return (
    <div className="">
      <AppListTable apps={data} projectId={projectId} />
    </div>
  );
};
