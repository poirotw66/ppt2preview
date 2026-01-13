import { useEffect, useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import ScriptPageEditor from '@/components/ScriptPageEditor';
import { useTaskStore } from '@/store/useTaskStore';
import { apiClient } from '@/services/api';
import { useToastStore } from '@/store/useToastStore';
import './PageLayout.css';

function ScriptPage() {
  const navigate = useNavigate();
  const { taskId, status, scriptContent, projectName, updateStatus } = useTaskStore();
  const { success, error: showError } = useToastStore();
  const [optimizing, setOptimizing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [editedName, setEditedName] = useState('');
  const [saving, setSaving] = useState(false);
  const hasCheckedRedirect = useRef(false);

  // Redirect only on initial load
  useEffect(() => {
    if (hasCheckedRedirect.current) return;
    hasCheckedRedirect.current = true;

    if (!taskId) {
      navigate('/upload');
    }
  }, []);
  const handleEditClick = () => {
    setEditedName(projectName || '');
    setIsEditing(true);
  };

  const handleSaveName = async () => {
    if (!taskId || !editedName.trim()) return;
    
    setSaving(true);
    try {
      const response = await apiClient.updateProjectName(taskId, editedName.trim());
      updateStatus(response);
      success('專案名稱已更新');
      setIsEditing(false);
    } catch (err: any) {
      showError(err.response?.data?.detail || '更新專案名稱失敗');
    } finally {
      setSaving(false);
    }
  };

  const handleCancelEdit = () => {
    setIsEditing(false);
    setEditedName('');
  };
  const handleOptimizeScript = async () => {
    if (!taskId) return;

    setOptimizing(true);
    setError(null);

    try {
      await apiClient.optimizeScript(taskId);

      // Poll for optimization completion
      const pollInterval = setInterval(async () => {
        try {
          const statusResponse = await apiClient.getTaskStatus(taskId!);
          updateStatus(statusResponse);
          
          if (statusResponse.status === 'script_ready') {
            clearInterval(pollInterval);
            // Load the optimized script
            const scriptResponse = await apiClient.getScript(taskId!);
            useTaskStore.getState().setScript(scriptResponse);
            setOptimizing(false);
            // Navigate to optimize page to show optimized script
            navigate(`/task/${taskId}/optimize`);
          } else if (statusResponse.status === 'failed') {
            clearInterval(pollInterval);
            setError(statusResponse.error || '腳本優化失敗');
            setOptimizing(false);
          }
        } catch (err) {
          console.error('Polling error:', err);
        }
      }, 2000);

      // Timeout after 5 minutes
      setTimeout(() => {
        clearInterval(pollInterval);
        if (optimizing) {
          setError('腳本優化超時，請重試');
          setOptimizing(false);
        }
      }, 300000);
    } catch (err: any) {
      setError(err.response?.data?.detail || '優化腳本失敗');
      setOptimizing(false);
    }
  };

  if (!taskId) {
    return null;
  }

  return (
    <div className="page-layout">
      <div className="page-header">
        <h1>步驟 2: 生成與編輯腳本</h1>
        <p>選擇腳本長度模式，生成腳本後可以進行編輯</p>
        {projectName && (
          <div className="project-name-badge">
            <span className="icon">✨</span>
            <span className="label">專案名稱：</span>
            {isEditing ? (
              <>
                <input
                  type="text"
                  className="project-name-input"
                  value={editedName}
                  onChange={(e) => setEditedName(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleSaveName()}
                  autoFocus
                  maxLength={20}
                />
                <div className="project-name-actions">
                  <button
                    className="project-name-btn save"
                    onClick={handleSaveName}
                    disabled={saving || !editedName.trim()}
                  >
                    {saving ? '儲存中...' : '✓ 儲存'}
                  </button>
                  <button
                    className="project-name-btn cancel"
                    onClick={handleCancelEdit}
                    disabled={saving}
                  >
                    ✕ 取消
                  </button>
                </div>
              </>
            ) : (
              <>
                <span className="name">{projectName}</span>
                <span className="edit-icon" onClick={handleEditClick} title="編輯專案名稱">
                  ✏️
                </span>
              </>
            )}
          </div>
        )}
      </div>

      <div className="page-content">
        <ScriptPageEditor />
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
            onClick={handleOptimizeScript}
            disabled={optimizing}
          >
            {optimizing ? '優化中...' : '下一步：優化腳本 →'}
          </button>
        )}
      </div>

      {error && <div className="error-message" style={{ textAlign: 'center', color: 'red', marginTop: '1rem' }}>{error}</div>}
    </div>
  );
}

export default ScriptPage;

