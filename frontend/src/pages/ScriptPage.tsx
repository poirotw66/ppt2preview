import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import ScriptEditor from '@/components/ScriptEditor';
import { useTaskStore } from '@/store/useTaskStore';
import './PageLayout.css';

function ScriptPage() {
  const navigate = useNavigate();
  const { taskId, status, scriptContent } = useTaskStore();

  // Redirect if no task or already completed
  useEffect(() => {
    if (!taskId) {
      navigate('/upload');
    } else if (status === 'generating_video') {
      navigate(`/task/${taskId}/video`);
    } else if (status === 'completed') {
      navigate(`/task/${taskId}/download`);
    }
  }, [taskId, status, navigate]);

  if (!taskId) {
    return null;
  }

  return (
    <div className="page-layout">
      <div className="page-header">
        <h1>步驟 2: 生成與編輯腳本</h1>
        <p>選擇腳本長度模式，生成腳本後可以進行編輯</p>
      </div>

      <div className="page-content">
        <ScriptEditor />
      </div>

      <div className="page-footer">
        <button
          className="back-button"
          onClick={() => taskId ? navigate(`/task/${taskId}/upload`) : navigate('/upload')}
        >
          ← 上一步：上傳檔案
        </button>

        {(status === 'script_ready' || scriptContent) && taskId && (
          <button
            className="next-button"
            onClick={() => navigate(`/task/${taskId}/optimize`)}
          >
            下一步：優化腳本 →
          </button>
        )}
      </div>
    </div>
  );
}

export default ScriptPage;

