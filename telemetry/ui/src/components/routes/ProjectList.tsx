import { useQuery } from 'react-query';
import { DefaultService, Project } from '../../api';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../common/table';
import { Loading } from '../common/loading';
import { DateDisplay } from '../common/dates';
import { Button } from '../common/button';

/**
 * Table of a project list. Uses the tailwind catalyst component.
 * This does not load or fetch any data, just renders it
 */
export const ProjectListTable = (props: { projects: Project[] }) => {
  const projectsCopy = [...props.projects];
  const projectsSorted = projectsCopy.sort((a, b) => {
    return a.last_written > b.last_written ? -1 : 1;
  });
  return (
    <Table>
      <TableHead>
        <TableRow>
          <TableHeader>Name</TableHeader>
          <TableHeader>Created</TableHeader>
          <TableHeader>Last Run</TableHeader>
          <TableHeader>App Runs</TableHeader>
          <TableHeader>Path</TableHeader>
          <TableHeader></TableHeader>
        </TableRow>
      </TableHead>
      <TableBody>
        {projectsSorted.map((project) => (
          <TableRow key={project.id}>
            <TableCell className="font-semibold text-gray-700">{project.name}</TableCell>
            <TableCell>
              <DateDisplay date={project.created} />
            </TableCell>
            <TableCell>
              <DateDisplay date={project.last_written} />
            </TableCell>
            <TableCell>{project.num_apps}</TableCell>
            <TableCell>
              <code className="text-gray-600">{project.uri}</code>
            </TableCell>
            <TableCell>
              <Button color="white" href={`/project/${project.id}`}>
                App Runs
              </Button>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
};

/**
 * Container for the table -- fetches the data and passes it to the table
 */
export const ProjectList = () => {
  const { data, error } = useQuery('projects', DefaultService.getProjectsApiV0ProjectsGet);
  if (error) return <div>Error loading projects</div>;
  if (data === undefined) return <Loading />;
  return (
    <div className="">
      <ProjectListTable projects={data} />
    </div>
  );
};
