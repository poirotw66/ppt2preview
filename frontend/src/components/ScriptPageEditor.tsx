import { useState, useEffect } from 'react';
import { apiClient } from '@/services/api';
import { useTaskStore } from '@/store/useTaskStore';
import { LengthMode } from '@/types';
import { useToastStore } from '@/store/useToastStore';
import './ScriptPageEditor.css';

interface ScriptPageEditorProps {
  showOptimizeButton?: boolean;
}

interface ScriptPage {
  pageNum: number;
  content: string;
}

interface SlideImage {
  page: number;
  filename: string;
  url: string;
}

function ScriptPageEditor({ showOptimizeButton = false }: ScriptPageEditorProps) {
  const { taskId, scriptContent, setScript, updateScriptContent, status, updateStatus } = useTaskStore();
  const { success, error: showError } = useToastStore();
  const [lengthMode, setLengthMode] = useState<LengthMode>(LengthMode.MEDIUM);
  const [generating, setGenerating] = useState(false);
  const [optimizing, setOptimizing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Script pages state
  const [scriptPages, setScriptPages] = useState<ScriptPage[]>([]);
  const [currentPage, setCurrentPage] = useState(0);
  
  // Slide images state
  const [slides, setSlides] = useState<SlideImage[]>([]);
  const [loadingSlides, setLoadingSlides] = useState(false);

  // Load script when it becomes available
  useEffect(() => {
    if (taskId && status === 'script_ready' && !scriptContent) {
      loadScript();
    }
  }, [taskId, status]);

  // Parse script into pages when scriptContent changes
  useEffect(() => {
    if (scriptContent) {
      parseScriptIntoPages(scriptContent);
    }
  }, [scriptContent]);

  // Load slides when taskId is available
  useEffect(() => {
    if (taskId) {
      loadSlides();
    }
  }, [taskId]);

  const loadScript = async () => {
    if (!taskId) return;

    try {
      const response = await apiClient.getScript(taskId);
      setScript(response);
    } catch (err: any) {
      setError(err.response?.data?.detail || '載入腳本失敗');
    }
  };

  const loadSlides = async () => {
    if (!taskId) return;

    setLoadingSlides(true);
    try {
      const response = await apiClient.getSlides(taskId);
      setSlides(response.slides);
    } catch (err: any) {
      console.error('載入投影片圖片失敗:', err);
      // Don't show error for slides as PDF might not be uploaded
    } finally {
      setLoadingSlides(false);
    }
  };

  const parseScriptIntoPages = (script: string) => {
    const pagesMap = new Map<number, string[]>();
    const lines = script.split('\n');
    let currentPageNum = 0;
    let currentContent: string[] = [];

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      // Check for page marker: ### [PAGE X]
      const pageMatch = line.match(/^###\s+\[PAGE\s+(\d+)\]/);
      
      if (pageMatch) {
        // Save previous page content if exists
        if (currentPageNum > 0 && currentContent.length > 0) {
          const trimmedContent = currentContent.join('\n').trim();
          if (trimmedContent) {
            if (!pagesMap.has(currentPageNum)) {
              pagesMap.set(currentPageNum, []);
            }
            pagesMap.get(currentPageNum)!.push(trimmedContent);
          }
        }
        
        // Start new page
        currentPageNum = parseInt(pageMatch[1]);
        currentContent = [];
      } else if (currentPageNum > 0) {
        // Add content to current page (skip empty lines at the beginning)
        if (currentContent.length > 0 || line.trim() !== '') {
          currentContent.push(line);
        }
      }
    }

    // Save last page
    if (currentPageNum > 0 && currentContent.length > 0) {
      const trimmedContent = currentContent.join('\n').trim();
      if (trimmedContent) {
        if (!pagesMap.has(currentPageNum)) {
          pagesMap.set(currentPageNum, []);
        }
        pagesMap.get(currentPageNum)!.push(trimmedContent);
      }
    }

    // Convert map to array, merging duplicate pages with separator
    const pages: ScriptPage[] = [];
    const sortedPageNums = Array.from(pagesMap.keys()).sort((a, b) => a - b);
    
    for (const pageNum of sortedPageNums) {
      const contents = pagesMap.get(pageNum)!;
      // Join multiple sections of the same page with a separator
      const mergedContent = contents.join('\n\n---\n\n');
      pages.push({
        pageNum,
        content: mergedContent
      });
    }

    setScriptPages(pages);
    if (pages.length > 0 && currentPage === 0) {
      setCurrentPage(0);
    }
  };

  const reconstructScript = (pages: ScriptPage[]): string => {
    return pages
      .map(page => {
        // Split merged content back into separate sections if it has separators
        const sections = page.content.split('\n\n---\n\n');
        return sections
          .map(section => `### [PAGE ${page.pageNum}]\n\n${section.trim()}`)
          .join('\n\n');
      })
      .join('\n\n');
  };

  const handlePageContentChange = (pageIndex: number, newContent: string) => {
    const updatedPages = [...scriptPages];
    updatedPages[pageIndex] = {
      ...updatedPages[pageIndex],
      content: newContent
    };
    setScriptPages(updatedPages);
  };

  const handleGenerateScript = async () => {
    if (!taskId) return;

    setGenerating(true);
    setError(null);

    try {
      await apiClient.generateScript({
        task_id: taskId,
        length_mode: lengthMode,
      });

      // Poll for script completion
      const pollInterval = setInterval(async () => {
        try {
          const statusResponse = await apiClient.getTaskStatus(taskId!);
          updateStatus(statusResponse);
          
          if (statusResponse.status === 'script_ready') {
            clearInterval(pollInterval);
            await loadScript();
            await loadSlides(); // Reload slides after script generation
            setGenerating(false);
            success('腳本生成完成！');
          } else if (statusResponse.status === 'failed') {
            clearInterval(pollInterval);
            const errorMsg = statusResponse.error || '腳本生成失敗';
            setError(errorMsg);
            showError(errorMsg);
            setGenerating(false);
          }
        } catch (err) {
          console.error('Polling error:', err);
        }
      }, 2000);

      // Timeout after 5 minutes
      setTimeout(() => {
        clearInterval(pollInterval);
        if (generating) {
          setError('腳本生成超時，請重試');
          setGenerating(false);
        }
      }, 300000);
    } catch (err: any) {
      setError(err.response?.data?.detail || '生成腳本失敗');
      setGenerating(false);
    }
  };

  const handleSaveScript = async () => {
    if (!taskId) return;

    setSaving(true);
    setError(null);

    try {
      const newScriptContent = reconstructScript(scriptPages);
      const response = await apiClient.updateScript(taskId, {
        script_content: newScriptContent,
      });
      updateScriptContent(response.script_content);
      success('腳本已儲存');
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || '儲存腳本失敗';
      setError(errorMsg);
      showError(errorMsg);
    } finally {
      setSaving(false);
    }
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
            await loadScript();
            setOptimizing(false);
            success('腳本優化完成！');
          } else if (statusResponse.status === 'failed') {
            clearInterval(pollInterval);
            const errorMsg = statusResponse.error || '腳本優化失敗';
            setError(errorMsg);
            showError(errorMsg);
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
    return <div>請先上傳檔案</div>;
  }

  return (
    <div className="script-page-editor">
      {!scriptContent && status !== 'generating_script' && (
        <div className="generate-section">
          <div className="length-mode-selector">
            <label>腳本長度：</label>
            <select
              value={lengthMode}
              onChange={(e) => setLengthMode(e.target.value as LengthMode)}
              disabled={generating}
            >
              <option value={LengthMode.SHORT}>簡短（約 7 分鐘）</option>
              <option value={LengthMode.MEDIUM}>中等（約 15 分鐘）</option>
              <option value={LengthMode.LONG}>完整（約 30 分鐘）</option>
            </select>
          </div>

          <button
            className="generate-button"
            onClick={handleGenerateScript}
            disabled={generating}
          >
            {generating ? '生成中...' : '生成腳本'}
          </button>
        </div>
      )}

      {(status === 'generating_script' || optimizing) && (
        <div className="generating-message">
          <div className="spinner"></div>
          <span>{optimizing ? '正在優化腳本，請稍候...' : '正在生成腳本，請稍候...'}</span>
        </div>
      )}

      {scriptContent && scriptPages.length > 0 && (
        <div className="split-editor-container">
          {/* Left side: Slide preview */}
          <div className="slide-section">
            <div className="slide-header">
              <h3>投影片預覽</h3>
              {slides.length > 0 && (
                <span className="slide-count">共 {slides.length} 頁</span>
              )}
            </div>

            <div className="slide-preview">
              {loadingSlides && (
                <div className="slide-loading">
                  <div className="spinner"></div>
                  <p>載入投影片中...</p>
                </div>
              )}

              {!loadingSlides && slides.length === 0 && (
                <div className="no-slides">
                  <svg className="no-slides-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  <p>尚未上傳 PDF 投影片</p>
                </div>
              )}

              {!loadingSlides && slides.length > 0 && scriptPages[currentPage] && (
                <div className="slide-image-container">
                  {/* Find corresponding slide */}
                  {(() => {
                    const pageNum = scriptPages[currentPage].pageNum;
                    const slide = slides.find(s => s.page === pageNum);
                    
                    if (slide) {
                      return (
                        <img
                          src={apiClient.getSlideUrl(taskId, slide.filename)}
                          alt={`第 ${pageNum} 頁`}
                          className="slide-image"
                        />
                      );
                    } else {
                      return (
                        <div className="slide-not-found">
                          <p>找不到第 {pageNum} 頁的投影片</p>
                        </div>
                      );
                    }
                  })()}
                </div>
              )}
            </div>
          </div>

          {/* Right side: Script editor */}
          <div className="script-section">
            <div className="editor-header">
              <h3>編輯腳本</h3>
              <div className="editor-actions">
                {showOptimizeButton && (
                  <button
                    className="optimize-button"
                    onClick={handleOptimizeScript}
                    disabled={optimizing || status === 'generating_script'}
                  >
                    {optimizing ? '優化中...' : '✨ AI 優化腳本'}
                  </button>
                )}
                <button
                  className="save-button"
                  onClick={handleSaveScript}
                  disabled={saving}
                >
                  {saving ? '儲存中...' : '儲存變更'}
                </button>
              </div>
            </div>

            {/* Page selector */}
            <div className="page-selector">
              {scriptPages.map((page, index) => (
                <button
                  key={page.pageNum}
                  className={`page-tab ${currentPage === index ? 'active' : ''}`}
                  onClick={() => setCurrentPage(index)}
                >
                  第 {page.pageNum} 頁
                </button>
              ))}
            </div>

            {/* Current page editor */}
            <div className="page-editor">
              <textarea
                className="script-textarea"
                value={scriptPages[currentPage]?.content || ''}
                onChange={(e) => handlePageContentChange(currentPage, e.target.value)}
                placeholder="腳本內容..."
                rows={20}
              />
            </div>
          </div>
        </div>
      )}

      {error && <div className="error-message">{error}</div>}
    </div>
  );
}

export default ScriptPageEditor;
