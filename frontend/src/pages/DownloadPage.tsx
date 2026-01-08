import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import VideoDownload from '@/components/VideoDownload';
import { useTaskStore } from '@/store/useTaskStore';
import './PageLayout.css';

function DownloadPage() {
  const navigate = useNavigate();
  const { taskId, status } = useTaskStore();

  // Redirect if not completed
  useEffect(() => {
    if (!taskId) {
      navigate('/upload');
    } else if (status !== 'completed') {
      navigate(`/task/${taskId}/video`);
    }
  }, [taskId, status, navigate]);

  if (!taskId || status !== 'completed') {
    return null;
  }

  return (
    <div className="page-layout">
      <div className="page-header">
        <h1>步驟 5: 下載影片</h1>
        <p>影片生成完成！您可以預覽並下載最終影片</p>
      </div>

      <div className="page-content">
        <VideoDownload />
      </div>

      <div className="page-footer">
        <button
          className="back-button"
          onClick={() => taskId ? navigate(`/task/${taskId}/video`) : navigate('/video')}
        >
          ← 上一步：生成影片
        </button>

        <button
          className="new-task-button"
          onClick={() => {
            useTaskStore.getState().reset();
            navigate('/upload');
          }}
        >
          <svg width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M12 4v16m8-8H4" />
          </svg>
          建立新任務
        </button>
      </div>
    </div>
  );
}

export default DownloadPage;

