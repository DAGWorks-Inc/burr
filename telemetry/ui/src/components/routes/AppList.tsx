import { useQuery } from 'react-query';
import { Navigate, useParams } from 'react-router';
import { Loading } from '../common/loading';
import { ApplicationSummary, DefaultService } from '../../api';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../common/table';
import { DateTimeDisplay } from '../common/dates';
import { useState } from 'react';
import { FunnelIcon, MinusIcon, PlusIcon } from '@heroicons/react/24/outline';
import { Link, useNavigate } from 'react-router-dom';
import { MdForkRight } from 'react-icons/md';
import { RiCornerDownRightLine } from 'react-icons/ri';

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

const isNullPartitionKey = (partitionKey: string | null) => {
  return partitionKey === null || partitionKey === '__none__';
};

const getForkID = (app: ApplicationSummary) => {
  if (app.parent_pointer) {
    return app.parent_pointer.app_id;
  } else {
    return null;
  }
};
/**
 * Sub-application list -- handles spaned applications.
 * This contains a list of applications that correspond to a parent application.
 * It is either an individual application or more when recursively applied
 * @param props
 * @returns
 */
const AppSubList = (props: {
  app: ApplicationSummary;
  navigate: (url: string) => void;
  projectId: string;
  spawningParentMap: Map<string, ApplicationSummary[]>;
  parentHovered?: boolean;
  depth?: number;
  displayPartitionKey: boolean;
}) => {
  const [subAppsExpanded, setSubAppsExpanded] = useState(false);

  const forkID = getForkID(props.app);
  const { app } = props;
  const ExpandIcon = subAppsExpanded ? MinusIcon : PlusIcon;

  const [isHovered, setIsHovered] = useState(true);
  const isHighlighted = props.parentHovered || isHovered;
  const depth = props.depth || 0;
  return (
    <>
      <TableRow
        onMouseEnter={() => {
          setIsHovered(true);
        }}
        onMouseLeave={() => {
          setIsHovered(false);
        }}
        key={props.app.app_id}
        className={`cursor-pointer ${isHighlighted ? 'bg-gray-50' : ''}`}
        onClick={() => {
          props.navigate(`/project/${props.projectId}/${app.partition_key}/${app.app_id}`);
        }}
      >
        {props.displayPartitionKey && (
          <TableCell className="text-gray-600 font-sans">
            {isNullPartitionKey(app.partition_key) ? (
              <></>
            ) : (
              <Link
                to={`/project/${props.projectId}/${app.partition_key}`}
                className="hover:underline"
                onClick={(e) => {
                  props.navigate(`/project/${props.projectId}/${app.partition_key}`);
                  e.stopPropagation();
                }}
              >
                {app.partition_key}
              </Link>
            )}
          </TableCell>
        )}
        <TableCell className="font-semibold text-gray-700">
          <div className="flex flex-row gap-1 items-center md:min-w-[21rem] md:max-w-none max-w-24">
            {[...Array(depth).keys()].map((i) => (
              <RiCornerDownRightLine
                key={i}
                className={`${i === depth - 1 ? 'opacity-100' : 'opacity-0'} text-lg text-gray-600`}
              ></RiCornerDownRightLine>
            ))}
            {app.app_id}
          </div>
        </TableCell>
        <TableCell>
          <DateTimeDisplay date={app.last_written} mode="long" />
        </TableCell>
        <TableCell className="z-50">
          {forkID ? (
            <MdForkRight
              className=" hover:scale-125 h-5 w-5 text-gray-600 "
              onClick={(e) => {
                props.navigate(`/project/${props.projectId}/${forkID}`);
                e.stopPropagation();
              }}
            />
          ) : (
            <></>
          )}
        </TableCell>
        <TableCell>
          {props.spawningParentMap.has(props.app.app_id) ? (
            <div className="flex flex-row items-center gap-1">
              <ExpandIcon
                className="h-4 w-4 text-gray-600 hover:scale-110 cursor-pointer"
                onClick={(e) => {
                  setSubAppsExpanded(!subAppsExpanded);
                  e.stopPropagation();
                }}
              />
              <span className="text-gray-600">
                ({props.spawningParentMap.get(props.app.app_id)?.length})
              </span>
            </div>
          ) : (
            <></>
          )}
        </TableCell>
        <TableCell className="text-gray-600">{app.num_steps}</TableCell>
      </TableRow>
      {props.spawningParentMap.has(props.app.app_id) && subAppsExpanded
        ? props.spawningParentMap.get(props.app.app_id)?.map((subApp) => {
            return (
              <AppSubList
                key={subApp.app_id}
                displayPartitionKey={props.displayPartitionKey}
                app={subApp}
                navigate={props.navigate}
                projectId={props.projectId}
                spawningParentMap={props.spawningParentMap}
                parentHovered={isHighlighted}
                depth={depth + 1}
              />
            );
          })
        : null}
    </>
  );
};
/**
 * List of applications. Purely rendering a list, also sorts them.
 */
export const AppListTable = (props: { apps: ApplicationSummary[]; projectId: string }) => {
  const appsCopy = [...props.apps];
  const [displayZeroCount, setDisplayZeroCount] = useState(true);
  const navigate = useNavigate();
  const appsToDisplay = appsCopy
    .sort((a, b) => {
      return new Date(a.last_written) > new Date(b.last_written) ? -1 : 1;
    })
    .filter((app) => {
      return app.num_steps > 0 || displayZeroCount;
    });

  // Maps from parents -> children
  const spawningParentMap = appsToDisplay.reduce((acc, app) => {
    if (app.spawning_parent_pointer) {
      if (acc.has(app.spawning_parent_pointer.app_id)) {
        acc.get(app.spawning_parent_pointer.app_id)!.push(app);
      } else {
        acc.set(app.spawning_parent_pointer.app_id, [app]);
      }
    }
    return acc;
  }, new Map<string, ApplicationSummary[]>());

  // Display the parents no matter what
  const rootAppsToDisplay = appsToDisplay.filter((app) => app.spawning_parent_pointer === null);
  const anyHavePartitionKey = rootAppsToDisplay.some(
    (app) => !isNullPartitionKey(app.partition_key)
  );

  return (
    <Table dense={1}>
      <TableHead>
        <TableRow>
          {anyHavePartitionKey && <TableHeader>Partition Key</TableHeader>}
          <TableHeader>ID</TableHeader>
          <TableHeader>Last Run</TableHeader>
          <TableHeader>Forked</TableHeader>
          <TableHeader>Sub Apps</TableHeader>
          <TableHeader>
            <StepCountHeader
              displayZeroCount={displayZeroCount}
              setDisplayZeroCount={setDisplayZeroCount}
            />
          </TableHeader>
        </TableRow>
      </TableHead>
      <TableBody>
        {rootAppsToDisplay.map((app) => {
          return (
            <AppSubList
              key={app.app_id}
              app={app}
              projectId={props.projectId}
              navigate={navigate}
              spawningParentMap={spawningParentMap}
              displayPartitionKey={anyHavePartitionKey}
            />
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
  const { projectId, partitionKey } = useParams();
  const { data, error } = useQuery(
    ['apps', projectId, partitionKey],
    () =>
      DefaultService.getAppsApiV0ProjectIdPartitionKeyAppsGet(
        projectId as string,
        partitionKey ? partitionKey : '__none__'
      ),
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
