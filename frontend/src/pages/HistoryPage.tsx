import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiClient } from '../services/api';
import { HistoryProject } from '../types';
import './HistoryPage.css';

function HistoryPage() {
  const navigate = useNavigate();
  const [projects, setProjects] = useState<HistoryProject[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiClient.getHistory();
      setProjects(response.projects);
    } catch (err: any) {
      console.error('Failed to load history:', err);
      setError(err.response?.data?.detail || '載入歷史專案失敗');
    } finally {
      setLoading(false);
    }
  };

  const handleOpenProject = (taskId: string, project: HistoryProject) => {
    // Navigate to appropriate page based on project status
    if (project.has_video) {
      navigate(`/task/${taskId}/download`);
    } else if (project.has_script) {
      navigate(`/task/${taskId}/optimize`);
    } else {
      navigate(`/task/${taskId}/upload`);
    }
  };

  const getStatusText = (status: string) => {
    const statusMap: Record<string, string> = {
      'completed': '已完成',
      'script_ready': '腳本已生成',
      'generating_video': '生成影片中',
      'generating_script': '生成腳本中',
      'failed': '失敗',
      'unknown': '未知'
    };
    return statusMap[status] || status;
  };

  const getStatusColor = (status: string) => {
    const colorMap: Record<string, string> = {
      'completed': 'success',
      'script_ready': 'warning',
      'generating_video': 'info',
      'generating_script': 'info',
      'failed': 'error',
      'unknown': 'default'
    };
    return colorMap[status] || 'default';
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return '未知';
    try {
      const date = new Date(dateString);
      return date.toLocaleString('zh-TW', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return '未知';
    }
  };

  return (
    <div className="history-page">
      <div className="history-container">
        {/* Header */}
        <div className="history-header">
          <button 
            className="back-button glass"
            onClick={() => navigate('/')}
            aria-label="返回首頁"
          >
            <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </button>
          
          <div className="header-content">
            <h1 className="page-title">歷史專案</h1>
            <p className="page-description">查看和繼續您的專案</p>
          </div>

          <button 
            className="refresh-button glass"
            onClick={loadProjects}
            aria-label="重新整理"
          >
            <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="history-content">
          {loading && (
            <div className="loading-state">
              <div className="spinner"></div>
              <p>載入中...</p>
            </div>
          )}

          {error && (
            <div className="error-state glass">
              <svg className="error-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <p>{error}</p>
              <button className="retry-button" onClick={loadProjects}>
                重試
              </button>
            </div>
          )}

          {!loading && !error && projects.length === 0 && (
            <div className="empty-state glass">
              <svg className="empty-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <h3>尚無歷史專案</h3>
              <p>開始創建您的第一個專案吧！</p>
              <button 
                className="cta-button primary"
                onClick={() => navigate('/upload')}
              >
                立即開始
              </button>
            </div>
          )}

          {!loading && !error && projects.length > 0 && (
            <div className="projects-grid">
              {projects.map((project) => (
                <div 
                  key={project.task_id}
                  className="project-card glass"
                  onClick={() => handleOpenProject(project.task_id, project)}
                >
                  <div className="project-header">
                    <div className={`project-status ${getStatusColor(project.status)}`}>
                      {getStatusText(project.status)}
                    </div>
                    <div className="project-icons">
                      {project.has_script && (
                        <svg className="icon-badge" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                      )}
                      {project.has_video && (
                        <svg className="icon-badge" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                        </svg>
                      )}
                    </div>
                  </div>

                  <div className="project-id">
                    <span className="id-label">專案 ID:</span>
                    <span className="id-value">{project.task_id.substring(0, 8)}...</span>
                  </div>

                  <div className="project-times">
                    <div className="time-item">
                      <svg className="time-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      <span>{formatDate(project.modified_time)}</span>
                    </div>
                  </div>

                  <button className="open-button">
                    <span>開啟專案</span>
                    <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                    </svg>
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default HistoryPage;
