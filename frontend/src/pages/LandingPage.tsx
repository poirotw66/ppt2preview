import { useNavigate } from 'react-router-dom';
import { useState } from 'react';
import './LandingPage.css';

function LandingPage() {
  const navigate = useNavigate();
  const [isPlaying, setIsPlaying] = useState(false);

  const handleWatchDemo = () => {
    setIsPlaying(true);
  };

  const features = [
    {
      title: '快速上傳',
      description: '支援 Markdown 大綱和 PDF 投影片，一鍵上傳即可開始',
      icon: (
        <svg className="feature-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
        </svg>
      ),
    },
    {
      title: 'AI 腳本生成',
      description: '智能分析投影片內容，自動生成專業解說腳本',
      icon: (
        <svg className="feature-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
        </svg>
      ),
    },
    {
      title: '靈活編輯',
      description: '可自由調整腳本內容，完全掌控解說細節',
      icon: (
        <svg className="feature-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
        </svg>
      ),
    },
    {
      title: '自動生成影片',
      description: '一鍵將投影片與腳本合成為高品質解說影片',
      icon: (
        <svg className="feature-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
        </svg>
      ),
    },
    {
      title: '即時下載',
      description: '影片生成完成後立即下載，支援多種格式',
      icon: (
        <svg className="feature-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
        </svg>
      ),
    },
    {
      title: '雲端處理',
      description: '強大的雲端運算能力，快速完成影片生成任務',
      icon: (
        <svg className="feature-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 10-9.78 2.096A4.001 4.001 0 003 15z" />
        </svg>
      ),
    },
  ];

  const steps = [
    { number: 1, title: '上傳檔案', description: '上傳 Markdown 大綱和 PDF 投影片' },
    { number: 2, title: '生成腳本', description: 'AI 自動生成解說腳本' },
    { number: 3, title: '優化編輯', description: '根據需求調整腳本內容' },
    { number: 4, title: '生成影片', description: '一鍵合成專業解說影片' },
  ];

  return (
    <div className="landing-page">
      {/* Hero Section */}
      <section className="hero-section">
        <div className="hero-content">
          <div className="hero-badge">
            <svg className="badge-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            <span>簡報轉影片 SaaS 平台</span>
          </div>
          
          <h1 className="hero-title">
            將簡報快速轉換為<br />
            <span className="gradient-text">專業解說影片</span>
          </h1>
          
          <p className="hero-description">
            上傳您的簡報大綱和投影片，讓 AI 自動生成解說腳本並合成影片。
            <br />
            節省時間，提升效率，讓內容傳播更簡單。
          </p>
          
          <div className="hero-actions">
            <button 
              className="cta-button primary"
              onClick={() => navigate('/upload')}
            >
              <span>立即開始</span>
              <svg className="button-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
              </svg>
            </button>
            
            <button className="cta-button secondary" onClick={handleWatchDemo}>
              <svg className="button-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span>觀看示範</span>
            </button>
          </div>
          
          <div className="hero-stats">
            <div className="stat-item">
              <div className="stat-value">5 分鐘</div>
              <div className="stat-label">平均生成時間</div>
            </div>
            <div className="stat-divider"></div>
            <div className="stat-item">
              <div className="stat-value">100%</div>
              <div className="stat-label">雲端處理</div>
            </div>
            <div className="stat-divider"></div>
            <div className="stat-item">
              <div className="stat-value">AI 驅動</div>
              <div className="stat-label">智能腳本生成</div>
            </div>
          </div>
        </div>
        
        <div className="hero-visual">
          <div className="visual-card glass">
            <div className="card-header">
              <div className="header-dots">
                <span className="dot red"></span>
                <span className="dot yellow"></span>
                <span className="dot green"></span>
              </div>
              <div className="header-title">ppt2preview.mp4</div>
            </div>
            <div className="card-content">
              {!isPlaying ? (
                <div className="video-placeholder" onClick={handleWatchDemo}>
                  <svg className="video-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
              ) : (
                <video 
                  controls 
                  autoPlay 
                  src="/example/presentation.mp4"
                  className="demo-video-inline"
                >
                  您的瀏覽器不支援影片播放。
                </video>
              )}
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="features-section">
        <div className="section-header">
          <h2 className="section-title">強大功能，一應俱全</h2>
          <p className="section-description">
            從上傳到下載，完整的影片生成流程，讓您專注於內容本身
          </p>
        </div>
        
        <div className="features-grid">
          {features.map((feature, index) => (
            <div key={index} className="feature-card glass">
              <div className="feature-icon-wrapper">
                {feature.icon}
              </div>
              <h3 className="feature-title">{feature.title}</h3>
              <p className="feature-description">{feature.description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* How It Works Section */}
      <section className="steps-section">
        <div className="section-header">
          <h2 className="section-title">簡單四步驟</h2>
          <p className="section-description">
            直觀的操作流程，讓您輕鬆完成影片製作
          </p>
        </div>
        
        <div className="steps-container">
          {steps.map((step, index) => (
            <div key={step.number} className="step-item">
              <div className="step-number-wrapper glass">
                <span className="step-number">{step.number}</span>
              </div>
              <div className="step-content">
                <h3 className="step-title">{step.title}</h3>
                <p className="step-description">{step.description}</p>
              </div>
              {index < steps.length - 1 && (
                <div className="step-connector">
                  <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                  </svg>
                </div>
              )}
            </div>
          ))}
        </div>
      </section>

      {/* CTA Section */}
      <section className="cta-section">
        <div className="cta-content glass">
          <h2 className="cta-title">準備好開始了嗎？</h2>
          <p className="cta-description">
            立即體驗 PPT2Preview，將您的簡報轉換為專業影片
          </p>
          <button 
            className="cta-button primary large"
            onClick={() => navigate('/upload')}
          >
            <span>免費開始使用</span>
            <svg className="button-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
            </svg>
          </button>
        </div>
      </section>

      {/* Footer */}
      <footer className="landing-footer">
        <p>&copy; 2026 PPT2Preview. All rights reserved.</p>
      </footer>
    </div>
  );
}

export default LandingPage;
