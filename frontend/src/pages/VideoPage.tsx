import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import ProgressTracker from '@/components/ProgressTracker';
import { useTaskStore } from '@/store/useTaskStore';
import { apiClient } from '@/services/api';
import { useToastStore } from '@/store/useToastStore';
import { VideoParams } from '@/types';
import './PageLayout.css';
import './VideoPage.css';

function VideoPage() {
  const navigate = useNavigate();
  const { taskId, status, videoParams, projectName, updateStatus } = useTaskStore();
  const { success, error: showError } = useToastStore();
  const hasCheckedRedirect = useRef(false);
  const [isEditing, setIsEditing] = useState(false);
  const [editedName, setEditedName] = useState('');
  const [saving, setSaving] = useState(false);

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
        <h1>步驟 4: 生成影片</h1>
        <p>設定影片參數並開始生成，進度將即時更新</p>
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
        {status === 'completed' ? (
          <div className="video-params-display">
            <div className="completion-message">
              <svg className="success-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <h3>影片生成完成！</h3>
              <p>您的影片已經成功生成，可以前往下載頁面查看和下載。</p>
            </div>
            {videoParams && (
              <>
                <h3 style={{ marginTop: '2rem', marginBottom: '1rem' }}>影片參數</h3>
                <div className="params-grid">
                  <div className="param-item">
                    <span className="param-label">FPS（幀率）</span>
                    <span className="param-value">{videoParams.fps || 5}</span>
                  </div>
                  <div className="param-item">
                    <span className="param-label">解析度</span>
                    <span className="param-value">
                      {videoParams.resolution_width || 1920} × {videoParams.resolution_height || 1080}
                    </span>
                  </div>
                  <div className="param-item">
                    <span className="param-label">位元率</span>
                    <span className="param-value">{videoParams.bitrate || '2000k'}</span>
                  </div>
                  <div className="param-item">
                    <span className="param-label">編碼預設</span>
                    <span className="param-value">{videoParams.preset || 'ultrafast'}</span>
                  </div>
                </div>
              </>
            )}
          </div>
        ) : (
          <ProgressTracker />
        )}
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

