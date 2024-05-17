import { useQuery } from 'react-query';
import { Navigate, useParams } from 'react-router';
import { Loading } from '../common/loading';
import { ApplicationSummary, DefaultService } from '../../api';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../common/table';
import { DateTimeDisplay } from '../common/dates';
import { useState } from 'react';
import { FunnelIcon } from '@heroicons/react/24/outline';
import { useNavigate } from 'react-router-dom';
import { MdForkRight } from 'react-icons/md';

const StepCountHeader = (props: {
  displayZeroCount: boolean;
  setDisplayZeroCount: (displayZeroCount: boolean) => void;
}) => {
  const fillColor = props.displayZeroCount ? 'fill-gray-300' : 'fill-gray-700';
  const borderColor = props.displayZeroCount ? 'text-gray-300' : 'text-gray-700';
  return (
    <div className="flex flex-row items-center gap-1">
      <FunnelIcon
        className={`h-5 w-5 hover:scale-125 cursor-pointer ${fillColor} ${borderColor}`}
        onClick={() => {
          props.setDisplayZeroCount(!props.displayZeroCount);
        }}
      />
      <span>Seq ID</span>
    </div>
  );
};

const getForkID = (app: ApplicationSummary) => {
  if (app.parent_pointer) {
    return app.parent_pointer.app_id;
  } else {
    return null;
  }
};

/**
 * List of applications. Purely rendering a list, also sorts them.
 */
export const AppListTable = (props: { apps: ApplicationSummary[]; projectId: string }) => {
  const appsCopy = [...props.apps];
  const [displayZeroCount, setDisplayZeroCount] = useState(false);
  const navigate = useNavigate();
  const appsToDisplay = appsCopy
    .sort((a, b) => {
      return new Date(a.last_written) > new Date(b.last_written) ? -1 : 1;
    })
    .filter((app) => {
      return app.num_steps > 0 || displayZeroCount;
    });
  return (
    <Table>
      <TableHead>
        <TableRow>
          <TableHeader>Partition Key</TableHeader>
          <TableHeader>ID</TableHeader>
          <TableHeader>First Seen</TableHeader>
          <TableHeader>Last Run</TableHeader>
          <TableHeader>Forked</TableHeader>
          <TableHeader>
            <StepCountHeader
              displayZeroCount={displayZeroCount}
              setDisplayZeroCount={setDisplayZeroCount}
            />
          </TableHeader>
          <TableHeader></TableHeader>
          <TableHeader></TableHeader>
        </TableRow>
      </TableHead>
      <TableBody>
        {appsToDisplay.map((app) => {
          const forkID = getForkID(app);
          return (
            <TableRow
              key={app.app_id}
              className="hover:bg-gray-50 cursor-pointer"
              onClick={() => {
                navigate(`/project/${props.projectId}/${app.app_id}`);
              }}
            >
              <TableCell className="text-gray-600 font-sans">{app.partition_key}</TableCell>
              <TableCell className="font-semibold text-gray-700">{app.app_id}</TableCell>
              <TableCell>
                <DateTimeDisplay date={app.first_written} mode="long" />
              </TableCell>
              <TableCell>
                <DateTimeDisplay date={app.last_written} mode="long" />
              </TableCell>
              <TableCell className="z-50">
                {forkID ? (
                  <MdForkRight
                    className=" hover:scale-125 h-5 w-5 text-gray-600 "
                    onClick={(e) => {
                      navigate(`/project/${props.projectId}/${forkID}`);
                      e.stopPropagation();
                    }}
                  />
                ) : (
                  <></>
                )}
              </TableCell>
              <TableCell>{app.num_steps}</TableCell>
            </TableRow>
          );
        })}
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
