import { BrowserRouter, Routes, Route, Navigate, useParams } from 'react-router-dom';
import Navigation from './components/Navigation';
import UploadPage from './pages/UploadPage';
import ScriptPage from './pages/ScriptPage';
import OptimizeScriptPage from './pages/OptimizeScriptPage';
import VideoPage from './pages/VideoPage';
import DownloadPage from './pages/DownloadPage';
import { useTaskStore } from './store/useTaskStore';
import { apiClient } from './services/api';
import { useEffect, useState } from 'react';
import './App.css';

// Wrapper component to sync taskId from URL params and restore task state
function TaskRouteWrapper({ children }: { children: React.ReactNode }) {
  const { taskId } = useParams<{ taskId: string }>();
  const { setTaskId, updateStatus, setScript, taskId: storeTaskId } = useTaskStore();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadTaskData = async () => {
      if (!taskId) {
        setLoading(false);
        return;
      }

      // Set taskId in store
      setTaskId(taskId);

      // If the store already has this taskId and data, no need to reload
      if (storeTaskId === taskId && useTaskStore.getState().scriptContent) {
        setLoading(false);
        return;
      }

      try {
        // Fetch task status
        const statusResponse = await apiClient.getTaskStatus(taskId);
        updateStatus(statusResponse);

        // If script is ready, fetch script content
        if (statusResponse.status === 'script_ready' || statusResponse.status === 'generating_video' || statusResponse.status === 'completed') {
          try {
            const scriptResponse = await apiClient.getScript(taskId);
            setScript(scriptResponse);
          } catch (err) {
            console.error('Failed to load script:', err);
            // Script might not exist yet, that's okay
          }
        }

        setLoading(false);
      } catch (err: any) {
        console.error('Failed to load task data:', err);
        setError(err.response?.data?.detail || '載入任務資料失敗');
        setLoading(false);
      }
    };

    loadTaskData();
  }, [taskId]);

  if (loading) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100vh',
        flexDirection: 'column',
        gap: '1rem'
      }}>
        <div className="spinner"></div>
        <span>載入中...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100vh',
        flexDirection: 'column',
        gap: '1rem'
      }}>
        <div style={{ color: 'red' }}>{error}</div>
        <button onClick={() => window.location.reload()}>重試</button>
      </div>
    );
  }

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

