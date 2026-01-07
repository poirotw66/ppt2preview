import { BrowserRouter, Routes, Route, Navigate, useParams } from 'react-router-dom';
import Navigation from './components/Navigation';
import UploadPage from './pages/UploadPage';
import ScriptPage from './pages/ScriptPage';
import OptimizeScriptPage from './pages/OptimizeScriptPage';
import VideoPage from './pages/VideoPage';
import DownloadPage from './pages/DownloadPage';
import { useTaskStore } from './store/useTaskStore';
import { useEffect } from 'react';
import './App.css';

// Wrapper component to sync taskId from URL params
function TaskRouteWrapper({ children }: { children: React.ReactNode }) {
  const { taskId } = useParams<{ taskId: string }>();
  const { setTaskId } = useTaskStore();

  useEffect(() => {
    if (taskId) {
      setTaskId(taskId);
    }
  }, [taskId, setTaskId]);

  return <>{children}</>;
}

function App() {
  return (
    <BrowserRouter>
      <div className="app-container">
        <Navigation />
        <Routes>
          <Route path="/" element={<Navigate to="/upload" replace />} />
          <Route path="/upload" element={<UploadPage />} />
          <Route path="/task/:taskId/upload" element={<TaskRouteWrapper><UploadPage /></TaskRouteWrapper>} />
          <Route path="/task/:taskId/script" element={<TaskRouteWrapper><ScriptPage /></TaskRouteWrapper>} />
          <Route path="/task/:taskId/optimize" element={<TaskRouteWrapper><OptimizeScriptPage /></TaskRouteWrapper>} />
          <Route path="/task/:taskId/video" element={<TaskRouteWrapper><VideoPage /></TaskRouteWrapper>} />
          <Route path="/task/:taskId/download" element={<TaskRouteWrapper><DownloadPage /></TaskRouteWrapper>} />
          {/* Legacy routes for backward compatibility */}
          <Route path="/script" element={<ScriptPage />} />
          <Route path="/video" element={<VideoPage />} />
          <Route path="/download" element={<DownloadPage />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;

