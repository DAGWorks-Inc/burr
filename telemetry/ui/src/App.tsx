import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import './App.css';
import { ProjectList } from './components/routes/ProjectList';
import { AppList } from './components/routes/AppList';
import { AppView } from './components/routes/app/AppView';
import { QueryClient, QueryClientProvider } from 'react-query';
import { OpenAPI } from './api';
import { AppContainer } from './components/nav/appcontainer';

// TODO -- unhardcode
OpenAPI.BASE = 'http://localhost:7241';
/**
 * Basic application. We have an AppContainer -- this has a breadcrumb and a sidebar.
 * We refer to route paths to gather parameters, as its simple to wire through. We may
 * want to consider passing parameters in to avoid overly coupled dependencies/ensure
 * more reusable top-level components.
 * @returns A rendered application object
 */
const App = () => {
  return (
    <QueryClientProvider client={new QueryClient()}>
      <Router>
        <AppContainer>
          <Routes>
            <Route path="/" element={<Navigate to="/projects" />} />
            <Route path="/projects" element={<ProjectList />} />
            <Route path="/project/:projectId" element={<AppList />} />
            <Route path="/project/:projectId/:appId" element={<AppView />} />
            <Route path="*" element={<Navigate to="/projects" />} />
          </Routes>
        </AppContainer>
      </Router>
    </QueryClientProvider>
  );
};

export default App;
