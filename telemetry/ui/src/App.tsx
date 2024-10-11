import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import './App.css';
import { ProjectList } from './components/routes/ProjectList';
import { AppList } from './components/routes/AppList';
import { AppViewContainer } from './components/routes/app/AppView';
import { QueryClient, QueryClientProvider } from 'react-query';
import { AppContainer } from './components/nav/appcontainer';
import { ChatbotWithTelemetry } from './examples/Chatbot';
import { Counter } from './examples/Counter';
import { EmailAssistantWithTelemetry } from './examples/EmailAssistant';
import { StreamingChatbotWithTelemetry } from './examples/StreamingChatbot';
import { AdminView } from './components/routes/AdminView';
import { AnnotationsViewContainer } from './components/routes/app/AnnotationsView';

/**
 * Basic application. We have an AppContainer -- this has a breadcrumb and a sidebar.
 * We refer to route paths to gather parameters, as its simple to wire through. We may
 * want to consider passing parameters in to avoid overly coupled dependencies/ensure
 * more reusable top-level components.
 *
 * Note that you can run this in one of two modes:
 * 1. As an asset served by the backend
 * 2. Standalone, using npm run
 *
 * npm run will proxy to port 7241, versus the asset which will
 * hit the backend (on the same port/server as the FE, its just a static route).
 *
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
            <Route path="/project/:projectId/:partitionKey" element={<AppList />} />
            <Route path="/project/:projectId/:partitionKey/:appId" element={<AppViewContainer />} />
            <Route path="/annotations/:projectId/" element={<AnnotationsViewContainer />} />
            <Route path="/demos/counter" element={<Counter />} />
            <Route path="/demos/chatbot" element={<ChatbotWithTelemetry />} />
            <Route path="/demos/streaming-chatbot" element={<StreamingChatbotWithTelemetry />} />
            <Route path="/demos/email-assistant" element={<EmailAssistantWithTelemetry />} />
            <Route path="/admin" element={<AdminView />} />
            <Route path="*" element={<Navigate to="/projects" />} />
          </Routes>
        </AppContainer>
      </Router>
    </QueryClientProvider>
  );
};

export default App;
