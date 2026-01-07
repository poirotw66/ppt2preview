import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import FileUpload from '@/components/FileUpload';
import { useTaskStore } from '@/store/useTaskStore';
import './PageLayout.css';

function UploadPage() {
  const navigate = useNavigate();
  const { taskId, status } = useTaskStore();

  // Redirect if task already exists
  useEffect(() => {
    if (taskId) {
      if (status === 'script_ready') {
        navigate(`/task/${taskId}/script`);
      } else if (status && ['generating_video', 'completed'].includes(status)) {
        navigate(`/task/${taskId}/video`);
      }
    }
  }, [taskId, status, navigate]);

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

