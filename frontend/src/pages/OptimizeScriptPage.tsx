import { useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import ScriptEditor from '@/components/ScriptEditor';
import { useTaskStore } from '@/store/useTaskStore';
import './PageLayout.css';

function OptimizeScriptPage() {
  const navigate = useNavigate();
  const { taskId, status, scriptContent } = useTaskStore();
  const hasCheckedRedirect = useRef(false);

  // Redirect only on initial load
  useEffect(() => {
    if (hasCheckedRedirect.current) return;
    hasCheckedRedirect.current = true;

    if (!taskId) {
      navigate('/upload');
    } else if (!scriptContent && status !== 'script_ready') {
      navigate(`/task/${taskId}/script`);
    }
  }, []);

  if (!taskId) {
    return null;
  }

  return (
    <div className="page-layout">
      <div className="page-header">
        <h1>步驟 3: 優化腳本</h1>
        <p>檢查並優化生成的腳本內容，確保符合您的需求</p>
      </div>

      <div className="page-content">
        <ScriptEditor showOptimizeButton={false} />
      </div>

      <div className="page-footer">
        <button
          className="back-button"
          onClick={() => taskId ? navigate(`/task/${taskId}/script`) : navigate('/script')}
        >
          ← 上一步：生成腳本
        </button>

        {(status === 'script_ready' || scriptContent) && taskId && (
          <button
            className="next-button"
            onClick={() => navigate(`/task/${taskId}/video`)}
          >
            下一步：生成影片 →
          </button>
        )}
      </div>
    </div>
  );
}

export default OptimizeScriptPage;

