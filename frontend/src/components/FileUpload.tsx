import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiClient } from '@/services/api';
import { useTaskStore } from '@/store/useTaskStore';
import { LengthMode } from '@/types';
import { useToastStore } from '@/store/useToastStore';
import './FileUpload.css';

function FileUpload() {
  const navigate = useNavigate();
  const { taskId, setTaskId, updateStatus } = useTaskStore();
  const { showToast, success, error: showError } = useToastStore();
  const [abstractFile, setAbstractFile] = useState<File | null>(null);
  const [pdfFile, setPdfFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isDraggingAbstract, setIsDraggingAbstract] = useState(false);
  const [isDraggingPdf, setIsDraggingPdf] = useState(false);
  const [validationErrors, setValidationErrors] = useState<{
    abstract?: string;
    pdf?: string;
  }>({});

  const validateFile = (file: File, type: 'abstract' | 'pdf'): boolean => {
    const errors = { ...validationErrors };
    
    if (type === 'abstract') {
      if (!file.name.endsWith('.md') && !file.name.endsWith('.markdown')) {
        errors.abstract = '請上傳 Markdown 檔案 (.md 或 .markdown)';
        setValidationErrors(errors);
        return false;
      } else if (file.size > 10 * 1024 * 1024) {
        errors.abstract = '檔案大小不能超過 10MB';
        setValidationErrors(errors);
        return false;
      } else {
        delete errors.abstract;
        setValidationErrors(errors);
        return true;
      }
    } else {
      if (!file.name.endsWith('.pdf')) {
        errors.pdf = '請上傳 PDF 檔案';
        setValidationErrors(errors);
        return false;
      } else if (file.size > 50 * 1024 * 1024) {
        errors.pdf = '檔案大小不能超過 50MB';
        setValidationErrors(errors);
        return false;
      } else {
        delete errors.pdf;
        setValidationErrors(errors);
        return true;
      }
    }
  };

  const handleAbstractFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      if (validateFile(file, 'abstract')) {
        setAbstractFile(file);
        setError(null);
        success(`已選擇檔案: ${file.name}`);
      } else {
        showError(validationErrors.abstract || '檔案格式不正確');
      }
    }
  };

  const handlePdfFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      if (validateFile(file, 'pdf')) {
        setPdfFile(file);
        setError(null);
        success(`已選擇 PDF: ${file.name}`);
      } else {
        showError(validationErrors.pdf || 'PDF 檔案格式不正確');
      }
    }
  };

  const handleDragEnter = (e: React.DragEvent, type: 'abstract' | 'pdf') => {
    e.preventDefault();
    e.stopPropagation();
    if (type === 'abstract') {
      setIsDraggingAbstract(true);
    } else {
      setIsDraggingPdf(true);
    }
  };

  const handleDragLeave = (e: React.DragEvent, type: 'abstract' | 'pdf') => {
    e.preventDefault();
    e.stopPropagation();
    if (type === 'abstract') {
      setIsDraggingAbstract(false);
    } else {
      setIsDraggingPdf(false);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e: React.DragEvent, type: 'abstract' | 'pdf') => {
    e.preventDefault();
    e.stopPropagation();
    
    if (type === 'abstract') {
      setIsDraggingAbstract(false);
    } else {
      setIsDraggingPdf(false);
    }

    const files = Array.from(e.dataTransfer.files);
    const file = files[0];
    
    if (file) {
      if (type === 'abstract') {
        if (validateFile(file, 'abstract')) {
          setAbstractFile(file);
          setError(null);
          success(`已拖放檔案: ${file.name}`);
        } else {
          showError(validationErrors.abstract || '檔案格式不正確');
        }
      } else {
        if (validateFile(file, 'pdf')) {
          setPdfFile(file);
          setError(null);
          success(`已拖放 PDF: ${file.name}`);
        } else {
          showError(validationErrors.pdf || 'PDF 檔案格式不正確');
        }
      }
    }
  };

  const handleUpload = async () => {
    if (!abstractFile) {
      const errorMsg = '請選擇簡報大綱檔案（Markdown）';
      setError(errorMsg);
      showError(errorMsg);
      return;
    }

    setUploading(true);
    setError(null);
    showToast('開始上傳檔案...', 'info');

    try {
      const response = await apiClient.uploadFiles(abstractFile, pdfFile || undefined);
      setTaskId(response.task_id);
      
      // Fetch complete task status including project_name
      try {
        const statusResponse = await apiClient.getTaskStatus(response.task_id);
        updateStatus(statusResponse);
      } catch (statusErr) {
        // Fallback to basic status if fetch fails
        updateStatus({
          task_id: response.task_id,
          status: 'uploading' as any,
          progress: 10,
          message: response.message,
        });
      }
      
      success('檔案上傳成功！');
      // Navigate to script page with task ID
      setTimeout(() => {
        navigate(`/task/${response.task_id}/script`);
      }, 500);
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || '上傳失敗，請重試';
      setError(errorMsg);
      showError(errorMsg);
      console.error('Upload error:', err);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="file-upload">
      <div className="upload-section">
        <label 
          className={`file-label ${isDraggingAbstract ? 'dragging' : ''} ${validationErrors.abstract ? 'error' : ''}`}
          onDragEnter={(e) => handleDragEnter(e, 'abstract')}
          onDragLeave={(e) => handleDragLeave(e, 'abstract')}
          onDragOver={handleDragOver}
          onDrop={(e) => handleDrop(e, 'abstract')}
        >
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
              {isDraggingAbstract ? '放開以上傳' : '點擊或拖曳檔案至此處上傳'}
            </span>
          </div>
          {abstractFile && (
            <span className="file-name">
              <svg className="file-name-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              {abstractFile.name}
              <span className="file-size">({(abstractFile.size / 1024).toFixed(1)} KB)</span>
            </span>
          )}
          {validationErrors.abstract && (
            <span className="file-error">{validationErrors.abstract}</span>
          )}
        </label>
      </div>

      <div className="upload-section">
        <label 
          className={`file-label ${isDraggingPdf ? 'dragging' : ''} ${validationErrors.pdf ? 'error' : ''}`}
          onDragEnter={(e) => handleDragEnter(e, 'pdf')}
          onDragLeave={(e) => handleDragLeave(e, 'pdf')}
          onDragOver={handleDragOver}
          onDrop={(e) => handleDrop(e, 'pdf')}
        >
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
              {isDraggingPdf ? '放開以上傳' : '點擊或拖曳檔案至此處上傳'}
            </span>
          </div>
          {pdfFile && (
            <span className="file-name">
              <svg className="file-name-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              {pdfFile.name}
              <span className="file-size">({(pdfFile.size / 1024 / 1024).toFixed(2)} MB)</span>
            </span>
          )}
          {validationErrors.pdf && (
            <span className="file-error">{validationErrors.pdf}</span>
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

