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
import { ToastContainer } from './components/Toast';
import { useToastStore } from './store/useToastStore';
import { useEffect, useState } from 'react';
import './App.css';

// Wrapper component to sync taskId from URL params and restore task state
function TaskRouteWrapper({ children }: { children: React.ReactNode }) {
  const { taskId } = useParams<{ taskId: string }>();
  const { setTaskId, updateStatus, setScript, taskId: storeTaskId } = useTaskStore();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [retryCount, setRetryCount] = useState(0);

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

        // Handle status response
        if (statusResponse.status === 'fulfilled') {
          updateStatus(statusResponse.value);
        } else {
          console.error('Failed to load status:', statusResponse.reason);
          throw new Error('無法載入任務狀態，請檢查任務ID是否正確');
        }

        // Handle script response
        if (scriptResponse.status === 'fulfilled') {
          setScript(scriptResponse.value);
        } else {
          console.log('Script not available yet:', scriptResponse.reason);
          // Script might not exist yet, that's okay for earlier stages
        }

        setLoading(false);
        setError(null);
      } catch (err: any) {
        console.error('Failed to load task data:', err);
        const errorMessage = err.message || err.response?.data?.detail || '載入任務資料失敗';
        setError(errorMessage);
        setLoading(false);
      }
    };

    loadTaskData();
  }, [taskId, retryCount]);

  const handleRetry = () => {
    setLoading(true);
    setError(null);
    setRetryCount(prev => prev + 1);
  };

  const handleGoHome = () => {
    window.location.href = '/';
  };

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
        gap: '1.5rem',
        padding: '2rem',
        maxWidth: '500px',
        margin: '0 auto'
      }}>
        <div style={{ 
          fontSize: '3rem',
          filter: 'grayscale(1)',
          opacity: 0.5
        }}>😕</div>
        <div style={{ 
          color: 'var(--text-primary)',
          fontSize: '1.25rem',
          fontWeight: 'bold',
          textAlign: 'center'
        }}>載入失敗</div>
        <div style={{ 
          color: 'var(--text-secondary)',
          fontSize: '0.95rem',
          textAlign: 'center',
          lineHeight: '1.6'
        }}>{error}</div>
        <div style={{
          display: 'flex',
          gap: '1rem',
          marginTop: '0.5rem'
        }}>
          <button 
            onClick={handleRetry}
            style={{
              padding: '0.75rem 1.5rem',
              background: 'var(--gradient-primary)',
              border: 'none',
              borderRadius: '12px',
              color: 'white',
              fontSize: '1rem',
              cursor: 'pointer',
              fontWeight: '600',
              transition: 'all 0.3s ease'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.transform = 'translateY(-2px)';
              e.currentTarget.style.boxShadow = '0 8px 16px rgba(0,0,0,0.2)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.transform = 'translateY(0)';
              e.currentTarget.style.boxShadow = 'none';
            }}
          >
            🔄 重試
          </button>
          <button 
            onClick={handleGoHome}
            style={{
              padding: '0.75rem 1.5rem',
              background: 'var(--glass-bg)',
              backdropFilter: 'blur(10px)',
              border: '1px solid var(--border-color)',
              borderRadius: '12px',
              color: 'var(--text-primary)',
              fontSize: '1rem',
              cursor: 'pointer',
              fontWeight: '600',
              transition: 'all 0.3s ease'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.transform = 'translateY(-2px)';
              e.currentTarget.style.boxShadow = '0 8px 16px rgba(0,0,0,0.2)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.transform = 'translateY(0)';
              e.currentTarget.style.boxShadow = 'none';
            }}
          >
            🏠 返回首頁
          </button>
        </div>
        {retryCount > 0 && (
          <div style={{ 
            color: 'var(--text-tertiary)',
            fontSize: '0.85rem',
            marginTop: '0.5rem'
          }}>
            已重試 {retryCount} 次
          </div>
        )}
      </div>
    );
  }

  return <>{children}</>;
}

function AppContent() {
  const location = useLocation();
  const hideNavigation = location.pathname === '/' || location.pathname === '/settings' || location.pathname === '/history';
  const { toasts, removeToast } = useToastStore();

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
      <ToastContainer toasts={toasts} onRemove={removeToast} />
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

