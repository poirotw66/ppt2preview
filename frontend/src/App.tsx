import { BrowserRouter, Routes, Route, Navigate, useParams, useLocation } from 'react-router-dom';
import Navigation from './components/Navigation';
import LandingPage from './pages/LandingPage';
import UploadPage from './pages/UploadPage';
import ScriptPage from './pages/ScriptPage';
import OptimizeScriptPage from './pages/OptimizeScriptPage';
import VideoPage from './pages/VideoPage';
import DownloadPage from './pages/DownloadPage';
import SettingsPage from './pages/SettingsPage';
import HistoryPage from './pages/HistoryPage';
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
      const currentState = useTaskStore.getState();
      if (storeTaskId === taskId && currentState.scriptContent && currentState.status) {
        setLoading(false);
        return;
      }

      try {
        // Fetch task status and script in parallel for better performance
        const [statusResponse, scriptResponse] = await Promise.allSettled([
          apiClient.getTaskStatus(taskId),
          apiClient.getScript(taskId)
        ]);

        // Update status
        if (statusResponse.status === 'fulfilled') {
          updateStatus(statusResponse.value);
        } else {
          console.error('Failed to load status:', statusResponse.reason);
        }

        // Update script if available
        if (scriptResponse.status === 'fulfilled') {
          setScript(scriptResponse.value);
        } else {
          console.log('Script not available yet:', scriptResponse.reason);
          // Script might not exist yet, that's okay
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

function AppContent() {
  const location = useLocation();
  const hideNavigation = location.pathname === '/' || location.pathname === '/settings' || location.pathname === '/history';

  return (
    <div className="app-container">
      {!hideNavigation && <Navigation />}
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/settings" element={<SettingsPage />} />
        <Route path="/history" element={<HistoryPage />} />
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
  );
}

function App() {
  return (
    <BrowserRouter>
      <AppContent />
    </BrowserRouter>
  );
}

export default App;

