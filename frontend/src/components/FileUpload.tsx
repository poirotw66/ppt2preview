import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiClient } from '@/services/api';
import { useTaskStore } from '@/store/useTaskStore';
import { LengthMode } from '@/types';
import './FileUpload.css';

function FileUpload() {
  const navigate = useNavigate();
  const { taskId, setTaskId, updateStatus } = useTaskStore();
  const [abstractFile, setAbstractFile] = useState<File | null>(null);
  const [pdfFile, setPdfFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleAbstractFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setAbstractFile(file);
      setError(null);
    }
  };

  const handlePdfFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setPdfFile(file);
      setError(null);
    }
  };

  const handleUpload = async () => {
    if (!abstractFile) {
      setError('請選擇簡報大綱檔案（Markdown）');
      return;
    }

    setUploading(true);
    setError(null);

    try {
      const response = await apiClient.uploadFiles(abstractFile, pdfFile || undefined);
      setTaskId(response.task_id);
      updateStatus({
        task_id: response.task_id,
        status: 'uploading' as any,
        progress: 10,
        message: response.message,
      });
      // Navigate to script page with task ID
      navigate(`/task/${response.task_id}/script`);
    } catch (err: any) {
      setError(err.response?.data?.detail || '上傳失敗，請重試');
      console.error('Upload error:', err);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="file-upload">
      <div className="upload-section">
        <label className="file-label">
          <input
            type="file"
            accept=".md,.markdown"
            onChange={handleAbstractFileChange}
            disabled={uploading || !!taskId}
          />
          <div className="file-label-content">
            <svg className="file-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
            </svg>
            <span className="file-label-title">
              簡報大綱檔案（Markdown）*
            </span>
            <span className="file-label-hint">
              點擊或拖曳檔案至此處上傳
            </span>
          </div>
          {abstractFile && (
            <span className="file-name">
              <svg className="file-name-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              {abstractFile.name}
            </span>
          )}
        </label>
      </div>

      <div className="upload-section">
        <label className="file-label">
          <input
            type="file"
            accept=".pdf"
            onChange={handlePdfFileChange}
            disabled={uploading || !!taskId}
          />
          <div className="file-label-content">
            <svg className="file-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
            </svg>
            <span className="file-label-title">
              PDF 投影片檔案（選填）
            </span>
            <span className="file-label-hint">
              點擊或拖曳檔案至此處上傳
            </span>
          </div>
          {pdfFile && (
            <span className="file-name">
              <svg className="file-name-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              {pdfFile.name}
            </span>
          )}
        </label>
      </div>

      {error && (
        <div className="error-message">
          <svg className="error-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          {error}
        </div>
      )}

      <button
        className="upload-button"
        onClick={handleUpload}
        disabled={!abstractFile || uploading || !!taskId}
      >
        {uploading ? (
          <>
            <svg className="upload-button-icon animate-spin" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            <span>上傳中...</span>
          </>
        ) : taskId ? (
          <>
            <svg className="upload-button-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            <span>已上傳</span>
          </>
        ) : (
          <>
            <svg className="upload-button-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
            <span>上傳檔案</span>
          </>
        )}
      </button>

      {taskId && (
        <div className="success-message">
          <svg className="success-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          檔案上傳成功！任務 ID: {taskId.substring(0, 8)}...
        </div>
      )}
    </div>
  );
}

export default FileUpload;

