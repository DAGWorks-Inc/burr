import { Fragment, useState } from 'react';
import { Dialog, Disclosure, Transition } from '@headlessui/react';
import {
  ComputerDesktopIcon,
  Square2StackIcon,
  QuestionMarkCircleIcon,
  XMarkIcon,
  ChatBubbleLeftEllipsisIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  ChevronDownIcon
} from '@heroicons/react/24/outline';
import { ListBulletIcon } from '@heroicons/react/20/solid';
import { BreadCrumb } from './breadcrumb';
import { Link } from 'react-router-dom';
import { classNames } from '../../utils/tailwind';

/**
 * Toggles the sidebar open and closed.
 */
const ToggleOpenButton = (props: { open: boolean; toggleSidebar: () => void }) => {
  const MinimizeMaximizeIcon = props.open ? ChevronLeftIcon : ChevronRightIcon;
  return (
    <MinimizeMaximizeIcon
      className={classNames(
        'text-gray-400',
        'h-8 w-8 hover:bg-gray-50 rounded-md hover:cursor-pointer'
      )}
      aria-hidden="true"
      onClick={props.toggleSidebar}
    />
  );
};

/**
 * Container for the app. Contains three main parts:
 * 1. The sidebar
 * 2. The breadcrumb
 * 3. The main content
 *
 * TODO -- get this to work in small mode -- the sidebar is currently not there.
 */
