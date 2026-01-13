import { useEffect, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import FileUpload from '@/components/FileUpload';
import { useTaskStore } from '@/store/useTaskStore';
import { apiClient } from '@/services/api';
import { useToastStore } from '@/store/useToastStore';
import './PageLayout.css';

function UploadPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { taskId, status, projectName, updateStatus, reset } = useTaskStore();
  const { success, error: showError } = useToastStore();
  const [isEditing, setIsEditing] = useState(false);
  const [editedName, setEditedName] = useState('');
  const [saving, setSaving] = useState(false);

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

  return (
    <div className="page-layout">
      <div className="page-header">
        <h1>步驟 1: 上傳檔案</h1>
        <p>請選擇簡報大綱檔案（Markdown）和 PDF 投影片檔案</p>
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

