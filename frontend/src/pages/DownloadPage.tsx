import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import VideoDownload from '@/components/VideoDownload';
import { useTaskStore } from '@/store/useTaskStore';
import { apiClient } from '@/services/api';
import { useToastStore } from '@/store/useToastStore';
import './PageLayout.css';

function DownloadPage() {
  const navigate = useNavigate();
  const { taskId, status, projectName, updateStatus } = useTaskStore();
  const { success, error: showError } = useToastStore();
  const [isEditing, setIsEditing] = useState(false);
  const [editedName, setEditedName] = useState('');
  const [saving, setSaving] = useState(false);

  // Redirect if not completed
  useEffect(() => {
    if (!taskId) {
      navigate('/upload');
    } else if (status !== 'completed') {
      navigate(`/task/${taskId}/video`);
    }
  }, [taskId, status, navigate]);

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

  if (!taskId || status !== 'completed') {
    return null;
  }

  return (
    <div className="page-layout">
      <div className="page-header">
        <h1>步驟 5: 下載影片</h1>
        <p>影片生成完成！您可以預覽並下載最終影片</p>
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