export const AppContainer = (props: { children: React.ReactNode }) => {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [smallSidebarOpen, setSmallSidebarOpen] = useState(false);
  const toggleSidebar = () => {
    setSidebarOpen(!sidebarOpen);
  };
  const navigation = [
    {
      name: 'Projects',
      href: '/projects',
      icon: Square2StackIcon,
      linkType: 'internal'
    },
    {
      name: 'Demos',
      href: '/demos',
      icon: ListBulletIcon,
      linkType: 'internal',
      children: [
        // { name: 'counter', href: '/demos/counter', current: false, linkType: 'internal' },
        { name: 'chatbot', href: '/demos/chatbot', current: false, linkType: 'internal' }
      ]
    },
    {
      name: 'Examples',
      href: 'https://github.com/DAGWorks-Inc/burr/tree/main/examples',
      icon: ListBulletIcon,
      linkType: 'external'
    },
    {
      name: 'Develop',
      href: 'https://github.com/dagworks-inc/burr',
      icon: ComputerDesktopIcon,
      linkType: 'external'
    },
    {
      name: 'Documentation',
      href: 'https://burr.dagworks.io',
      icon: QuestionMarkCircleIcon,
      linkType: 'external'
    },
    {
      name: 'Get Help',
      href: 'https://github.com/DAGWorks-Inc/burr/discussions',
      icon: ChatBubbleLeftEllipsisIcon,
      linkType: 'external'
    }
  ];

  const isCurrent = (href: string, linkType: string) => {
    if (linkType === 'external') {
      return false;
    }
    return window.location.pathname.startsWith(href);
  };

  return (
    <>
      <div className="h-screen w-screen overflow-x-auto">
        <Transition.Root show={smallSidebarOpen} as={Fragment}>
          <Dialog as="div" className="relative z-50 lg:hidden" onClose={setSmallSidebarOpen}>
            <Transition.Child
              as={Fragment}
              enter="transition-opacity ease-linear duration-300"
              enterFrom="opacity-0"
              enterTo="opacity-100"
              leave="transition-opacity ease-linear duration-300"
              leaveFrom="opacity-100"
              leaveTo="opacity-0"
            >
              <div className="fixed inset-0 bg-gray-900/80" />
            </Transition.Child>

            <div className="fixed inset-0 flex">
              <Transition.Child
                as={Fragment}
                enter="transition ease-in-out duration-300 transform"
                enterFrom="-translate-x-full"
                enterTo="translate-x-0"
                leave="transition ease-in-out duration-300 transform"
                leaveFrom="translate-x-0"
                leaveTo="-translate-x-full"
              >
                <Dialog.Panel className="relative mr-16 flex w-full max-w-xs flex-1">
                  <Transition.Child
                    as={Fragment}
                    enter="ease-in-out duration-300"
                    enterFrom="opacity-0"
                    enterTo="opacity-100"
                    leave="ease-in-out duration-300"
                    leaveFrom="opacity-100"
                    leaveTo="opacity-0"
                  >
                    <div className="absolute left-full top-0 flex w-16 justify-center pt-5">
                      <button
                        type="button"
                        className="-m-2.5 p-2.5"
                        onClick={() => setSmallSidebarOpen(false)}
                      >
                        <span className="sr-only">Close sidebar</span>
                        <XMarkIcon className="h-6 w-6 text-white" aria-hidden="true" />
                      </button>
                    </div>
                  </Transition.Child>
                  {/* Sidebar component, swap this element with another sidebar if you like */}
                  <div className="flex grow flex-col gap-y-5 overflow-y-auto bg-white px-6 pb-2 py-2">
                    <div className="flex h-16 shrink-0 items-center">
                      <img className="h-10 w-auto" src={'/logo.png'} alt="Burr" />
                    </div>
                    <nav className="flex flex-1 flex-col">
                      <ul role="list" className="flex flex-1 flex-col gap-y-7">
                        <li>
                          <ul role="list" className="-mx-2 space-y-1">
                            {navigation.map((item) => (
                              <li key={item.name}>
                                <Link
                                  to={item.href}
                                  // target={item.linkType === 'external' ? '_blank' : undefined}
                                  // rel={
                                  //   item.linkType === 'external' ? 'noopener noreferrer' : undefined
                                  // }
                                  className={classNames(
                                    isCurrent(item.href, item.linkType)
                                      ? 'bg-gray-50 text-dwdarkblue'
                                      : item.linkType === 'external'
                                        ? 'text-gray-700 hover:text-dwdarkblue'
                                        : 'text-gray-700 hover:text-dwdarkblue hover:bg-gray-50',
                                    'group flex gap-x-3 rounded-md p-2 text-sm leading-6 font-semibold'
                                  )}
                                >
                                  <item.icon
                                    className={classNames(
                                      isCurrent(item.href, item.linkType)
                                        ? 'text-dwdarkblue'
                                        : 'text-gray-400 group-hover:text-dwdarkblue',
                                      'h-6 w-6 shrink-0'
                                    )}
                                    aria-hidden="true"
                                  />
                                  {item.name}
                                </Link>
                              </li>
                            ))}
                          </ul>
                        </li>
                      </ul>
                    </nav>
                  </div>
                </Dialog.Panel>
              </Transition.Child>
            </div>
          </Dialog>
        </Transition.Root>

        {/* Static sidebar for desktop */}
        <div
          className={`hidden ${
            sidebarOpen ? 'h-screen lg:fixed lg:inset-y-0 lg:z-50 lg:flex lg:w-72 lg:flex-col' : ''
          }`}
        >
          {/* Sidebar component, swap this element with another sidebar if you like */}
          <div className="flex grow flex-col gap-y-5 overflow-y-auto border-r border-gray-200 bg-white px-6 py-2">
            <div className="flex h-16 shrink-0 items-center">
              <img className="h-12 w-auto" src={'/public/logo.png'} alt="Burr" />
            </div>
            <nav className="flex flex-1 flex-col">
              <ul role="list" className="flex flex-1 flex-col gap-y-7">
                <li>
                  <ul role="list" className="-mx-2 space-y-1">
                    {navigation.map((item) => (
                      <li key={item.name}>
                        {!item?.children ? (
                          <Link
                            to={item.href}
                            className={classNames(
                              isCurrent(item.href, item.linkType)
                                ? 'bg-gray-50'
                                : 'hover:bg-gray-50',
                              'group flex gap-x-3 rounded-md p-2 text-sm leading-6 font-semibold text-gray-700'
                            )}
                          >
                            <item.icon
                              className="h-6 w-6 shrink-0 text-gray-400"
                              aria-hidden="true"
                            />
                            {item.name}
                          </Link>
                        ) : (
                          <Disclosure as="div">
                            {({ open }) => (
                              <>
                                <Disclosure.Button
                                  className={classNames(
                                    isCurrent(item.href, item.linkType)
                                      ? 'bg-gray-50'
                                      : 'hover:bg-gray-50',
                                    'flex items-center w-full text-left rounded-md p-2 gap-x-3 text-sm leading-6 font-semibold text-gray-700'
                                  )}
                                >
                                  <item.icon
                                    className="h-6 w-6 shrink-0 text-gray-400"
                                    aria-hidden="true"
                                  />
                                  {item.name}
                                  <ChevronDownIcon
                                    className={classNames(
                                      open ? 'rotate-180 text-gray-500' : 'text-gray-400',
                                      'ml-auto h-5 w-5 shrink-0'
                                    )}
                                    aria-hidden="true"
                                  />
                                </Disclosure.Button>
                                <Disclosure.Panel as="ul" className="mt-1 px-2">
                                  {item.children.map((subItem) => (
                                    <li key={subItem.name}>
                                      <Link
                                        to={subItem.href}
                                        className={classNames(
                                          isCurrent(subItem.href, subItem.linkType)
                                            ? 'bg-gray-50'
                                            : 'hover:bg-gray-50',
                                          'block rounded-md py-2 pr-2 pl-9 text-sm leading-6 text-gray-700'
                                        )}
                                      >
                                        {subItem.name}
                                      </Link>
                                    </li>
                                  ))}
                                </Disclosure.Panel>
                              </>
                            )}
                          </Disclosure>
                        )}
                      </li>
                    ))}
                  </ul>
                </li>
              </ul>
            </nav>
            <div className="flex justify-start -mx-5">
              <ToggleOpenButton open={sidebarOpen} toggleSidebar={toggleSidebar} />
            </div>
          </div>
        </div>
        <div
          className={`hidden h-screen ${
            !sidebarOpen
              ? 'lg:fixed lg:inset-y-0 lg:z-50 lg:flex lg:w-8 lg:flex-col justify-end lg:py-2 lg:px-1'
              : ''
          }`}
        >
          <ToggleOpenButton open={sidebarOpen} toggleSidebar={toggleSidebar} />
        </div>

        {/* This is a bit hacky -- just quickly prototyping and these margins were the ones that worked! */}
        <main className={`py-14 -my-1 ${sidebarOpen ? 'lg:pl-72' : 'lg:pl-5'} h-full`}>
          <div className="flex items-center px-5 sm:px-7 lg:px-9 pb-8 -my-4">
            <BreadCrumb />
          </div>
          <div className="flex h-full flex-col">
            <div className="px-4 sm:px-6 lg:px-2 max-h-full h-full flex-1"> {props.children}</div>
          </div>
        </main>
      </div>
    </>
  );
};
