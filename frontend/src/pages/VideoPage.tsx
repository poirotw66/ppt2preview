import { useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import ProgressTracker from '@/components/ProgressTracker';
import { useTaskStore } from '@/store/useTaskStore';
import './PageLayout.css';

function VideoPage() {
  const navigate = useNavigate();
  const { taskId, status } = useTaskStore();
  const hasCheckedRedirect = useRef(false);

  // Redirect only on initial load, not when status changes
  useEffect(() => {
    if (hasCheckedRedirect.current) return;
    hasCheckedRedirect.current = true;

    if (!taskId) {
      navigate('/upload');
    } else if (status === 'failed') {
      // Stay on video page to show error
      return;
    } else if (status !== 'generating_video' && status !== 'script_ready' && status !== 'completed') {
      // Only redirect if not in valid state
      navigate(`/task/${taskId}/optimize`);
    }
  }, []);

  if (!taskId) {
    return null;
  }

  return (
    <div className="page-layout">
      <div className="page-header">
        <h1>步驟 4: 生成影片</h1>
        <p>設定影片參數並開始生成，進度將即時更新</p>
      </div>

      <div className="page-content">
        <ProgressTracker />
      </div>

      <div className="page-footer">
        <button
          className="back-button"
          onClick={() => taskId ? navigate(`/task/${taskId}/optimize`) : navigate('/optimize')}
        >
          ← 上一步：優化腳本
        </button>

        {status === 'completed' && taskId && (
          <button
            className="next-button"
            onClick={() => navigate(`/task/${taskId}/download`)}
          >
            下一步：下載影片 →
          </button>
        )}
      </div>
    </div>
  );
}

export default VideoPage;

