import { useState, useEffect } from 'react';
import { apiClient } from '@/services/api';
import { useTaskStore } from '@/store/useTaskStore';
import { LengthMode } from '@/types';
import './ScriptEditor.css';

interface ScriptEditorProps {
  showOptimizeButton?: boolean;
}

function ScriptEditor({ showOptimizeButton = false }: ScriptEditorProps) {
  const { taskId, scriptContent, setScript, updateScriptContent, status, updateStatus } = useTaskStore();
  const [lengthMode, setLengthMode] = useState<LengthMode>(LengthMode.MEDIUM);
  const [generating, setGenerating] = useState(false);
  const [optimizing, setOptimizing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [localScript, setLocalScript] = useState(scriptContent || '');

  // Load script when it becomes available
  useEffect(() => {
    if (taskId && status === 'script_ready' && !scriptContent) {
      loadScript();
    }
  }, [taskId, status]);

  // Sync local script with store
  useEffect(() => {
    if (scriptContent) {
      setLocalScript(scriptContent);
    }
  }, [scriptContent]);

  const loadScript = async () => {
    if (!taskId) return;

    try {
      const response = await apiClient.getScript(taskId);
      setScript(response);
      setLocalScript(response.script_content);
    } catch (err: any) {
      setError(err.response?.data?.detail || '載入腳本失敗');
    }
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
          // Update store status
          updateStatus(statusResponse);
          
          if (statusResponse.status === 'script_ready') {
            clearInterval(pollInterval);
            await loadScript();
            setGenerating(false);
          } else if (statusResponse.status === 'failed') {
            clearInterval(pollInterval);
            setError(statusResponse.error || '腳本生成失敗');
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
      const response = await apiClient.updateScript(taskId, {
        script_content: localScript,
      });
      updateScriptContent(response.script_content);
    } catch (err: any) {
      setError(err.response?.data?.detail || '儲存腳本失敗');
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
    return <div>請先上傳檔案</div>;
  }

  return (
    <div className="script-editor">
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

      {scriptContent && (
        <div className="editor-section">
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
                disabled={saving || localScript === scriptContent}
              >
                {saving ? '儲存中...' : '儲存變更'}
              </button>
            </div>
          </div>

          <textarea
            className="script-textarea"
            value={localScript}
            onChange={(e) => setLocalScript(e.target.value)}
            placeholder="腳本內容..."
            rows={20}
          />
        </div>
      )}

      {error && <div className="error-message">{error}</div>}
    </div>
  );
}

export default ScriptEditor;

