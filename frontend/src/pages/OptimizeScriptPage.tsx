import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import ScriptPageEditor from '@/components/ScriptPageEditor';
import { useTaskStore } from '@/store/useTaskStore';
import { apiClient } from '@/services/api';
import { useToastStore } from '@/store/useToastStore';
import './PageLayout.css';

function OptimizeScriptPage() {
  const navigate = useNavigate();
  const { taskId, status, scriptContent, projectName, updateStatus } = useTaskStore();
  const { success, error: showError } = useToastStore();
  const hasCheckedRedirect = useRef(false);
  const [isEditing, setIsEditing] = useState(false);
  const [editedName, setEditedName] = useState('');
  const [saving, setSaving] = useState(false);

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

  if (!taskId) {
    return null;
  }

  return (
    <div className="page-layout">
      <div className="page-header">
        <h1>步驟 3: 優化腳本</h1>
        <p>檢查並優化生成的腳本內容，確保符合您的需求</p>
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
        <ScriptPageEditor showOptimizeButton={false} />
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

