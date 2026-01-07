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
          <span>簡報大綱檔案（Markdown）*</span>
          <input
            type="file"
            accept=".md,.markdown"
            onChange={handleAbstractFileChange}
            disabled={uploading || !!taskId}
          />
          {abstractFile && (
            <span className="file-name">已選擇: {abstractFile.name}</span>
          )}
        </label>
      </div>

      <div className="upload-section">
        <label className="file-label">
          <span>PDF 投影片檔案（選填）</span>
          <input
            type="file"
            accept=".pdf"
            onChange={handlePdfFileChange}
            disabled={uploading || !!taskId}
          />
          {pdfFile && (
            <span className="file-name">已選擇: {pdfFile.name}</span>
          )}
        </label>
      </div>

      {error && <div className="error-message">{error}</div>}

      <button
        className="upload-button"
        onClick={handleUpload}
        disabled={!abstractFile || uploading || !!taskId}
      >
        {uploading ? '上傳中...' : taskId ? '已上傳' : '上傳檔案'}
      </button>

      {taskId && (
        <div className="success-message">
          ✓ 檔案上傳成功！任務 ID: {taskId.substring(0, 8)}...
        </div>
      )}
    </div>
  );
}

export default FileUpload;

