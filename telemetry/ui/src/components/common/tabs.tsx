function classNames(...classes: string[]) {
  return classes.filter(Boolean).join(' ');
}
/**
 * Tabs component for displaying a list of tabs.
 */
export const Tabs = (props: {
  tabs: {
    id: string;
    displayName: string;
  }[];
  currentTab: string;
  setCurrentTab: (tab: string) => void;
}) => {
  const { currentTab, setCurrentTab } = props;
  return (
    <div>
      <div className="sm:hidden">
        <label htmlFor="tabs" className="sr-only">
          Select a tab
        </label>
        {/* Use an "onChange" listener to redirect the user to the selected tab URL. */}
        <select
          id="tabs"
          name="tabs"
          className="block w-full rounded-md border-gray-300 focus:border-indigo-500 focus:ring-indigo-500"
          defaultValue={currentTab}
        >
          {props.tabs.map((tab) => (
            <option key={tab.id}>{tab.displayName}</option>
          ))}
        </select>
      </div>
      <div className="hidden sm:block">
        <nav className="flex space-x-4" aria-label="Tabs">
          {props.tabs.map((tab) => (
            <span
              onClick={() => setCurrentTab(tab.id)}
              key={tab.displayName}
              className={classNames(
                tab.id === currentTab
                  ? 'bg-indigo-100 text-dwdarkblue'
                  : 'text-gray-500 hover:text-gray-700',
                'rounded-md px-3 py-2 text-sm font-medium hover:cursor-pointer'
              )}
              aria-current={tab.id === currentTab ? 'page' : undefined}
            >
              {tab.displayName}
            </span>
          ))}
        </nav>
      </div>
    </div>
  );
};
