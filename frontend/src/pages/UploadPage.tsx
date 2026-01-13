import { useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import FileUpload from '@/components/FileUpload';
import { useTaskStore } from '@/store/useTaskStore';
import './PageLayout.css';

function UploadPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { taskId, status, reset } = useTaskStore();

  // Check if we're on a task-specific route or just /upload
  const isTaskRoute = location.pathname.includes('/task/');
  
  // If user navigates to /upload (not a task route), reset the store to start fresh
  useEffect(() => {
    if (!isTaskRoute && taskId) {
      // User came from landing page or directly navigated to /upload
      // Reset to ensure a fresh start
      reset();
    }
  }, [isTaskRoute, taskId, reset]);

  // Redirect if task already exists (only for task-specific routes)
  useEffect(() => {
    // Only redirect if we're on a task-specific route and have a valid task
    if (isTaskRoute && taskId) {
      if (status === 'script_ready') {
        navigate(`/task/${taskId}/script`);
      } else if (status && ['generating_video', 'completed'].includes(status)) {
        navigate(`/task/${taskId}/video`);
      }
    }
  }, [taskId, status, navigate, isTaskRoute]);

  return (
    <div className="page-layout">
      <div className="page-header">
        <h1>步驟 1: 上傳檔案</h1>
        <p>請選擇簡報大綱檔案（Markdown）和 PDF 投影片檔案</p>
      </div>

      <div className="page-content">
        <FileUpload />
      </div>

      <div className="page-footer">
        {taskId && (
          <button
            className="next-button"
            onClick={() => navigate(`/task/${taskId}/script`)}
          >
            下一步：生成腳本 →
          </button>
        )}
      </div>
    </div>
  );
}

export default UploadPage;

