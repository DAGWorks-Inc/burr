import { HomeIcon } from '@heroicons/react/20/solid';
import { useLocation } from 'react-router-dom';

/**
 * Breadcrumb component
 * This isn't perfect as not all the sub-routes map to a name
 * (and you can click on any of them), but it works for now,
 * and no routes lead to nothing (the /project route leads
 * to /projects, which is the default...)
 */
export const BreadCrumb = () => {
  const location = useLocation();
  const pathnames = location.pathname.split('/').filter((x) => x);

  const pages = pathnames.map((value, index) => {
    const href = `/${pathnames.slice(0, index + 1).join('/')}`;
    const isCurrentPage = index === pathnames.length - 1;
    return {
      name: value,
      href,
      current: isCurrentPage
    };
  });
  {
    return (
      <nav className="flex" aria-label="Breadcrumb">
        <ol role="list" className="flex items-center space-x-4">
          <li>
            <div>
              <a href="/" className="text-gray-400 hover:text-gray-500">
                <HomeIcon className="h-5 w-5 flex-shrink-0" aria-hidden="true" />
                <span className="sr-only">Home</span>
              </a>
            </div>
          </li>
          {pages.map((page) => (
            <li key={page.name}>
              <div className="flex items-center">
                <svg
                  className="h-5 w-5 flex-shrink-0 text-gray-300"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                  aria-hidden="true"
                >
                  <path d="M5.555 17.776l8-16 .894.448-8 16-.894-.448z" />
                </svg>
                <a
                  href={page.href}
                  className="ml-4 text-sm font-medium text-gray-500 hover:text-gray-700"
                  aria-current={page.current ? 'page' : undefined}
                >
                  {page.name}
                </a>
              </div>
            </li>
          ))}
        </ol>
      </nav>
    );
  }
};
