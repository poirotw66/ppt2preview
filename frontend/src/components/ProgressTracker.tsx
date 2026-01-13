import { useEffect, useState } from 'react';
import { useTaskStore } from '@/store/useTaskStore';
import { useSettingsStore } from '@/store/useSettingsStore';
import { apiClient } from '@/services/api';
import { WebSocketClient } from '@/services/websocket';
import { VideoParams } from '@/types';
import './ProgressTracker.css';

function ProgressTracker() {
  const { taskId, status, progress, currentStep, message, error, updateStatus } = useTaskStore();
  const { selectedVoice } = useSettingsStore();
  const [wsClient, setWsClient] = useState<WebSocketClient | null>(null);
  const [generating, setGenerating] = useState(false);
  
  // Update status when error occurs to prevent redirect
  useEffect(() => {
    if (status === 'failed' && error) {
      // Status is already updated, just ensure we stay on this page
      console.error('Video generation failed:', error);
    }
  }, [status, error]);
  const [videoParams, setVideoParams] = useState<VideoParams>({
    fps: 5,
    resolution_width: 1920,
    resolution_height: 1080,
    bitrate: '2000k',
    preset: 'ultrafast',
  });

  // Initialize WebSocket connection
  useEffect(() => {
    if (taskId && (status === 'script_ready' || status === 'generating_video' || status === 'failed')) {
      const client = new WebSocketClient(
        (update) => {
          updateStatus(update);
        },
        (err) => {
          console.error('WebSocket error:', err);
        },
        () => {
          console.log('WebSocket closed');
        }
      );

      // Small delay to ensure backend is ready
      const timeoutId = setTimeout(() => {
        client.connect(taskId);
        setWsClient(client);
      }, 100);

      return () => {
        clearTimeout(timeoutId);
        client.disconnect();
      };
    } else if (wsClient) {
      // Disconnect if status changed
      wsClient.disconnect();
      setWsClient(null);
    }
  }, [taskId, status]);

  const handleGenerateVideo = async () => {
    if (!taskId) return;

    setGenerating(true);

    try {
      await apiClient.generateVideo({
        task_id: taskId,
        video_params: videoParams,
        voice_name: selectedVoice,
      });
    } catch (err: any) {
      console.error('Failed to start video generation:', err);
      alert(err.response?.data?.detail || '啟動影片生成失敗');
      setGenerating(false);
    }
  };

  if (!taskId) {
    return <div>請先完成前面的步驟</div>;
  }

  // Define video generation steps
  const videoSteps = [
    { id: 'parsing', label: '解析對話內容', icon: '📝', keywords: ['解析', '對話'] },
    { id: 'converting', label: '轉換 PDF 為圖片', icon: '🖼️', keywords: ['轉換', 'PDF', '圖片', '投影片'] },
    { id: 'generating_audio', label: '產生音訊片段', icon: '🎙️', keywords: ['音訊', '產生', 'audio', 'mp3'] },
    { id: 'creating_clips', label: '創建影片片段', icon: '🎬', keywords: ['創建', '影片片段', 'video clip'] },
    { id: 'concatenating', label: '合併影片片段', icon: '🔗', keywords: ['合併', 'concatenate'] },
    { id: 'writing', label: '輸出影片檔案', icon: '💾', keywords: ['輸出', '寫入', 'write'] },
  ];

  const getCurrentStepIndex = () => {
    if (!currentStep) return -1;
    return videoSteps.findIndex(step => 
      step.keywords.some(keyword => currentStep.includes(keyword))
    );
  };

  const currentStepIndex = getCurrentStepIndex();

  if (status === 'generating_video') {
    return (
      <div className="progress-tracker">
        <div className="progress-section">
          <div className="progress-header">
            <h3>正在生成影片</h3>
            <span className="progress-percentage">{Math.round(progress)}%</span>
          </div>

          <div className="progress-bar-container">
            <div
              className="progress-bar"
              style={{ width: `${progress}%` }}
            />
          </div>

          {/* Step List */}
          <div className="steps-list">
            {videoSteps.map((step, index) => {
              const isCompleted = index < currentStepIndex;
              const isActive = index === currentStepIndex;
              const isPending = index > currentStepIndex;

              return (
                <div
                  key={step.id}
                  className={`step-item ${isCompleted ? 'completed' : ''} ${isActive ? 'active' : ''} ${isPending ? 'pending' : ''}`}
                >
                  <div className="step-icon-wrapper">
                    <div className="step-icon">{step.icon}</div>
                    {isActive && <div className="step-spinner">⏳</div>}
                  </div>
                  <div className="step-content">
                    <div className="step-label">{step.label}</div>
                    {isActive && message && (
                      <div className="step-message">{message}</div>
                    )}
                  </div>
                  {isCompleted && (
                    <div className="step-check">
                      <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                      </svg>
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {error && (
            <div className="error-message">
              <strong>錯誤：</strong> {error}
            </div>
          )}
        </div>
      </div>
    );
  }

  if (status === 'failed') {
    return (
      <div className="progress-tracker">
        <div className="error-section">
          <h3>影片生成失敗</h3>
          {error && (
            <div className="error-message">
              <strong>錯誤訊息：</strong>
              <pre style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                {error}
              </pre>
            </div>
          )}
          {message && (
            <div className="error-details">
              <strong>詳細資訊：</strong> {message}
            </div>
          )}
          <button
            className="retry-button"
            onClick={handleGenerateVideo}
            disabled={generating}
          >
            {generating ? '啟動中...' : '重新嘗試生成影片'}
          </button>
        </div>
      </div>
    );
  }

  if (status === 'script_ready') {
    return (
      <div className="progress-tracker">
        <div className="video-params-section">
          <h3>影片參數設定</h3>

          <div className="params-grid">
            <div className="param-group">
              <label>FPS（幀率）</label>
              <input
                type="number"
                min="1"
                max="30"
                value={videoParams.fps}
                onChange={(e) =>
                  setVideoParams({ ...videoParams, fps: parseInt(e.target.value) })
                }
              />
            </div>

            <div className="param-group">
              <label>寬度（像素）</label>
              <input
                type="number"
                min="640"
                max="3840"
                value={videoParams.resolution_width}
                onChange={(e) =>
                  setVideoParams({
                    ...videoParams,
                    resolution_width: parseInt(e.target.value),
                  })
                }
              />
            </div>

            <div className="param-group">
              <label>高度（像素）</label>
              <input
                type="number"
                min="360"
                max="2160"
                value={videoParams.resolution_height}
                onChange={(e) =>
                  setVideoParams({
                    ...videoParams,
                    resolution_height: parseInt(e.target.value),
                  })
                }
              />
            </div>

            <div className="param-group">
              <label>位元率</label>
              <select
                value={videoParams.bitrate}
                onChange={(e) =>
                  setVideoParams({ ...videoParams, bitrate: e.target.value })
                }
              >
                <option value="1000k">1000k</option>
                <option value="2000k">2000k</option>
                <option value="3000k">3000k</option>
                <option value="5000k">5000k</option>
              </select>
            </div>

            <div className="param-group">
              <label>編碼預設</label>
              <select
                value={videoParams.preset}
                onChange={(e) =>
                  setVideoParams({ ...videoParams, preset: e.target.value })
                }
              >
                <option value="ultrafast">ultrafast（最快）</option>
                <option value="veryfast">veryfast</option>
                <option value="fast">fast</option>
                <option value="medium">medium</option>
              </select>
            </div>
          </div>

          <button
            className="generate-video-button"
            onClick={handleGenerateVideo}
            disabled={generating}
          >
            {generating ? '啟動中...' : '開始生成影片'}
          </button>
        </div>
      </div>
    );
  }

  return null;
}

export default ProgressTracker;

