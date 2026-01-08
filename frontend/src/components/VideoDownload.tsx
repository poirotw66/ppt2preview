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
        <h3>
          <svg className="success-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          影片生成完成！
        </h3>
        <p>您的簡報影片已準備就緒，可以下載了。</p>

        <div className="download-actions">
          <button className="download-button" onClick={handleDownload}>
            <svg className="download-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
            下載影片
          </button>

          <a
            href={downloadUrl}
            download
            className="download-link"
          >
            <svg className="link-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
            </svg>
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

