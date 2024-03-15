import { Link } from 'react-router-dom';

export const Counter = () => {
  return (
    <div className="flex justify-center items-center h-full w-full">
      <p className="text-gray-700">
        {' '}
        This is a WIP! Please check back soon or comment/vote/contribute at the{' '}
        <Link
          className="hover:underline text-dwlightblue"
          to="https://github.com/DAGWorks-Inc/burr/issues/69"
        >
          github issue
        </Link>
        .
      </p>
    </div>
  );
};
