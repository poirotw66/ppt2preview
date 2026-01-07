import { useTaskStore } from '@/store/useTaskStore';
import { apiClient } from '@/services/api';
import './VideoDownload.css';

function VideoDownload() {
  const { taskId } = useTaskStore();

  if (!taskId) {
    return <div>請先完成前面的步驟</div>;
  }

  const downloadUrl = apiClient.getDownloadUrl(taskId);

  const handleDownload = () => {
    window.open(downloadUrl, '_blank');
  };

  return (
    <div className="video-download">
      <div className="download-section">
        <h3>影片生成完成！</h3>
        <p>您的簡報影片已準備就緒，可以下載了。</p>

        <div className="download-actions">
          <button className="download-button" onClick={handleDownload}>
            下載影片
          </button>

          <a
            href={downloadUrl}
            download
            className="download-link"
          >
            或直接點擊此連結下載
          </a>
        </div>

        <div className="video-preview">
          <video controls src={downloadUrl} style={{ maxWidth: '100%' }}>
            您的瀏覽器不支援影片播放。
          </video>
        </div>
      </div>
    </div>
  );
}

export default VideoDownload;

